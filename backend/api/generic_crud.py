# backend/api/generic_crud.py - Generic CRUD handler for ArangoDB collections
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Type, Generic, TypeVar, Dict, Any
from pydantic import BaseModel, Field, create_model
from datetime import datetime
import uuid
import logging
from backend.assetlibrary.config import BlacksmithAtlasConfig
from backend.assetlibrary.database.arango_queries import AssetQueries

logger = logging.getLogger(__name__)

# Type variables for generic models
T = TypeVar('T', bound=BaseModel)
CreateT = TypeVar('CreateT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of items to skip")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

class GenericCRUDHandler(Generic[T, CreateT, UpdateT]):
    """
    Generic CRUD handler for ArangoDB collections
    
    Usage:
        products_crud = GenericCRUDHandler(
            collection_name="products",
            response_model=ProductResponse,
            create_model=ProductCreate,
            update_model=ProductUpdate
        )
        router = products_crud.get_router()
    """
    
    def __init__(
        self,
        collection_name: str,
        response_model: Type[T],
        create_model: Type[CreateT],
        update_model: Type[UpdateT],
        id_prefix: Optional[str] = None,
        searchable_fields: List[str] = None,
        expandable_relations: List[str] = None
    ):
        self.collection_name = collection_name
        self.response_model = response_model
        self.create_model = create_model
        self.update_model = update_model
        self.id_prefix = id_prefix or collection_name[:-1]  # Remove 's' from collection name
        self.searchable_fields = searchable_fields or ["name", "description", "category"]
        self.expandable_relations = expandable_relations or []
        self.router = APIRouter(prefix=f"/{collection_name}", tags=[collection_name])
        self._setup_routes()
    
    def get_db(self):
        """Get database connection"""
        try:
            environment = os.getenv('ATLAS_ENV', 'development')
            arango_config = BlacksmithAtlasConfig.get_database_config(environment)
            queries = AssetQueries(arango_config)
            
            # Ensure collection exists
            if not queries.db.has_collection(self.collection_name):
                queries.db.create_collection(self.collection_name)
            
            return queries.db
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            raise HTTPException(status_code=503, detail="Database not available")
    
    def _setup_routes(self):
        """Setup all CRUD routes"""
        
        @self.router.get("", response_model=PaginatedResponse[self.response_model])
        async def list_items(
            search: Optional[str] = Query(None, description="Search term"),
            pagination: PaginationParams = Depends()
        ):
            """List all items with pagination and search"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                # Build search query
                if search:
                    search_conditions = []
                    for field in self.searchable_fields:
                        search_conditions.append(f"CONTAINS(LOWER(doc.{field}), LOWER(@search))")
                    
                    query = f"""
                    FOR doc IN {self.collection_name}
                        FILTER {' OR '.join(search_conditions)}
                        SORT doc.created_at DESC
                        RETURN doc
                    """
                    bind_vars = {"search": search}
                else:
                    query = f"""
                    FOR doc IN {self.collection_name}
                        SORT doc.created_at DESC
                        RETURN doc
                    """
                    bind_vars = {}
                
                # Execute query
                cursor = db.aql.execute(query, bind_vars=bind_vars)
                all_items = list(cursor)
                
                # Apply pagination
                total = len(all_items)
                items = all_items[pagination.offset:pagination.offset + pagination.limit]
                
                return PaginatedResponse(
                    items=[self.response_model(**item) for item in items],
                    total=total,
                    limit=pagination.limit,
                    offset=pagination.offset,
                    has_more=(pagination.offset + pagination.limit) < total
                )
                
            except Exception as e:
                logger.error(f"Error listing {self.collection_name}: {e}")
                raise HTTPException(status_code=500, detail=f"Error listing items: {str(e)}")
        
        @self.router.post("", response_model=self.response_model)
        async def create_item(item: self.create_model):
            """Create a new item"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                # Generate ID
                item_id = f"{self.id_prefix}_{uuid.uuid4().hex[:8]}"
                
                # Create document
                doc = item.dict()
                doc["_key"] = item_id
                doc["id"] = item_id
                doc["created_at"] = datetime.now().isoformat()
                doc["updated_at"] = datetime.now().isoformat()
                
                # Insert into database
                result = collection.insert(doc)
                
                logger.info(f"Created {self.collection_name} item: {item_id}")
                return self.response_model(**doc)
                
            except Exception as e:
                logger.error(f"Error creating {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")
        
        @self.router.get("/{item_id}", response_model=self.response_model)
        async def get_item(item_id: str):
            """Get a specific item by ID"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                if not collection.has(item_id):
                    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
                
                doc = collection.get(item_id)
                return self.response_model(**doc)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error getting item: {str(e)}")
        
        @self.router.put("/{item_id}", response_model=self.response_model)
        async def update_item(item_id: str, item: self.create_model):
            """Full update of an item"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                if not collection.has(item_id):
                    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
                
                # Get existing document for metadata preservation
                existing = collection.get(item_id)
                
                # Create updated document
                doc = item.dict()
                doc["_key"] = item_id
                doc["id"] = item_id
                doc["created_at"] = existing.get("created_at", datetime.now().isoformat())
                doc["updated_at"] = datetime.now().isoformat()
                
                # Replace document
                result = collection.replace(item_id, doc)
                
                logger.info(f"Updated {self.collection_name} item: {item_id}")
                return self.response_model(**doc)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")
        
        @self.router.patch("/{item_id}", response_model=self.response_model)
        async def patch_item(item_id: str, updates: Dict[str, Any]):
            """Partial update of an item"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                if not collection.has(item_id):
                    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
                
                # Add update timestamp
                updates["updated_at"] = datetime.now().isoformat()
                
                # Update document
                result = collection.update(item_id, updates)
                
                # Get updated document
                doc = collection.get(item_id)
                
                logger.info(f"Patched {self.collection_name} item: {item_id}")
                return self.response_model(**doc)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error patching {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error patching item: {str(e)}")
        
        @self.router.delete("/{item_id}")
        async def delete_item(item_id: str):
            """Delete an item"""
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                if not collection.has(item_id):
                    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
                
                # Delete document
                result = collection.delete(item_id)
                
                logger.info(f"Deleted {self.collection_name} item: {item_id}")
                
                return {
                    "success": True,
                    "message": f"Item {item_id} deleted successfully",
                    "deleted_id": item_id
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")
        
        @self.router.get("/{item_id}/expand")
        async def expand_item(
            item_id: str,
            relations: Optional[List[str]] = Query(None, description="Relations to expand")
        ):
            """Get item with expanded relationships"""
            if not self.expandable_relations:
                raise HTTPException(
                    status_code=501, 
                    detail="Expansion not implemented for this collection"
                )
            
            db = self.get_db()
            collection = db.collection(self.collection_name)
            
            try:
                if not collection.has(item_id):
                    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
                
                doc = collection.get(item_id)
                result = {
                    "item": self.response_model(**doc),
                    "relations": {}
                }
                
                # Expand requested relations
                relations = relations or self.expandable_relations
                
                for relation in relations:
                    if relation in self.expandable_relations:
                        # Custom expansion logic per relation type
                        # This would be implemented based on specific use cases
                        result["relations"][relation] = []
                
                return result
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error expanding {self.collection_name} item: {e}")
                raise HTTPException(status_code=500, detail=f"Error expanding item: {str(e)}")
        
        @self.router.get("/search")
        async def search_items(
            **kwargs: Dict[str, Any]
        ):
            """Search items by field values"""
            db = self.get_db()
            
            try:
                # Build filter conditions
                conditions = []
                bind_vars = {}
                
                for field, value in kwargs.items():
                    if value is not None:
                        conditions.append(f"doc.{field} == @{field}")
                        bind_vars[field] = value
                
                if not conditions:
                    raise HTTPException(status_code=400, detail="No search parameters provided")
                
                query = f"""
                FOR doc IN {self.collection_name}
                    FILTER {' AND '.join(conditions)}
                    RETURN doc
                """
                
                cursor = db.aql.execute(query, bind_vars=bind_vars)
                items = list(cursor)
                
                return [self.response_model(**item) for item in items]
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error searching {self.collection_name}: {e}")
                raise HTTPException(status_code=500, detail=f"Error searching items: {str(e)}")
    
    def get_router(self) -> APIRouter:
        """Get the configured router"""
        return self.router


# Import os module that was missing
import os