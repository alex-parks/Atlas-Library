# backend/api/products.py - Products API using generic CRUD handler
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.api.generic_crud import GenericCRUDHandler

# Pydantic models for products
class ProductBase(BaseModel):
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    stock_quantity: int = Field(0, ge=0, description="Stock quantity")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    specifications: dict = Field(default_factory=dict, description="Product specifications")
    is_active: bool = Field(True, description="Whether product is active")

class ProductCreate(ProductBase):
    """Model for creating a product"""
    pass

class ProductUpdate(BaseModel):
    """Model for updating a product - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = None
    manufacturer: Optional[str] = None
    tags: Optional[List[str]] = None
    specifications: Optional[dict] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    """Model for product responses"""
    id: str
    created_at: str
    updated_at: str
    
    class Config:
        populate_by_name = True

# Create products CRUD handler
products_crud = GenericCRUDHandler(
    collection_name="products",
    response_model=ProductResponse,
    create_model=ProductCreate,
    update_model=ProductUpdate,
    id_prefix="prod",
    searchable_fields=["name", "description", "category", "manufacturer", "sku"],
    expandable_relations=["suppliers", "reviews", "inventory"]
)

# Get the router
router = products_crud.get_router()

# Add custom endpoints specific to products
from fastapi import Query, HTTPException
from typing import Dict

@router.get("/by-category/{category}")
async def get_products_by_category(
    category: str,
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Only show in-stock products")
):
    """Get products by category with optional price filtering"""
    db = products_crud.get_db()
    
    try:
        # Build query
        filters = ["doc.category == @category"]
        bind_vars = {"category": category}
        
        if min_price is not None:
            filters.append("doc.price >= @min_price")
            bind_vars["min_price"] = min_price
        
        if max_price is not None:
            filters.append("doc.price <= @max_price")
            bind_vars["max_price"] = max_price
        
        if in_stock_only:
            filters.append("doc.stock_quantity > 0")
        
        query = f"""
        FOR doc IN products
            FILTER {' AND '.join(filters)}
            SORT doc.price ASC
            RETURN doc
        """
        
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        products = list(cursor)
        
        return [ProductResponse(**product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting products: {str(e)}")

@router.post("/{product_id}/update-stock")
async def update_product_stock(
    product_id: str,
    quantity_change: int = Query(..., description="Positive to add, negative to subtract")
):
    """Update product stock quantity"""
    db = products_crud.get_db()
    collection = db.collection("products")
    
    try:
        if not collection.has(product_id):
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Get current product
        product = collection.get(product_id)
        current_stock = product.get("stock_quantity", 0)
        new_stock = current_stock + quantity_change
        
        if new_stock < 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Current: {current_stock}, Requested change: {quantity_change}"
            )
        
        # Update stock
        collection.update(product_id, {
            "stock_quantity": new_stock,
            "updated_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "product_id": product_id,
            "previous_stock": current_stock,
            "new_stock": new_stock,
            "change": quantity_change
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stock: {str(e)}")

@router.get("/low-stock")
async def get_low_stock_products(threshold: int = Query(10, ge=0, description="Stock threshold")):
    """Get products with low stock"""
    db = products_crud.get_db()
    
    try:
        query = """
        FOR doc IN products
            FILTER doc.stock_quantity <= @threshold AND doc.is_active == true
            SORT doc.stock_quantity ASC
            RETURN doc
        """
        
        cursor = db.aql.execute(query, bind_vars={"threshold": threshold})
        products = list(cursor)
        
        return [ProductResponse(**product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting low stock products: {str(e)}")