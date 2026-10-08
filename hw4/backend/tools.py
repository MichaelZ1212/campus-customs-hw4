"""Database-backed tools available to the Campus Customs agent."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

try:
    from .models import InventoryItem, ProductCard, ProductLookupResult, ProductSearchResult, StockLookupResult
except ImportError:  # Supports `uvicorn main:app` from inside backend/.
    from models import InventoryItem, ProductCard, ProductLookupResult, ProductSearchResult, StockLookupResult


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "campus_customs.db"
SEARCH_STOP_WORDS = {
    "a", "an", "and", "apparel", "are", "do", "for", "have", "i", "looking", "me",
    "merch", "merchandise", "of", "please", "product", "products", "show", "some", "the",
    "want", "what", "with", "you",
}


def _image_url(path: str) -> str:
    normalized = path.replace("\\", "/").removeprefix("products/")
    return f"/product-images/{quote(normalized, safe='/')}"


def search_products(query: str, limit: int = 5) -> ProductSearchResult:
    """Search the local catalogue by name, type, description, colors, or tags.

    Use this tool whenever a shopper asks for products or recommendations. Results
    are factual catalogue records. Do not invent products that are not returned.
    Only the products matching the most search words are returned, so `total_matches`
    counts those best matches and may exceed the number of returned products (at most 8).
    """
    raw_terms = [term.strip(".,!?;:'\"").lower() for term in query.split()]
    # One variant group per shopper word, so "hoodies"/"hoodie" count as a single matched word.
    word_variants: list[list[str]] = []
    for term in dict.fromkeys(raw_terms):
        if len(term) <= 1 or term in SEARCH_STOP_WORDS:
            continue
        variants = [term]
        if term.endswith("ies") and len(term) > 3:
            variants += [f"{term[:-3]}y", term[:-1]]
        elif term.endswith("s") and len(term) > 3:
            variants.append(term[:-1])
        word_variants.append(variants)
    word_variants = word_variants[:6]
    if not word_variants:
        return ProductSearchResult(total_matches=0, products=[])
    # Match at word starts so "red" does not match "embroidered", while "hoodie" still matches "hoodies".
    patterns = [re.compile("|".join(rf"\b{re.escape(variant)}" for variant in variants)) for variants in word_variants]
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            """SELECT product_id, name, garment_type, price, image_file_path,
                      description, colors, search_tags FROM catalogue"""
        ).fetchall()
    scored = []
    for row in rows:
        searchable = " ".join(str(row[field]) for field in ("name", "garment_type", "description", "colors", "search_tags")).lower()
        score = sum(bool(pattern.search(searchable)) for pattern in patterns)
        if score:
            scored.append((score, row))
    best_score = max((score for score, _ in scored), default=0)
    best = sorted((row for score, row in scored if score == best_score), key=lambda row: row["name"].lower())
    rows = best[: max(1, min(limit, 8))]
    return ProductSearchResult(
        total_matches=len(best),
        products=[
            ProductCard(
                product_id=row["product_id"], name=row["name"], price=row["price"],
                image_url=_image_url(row["image_file_path"]), description=row["description"],
            )
            for row in rows
        ],
    )


def get_product_cards_by_ids(product_ids: list[str]) -> list[ProductCard]:
    """Hydrate cards from SQLite so model-invented products cannot reach the frontend."""
    unique_ids = list(dict.fromkeys(product_ids))[:8]
    if not unique_ids:
        return []
    placeholders = ",".join("?" for _ in unique_ids)
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            f"""SELECT product_id, name, price, image_file_path, description
                 FROM catalogue WHERE product_id IN ({placeholders})""",
            unique_ids,
        ).fetchall()
    by_id = {row["product_id"]: row for row in rows}
    return [
        ProductCard(
            product_id=by_id[product_id]["product_id"], name=by_id[product_id]["name"],
            price=by_id[product_id]["price"], image_url=_image_url(by_id[product_id]["image_file_path"]),
            description=by_id[product_id]["description"],
        )
        for product_id in unique_ids if product_id in by_id
    ]


def _find_products(connection: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    normalized = query.strip().lower()
    like = "%" + normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    exact = connection.execute(
        """SELECT product_id, name, description, price, colors, image_file_path
           FROM catalogue WHERE lower(product_id) = ? OR lower(name) = ?""",
        (normalized, normalized),
    ).fetchall()
    if exact:
        return exact
    return connection.execute(
        """SELECT product_id, name, description, price, colors, image_file_path
           FROM catalogue
           WHERE lower(name) LIKE ? ESCAPE '\\' OR lower(product_id) LIKE ? ESCAPE '\\'
           ORDER BY name COLLATE NOCASE LIMIT 6""",
        (like, like),
    ).fetchall()


def get_product_details(product_query: str) -> ProductLookupResult:
    """Get database facts for a product: description, current price, colors, and all size inventory.

    Pass an exact product ID or name when possible. If a partial name matches multiple
    products, this returns candidates instead of guessing which product the shopper means.
    """
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        matches = _find_products(connection, product_query)
        if not matches:
            return ProductLookupResult(found=False, message=f'No product matching "{product_query}" was found.')
        if len(matches) > 1:
            candidates = [row["name"] for row in matches]
            return ProductLookupResult(
                found=False,
                message="That description matches multiple products. Ask the shopper which one they mean.",
                candidates=candidates,
            )
        product = matches[0]
        inventory = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product["product_id"],)
        ).fetchall()
    colors: list[str] = []
    try:
        parsed = json.loads(product["colors"])
        if isinstance(parsed, list):
            colors = [str(color) for color in parsed]
    except (json.JSONDecodeError, TypeError):
        colors = [product["colors"]] if product["colors"] else []
    stock = [InventoryItem(size=row["size"], quantity=row["quantity"], available=row["quantity"] > 0) for row in inventory]
    return ProductLookupResult(
        found=True,
        message="Product details retrieved from the catalogue and inventory tables.",
        product_id=product["product_id"], name=product["name"], description=product["description"],
        price=product["price"], colors=colors, inventory=stock,
        total_quantity=sum(item.quantity for item in stock),
    )


def check_size_inventory(product_query: str, size: str) -> StockLookupResult:
    """Check the exact database quantity for one requested product size.

    Always use this for questions asking whether a particular size is available.
    A zero quantity means out of stock. Missing products or sizes are reported explicitly.
    """
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        matches = _find_products(connection, product_query)
        if not matches:
            return StockLookupResult(found_product=False, found_size=False, available=False, message=f'No product matching "{product_query}" was found.')
        if len(matches) > 1:
            return StockLookupResult(found_product=False, found_size=False, available=False, message=f'Multiple products match: {", ".join(row["name"] for row in matches)}. Ask the shopper to be more specific.')
        product = matches[0]
        rows = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product["product_id"],)
        ).fetchall()
    requested = size.strip().casefold()
    match = next((row for row in rows if row["size"].strip().casefold() == requested), None)
    available_sizes = [row["size"] for row in rows if row["quantity"] > 0]
    if match is None:
        return StockLookupResult(
            found_product=True, found_size=False, available=False, product_id=product["product_id"],
            name=product["name"], size=size.strip(), available_sizes=available_sizes,
            message=f'Size {size.strip()} is not offered for {product["name"]}.',
        )
    quantity = int(match["quantity"])
    message = f'Size {match["size"]} has {quantity} units in stock.' if quantity > 0 else f'Size {match["size"]} is out of stock.'
    return StockLookupResult(
        found_product=True, found_size=True, available=quantity > 0, product_id=product["product_id"],
        name=product["name"], size=match["size"], quantity=quantity, available_sizes=available_sizes, message=message,
    )
