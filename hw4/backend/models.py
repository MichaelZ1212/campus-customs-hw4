"""Shared request and structured response models for the chat API."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class PageContext(BaseModel):
    path: str = Field(max_length=500)
    product_id: str | None = Field(default=None, max_length=200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    page: PageContext


class ProductCard(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: str
    description: str


class ProductSearchResult(BaseModel):
    total_matches: int = Field(ge=0, description="How many catalogue products matched the search in total.")
    products: list[ProductCard] = Field(description="The best-ranked matches; may be fewer than total_matches.")


class InventoryItem(BaseModel):
    size: str = Field(description="The size label exactly as stored in inventory.")
    quantity: int = Field(ge=0, description="The current database stock count for this size.")
    available: bool = Field(description="True only when quantity is greater than zero.")


class ProductLookupResult(BaseModel):
    found: bool
    message: str
    product_id: str | None = None
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    colors: list[str] = Field(default_factory=list)
    inventory: list[InventoryItem] = Field(default_factory=list)
    total_quantity: int = Field(default=0, ge=0)
    candidates: list[str] = Field(default_factory=list)


class StockLookupResult(BaseModel):
    found_product: bool
    found_size: bool
    available: bool
    message: str
    product_id: str | None = None
    name: str | None = None
    size: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    available_sizes: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str = Field(description="The assistant's helpful response to the shopper.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Products grounded in tool results that are relevant to the response.",
    )


class ChatApiResponse(ChatResponse):
    """API response; `show_on_page` is set by the backend, never by the model."""

    show_on_page: bool = False


class StoredChatMessage(ChatMessage):
    id: int
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str
