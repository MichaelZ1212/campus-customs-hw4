"""Small read-only API for the Campus Customs storefront."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import logging
import base64
import os
import time
from contextlib import closing
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from pydantic_ai.exceptions import UsageLimitExceeded
from dotenv import load_dotenv


_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

try:
    from .agent import AgentDependencies, chat as run_agent_chat
    from .models import ChatApiResponse, ChatMessage, ChatRequest, ChatResponse, StoredChatMessage
    from .tools import get_product_cards_by_ids
except ImportError:  # Supports `uvicorn main:app` from inside backend/.
    from agent import AgentDependencies, chat as run_agent_chat
    from models import ChatApiResponse, ChatMessage, ChatRequest, ChatResponse, StoredChatMessage
    from tools import get_product_cards_by_ids


logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "campus_customs.db"
PRODUCT_IMAGE_DIR = DATA_DIR / "products"
LEGACY_PBKDF2_ITERATIONS = 120_000
PBKDF2_ITERATIONS = 600_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SESSION_LIFETIME_SECONDS = 60 * 60 * 24 * 7
SESSION_SECRET = os.getenv("CAMPUS_CUSTOMS_SESSION_SECRET", secrets.token_urlsafe(32)).encode("utf-8")

if not DATABASE_PATH.is_file():
    raise RuntimeError(f"Database not found: {DATABASE_PATH}")
if not PRODUCT_IMAGE_DIR.is_dir():
    raise RuntimeError(f"Product image directory not found: {PRODUCT_IMAGE_DIR}")

app = FastAPI(title="Campus Customs API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/product-images", StaticFiles(directory=PRODUCT_IMAGE_DIR), name="product-images")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return [value] if value else []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def image_url(path: str) -> str:
    normalized = path.replace("\\", "/").removeprefix("products/")
    return f"/product-images/{quote(normalized, safe='/')}"


class RegistrationRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    password_confirmation: str = Field(min_length=8, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be blank")
        return cleaned

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(cleaned):
            raise ValueError("Enter a valid email address")
        return cleaned


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    parts = stored_hash.split("$")
    try:
        if len(parts) == 3 and parts[0] == "pbkdf2_sha256":
            _, salt, expected = parts
            iterations = LEGACY_PBKDF2_ITERATIONS
        elif len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            _, iteration_text, salt, expected = parts
            iterations = int(iteration_text)
            if not 100_000 <= iterations <= 2_000_000:
                return False
        else:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def public_user(row: sqlite3.Row) -> UserResponse:
    first_name = row["first_name"] or row["name"].split(" ", 1)[0]
    last_name = row["last_name"] or (row["name"].split(" ", 1)[1] if " " in row["name"] else "")
    return UserResponse(id=row["id"], first_name=first_name, last_name=last_name, email=row["email"])


def create_access_token(user_id: int) -> str:
    expires = int(time.time()) + SESSION_LIFETIME_SECONDS
    payload = f"{user_id}:{expires}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(SESSION_SECRET, encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def authenticated_user(authorization: str | None) -> UserResponse | None:
    if authorization is None:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(SESSION_SECRET, encoded.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        padded = encoded + "=" * (-len(encoded) % 4)
        user_id_text, expires_text = base64.urlsafe_b64decode(padded).decode("utf-8").split(":", 1)
        if int(expires_text) < int(time.time()):
            raise ValueError
        user_id = int(user_id_text)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token") from None
    with closing(connect()) as connection:
        row = connection.execute(
            "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return public_user(row)


def serialize_product(row: sqlite3.Row, include_details: bool = False) -> dict[str, Any]:
    product = {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": parse_json_list(row["colors"]),
        "search_tags": parse_json_list(row["search_tags"]),
        "image_url": image_url(row["image_file_path"]),
        "price": row["price"],
    }
    if include_details:
        product["inventory"] = [
            {"size": item["size"], "quantity": item["quantity"]}
            for item in row["inventory"]
        ]
    return product


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(payload: RegistrationRequest) -> UserResponse:
    if payload.password != payload.password_confirmation:
        raise HTTPException(status_code=422, detail="Passwords do not match")

    full_name = f"{payload.first_name} {payload.last_name}"
    try:
        with closing(connect()) as connection:
            connection.execute("PRAGMA query_only = OFF")
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, payload.email, hash_password(payload.password), payload.first_name, payload.last_name),
            )
            connection.commit()
            row = connection.execute(
                "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    if row is None:
        raise HTTPException(status_code=500, detail="Account could not be created")
    return public_user(row)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    email = payload.email.strip().lower()
    with closing(connect()) as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash, first_name, last_name
            FROM users WHERE lower(email) = ?
            """,
            (email,),
        ).fetchone()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    user = public_user(row)
    return AuthResponse(user=user, access_token=create_access_token(user.id))


