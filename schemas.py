"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Core app schemas

class WishlistItem(BaseModel):
    """
    Wishlist items for Pokemon TCG cards
    Collection name: "wishlistitem"
    """
    card_id: str = Field(..., description="Pokemon TCG card ID (e.g., sv3-1)")
    name: str = Field(..., description="Card name")
    set_name: Optional[str] = Field(None, description="Set name")
    set_id: Optional[str] = Field(None, description="Set ID")
    number: Optional[str] = Field(None, description="Card number within the set")
    image_url: Optional[str] = Field(None, description="Primary image URL for the card")
    desired_price: Optional[float] = Field(None, ge=0, description="Target price to buy")
    notes: Optional[str] = Field(None, description="User notes")
    status: str = Field("watching", description="watching | bought | removed")


# Example schemas (kept for reference)
class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