@app.post("/api/chat", response_model=ChatApiResponse)
async def chat_endpoint(payload: ChatRequest, authorization: str | None = Header(default=None)) -> ChatApiResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be blank")
    try:
        user = authenticated_user(authorization)
        history = payload.history
        if user:
            history = load_user_history(user.id, limit=20)
        deps = AgentDependencies(
            user_id=user.id if user else None,
            customer_name=f"{user.first_name} {user.last_name}".strip() if user else None,
            customer_email=user.email if user else None,
            page_path=payload.page.path,
            product_id=payload.page.product_id,
        )
        response = await run_agent_chat(payload.message.strip(), history, deps)
        if user:
            save_chat_exchange(user.id, payload.message.strip(), response)
        return response
    except HTTPException:
        raise  # e.g. an expired login token must reach the browser as 401, not a generic failure.
    except UsageLimitExceeded:
        logger.warning("The shopping assistant reached its agent/tool loop limit")
        return ChatApiResponse(
            message="That request needs more lookups than I can do at once. Could you narrow it down, for example to one product, size, or category?",
        )
    except sqlite3.Error:
        logger.exception("The shopping assistant database request failed")
        raise HTTPException(
            status_code=503,
            detail="I can’t check the catalogue right now. Please try again in a moment.",
        ) from None
    except Exception:
        logger.exception("The shopping assistant request failed")
        raise HTTPException(
            status_code=502,
            detail="I’m having trouble answering right now. Please try again in a moment.",
        ) from None


def load_user_history(user_id: int, limit: int = 50) -> list[ChatMessage]:
    with closing(connect()) as connection:
        rows = connection.execute(
            """SELECT role, content FROM (
                   SELECT id, role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?
               ) ORDER BY id""",
            (user_id, limit),
        ).fetchall()
    return [ChatMessage(role=row["role"], content=row["content"]) for row in rows if row["role"] in {"user", "assistant"}]


def save_chat_exchange(user_id: int, user_message: str, response: ChatResponse) -> None:
    products_json = json.dumps([product.model_dump() for product in response.products]) if response.products else None
    with closing(connect()) as connection:
        connection.execute("PRAGMA query_only = OFF")
        connection.executemany(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            [(user_id, "user", user_message, None), (user_id, "assistant", response.message, products_json)],
        )
        connection.commit()


@app.get("/api/chat/history", response_model=list[StoredChatMessage])
def chat_history(authorization: str | None = Header(default=None)) -> list[StoredChatMessage]:
    user = authenticated_user(authorization)
    if user is None:
        return []
    with closing(connect()) as connection:
        rows = connection.execute(
            """SELECT id, role, content, products_json, created_at FROM (
                   SELECT id, role, content, products_json, created_at FROM chat_messages
                   WHERE user_id = ? ORDER BY id DESC LIMIT 50
               ) ORDER BY id""",
            (user.id,),
        ).fetchall()
    messages = []
    for row in rows:
        product_ids: list[str] = []
        if row["products_json"]:
            try:
                saved_products = json.loads(row["products_json"])
                product_ids = [item["product_id"] for item in saved_products if isinstance(item, dict) and "product_id" in item]
            except (json.JSONDecodeError, TypeError):
                pass
        messages.append(StoredChatMessage(
            id=row["id"], role=row["role"], content=row["content"],
            products=get_product_cards_by_ids(product_ids), created_at=row["created_at"],
        ))
    return messages


@app.get("/api/products")
def list_products() -> list[dict[str, Any]]:
    with closing(connect()) as connection:
        rows = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors,
                   search_tags, image_file_path, price
            FROM catalogue
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()
    return [serialize_product(row) for row in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    with closing(connect()) as connection:
        product = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors,
                   search_tags, image_file_path, price
            FROM catalogue
            WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        inventory = connection.execute(
            """
            SELECT size, quantity
            FROM inventory
            WHERE product_id = ?
            ORDER BY id
            """,
            (product_id,),
        ).fetchall()

    enriched = dict(product)
    enriched["inventory"] = inventory
    return serialize_product(enriched, include_details=True)
