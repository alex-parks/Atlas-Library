# backend/api/todos.py - Todos API with ArangoDB integration
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import os
from backend.assetlibrary.config import BlacksmithAtlasConfig

router = APIRouter(prefix="/api/v1", tags=["todos"])

# Initialize ArangoDB handler (with error handling)
try:
    from backend.assetlibrary.database.arango_queries import AssetQueries
    arango_config = BlacksmithAtlasConfig.get_database_config()
    
    # Custom TodoQueries class for todo-specific operations
    class TodoQueries(AssetQueries):
        def __init__(self, db_config: dict):
            super().__init__(db_config)
            # Ensure todos collection exists
            if not self.db.has_collection('todos'):
                self.db.create_collection('todos')
            self.todos = self.db.collection('todos')
        
        def get_all_todos(self, user_id: Optional[str] = None, completed: Optional[bool] = None) -> List[dict]:
            """Get all todos with optional filtering"""
            query = """
            FOR todo IN todos
                FILTER (@user_id == null OR todo.user_id == @user_id)
                FILTER (@completed == null OR todo.completed == @completed)
                SORT todo.created_at DESC
                RETURN todo
            """
            
            bind_vars = {
                'user_id': user_id,
                'completed': completed
            }
            
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        
        def get_todo_by_id(self, todo_id: str) -> Optional[dict]:
            """Get a specific todo by ID"""
            try:
                return self.db.collection('todos').get(todo_id)
            except Exception:
                return None
        
        def create_todo(self, todo_data: dict) -> dict:
            """Create a new todo"""
            todo_data['_key'] = todo_data.get('_key', uuid.uuid4().hex[:12])
            todo_data['created_at'] = datetime.now().isoformat()
            todo_data['updated_at'] = datetime.now().isoformat()
            
            result = self.todos.insert(todo_data)
            todo_data['_id'] = result['_id']
            return todo_data
        
        def update_todo(self, todo_id: str, update_data: dict) -> Optional[dict]:
            """Update an existing todo"""
            try:
                update_data['updated_at'] = datetime.now().isoformat()
                result = self.todos.update({'_key': todo_id}, update_data, return_new=True)
                return result['new']
            except Exception:
                return None
        
        def delete_todo(self, todo_id: str) -> bool:
            """Delete a todo"""
            try:
                self.todos.delete({'_key': todo_id})
                return True
            except Exception:
                return False
        
        def get_todo_statistics(self, user_id: Optional[str] = None) -> dict:
            """Get todo statistics"""
            query = """
            LET todos = (
                FOR todo IN todos
                    FILTER (@user_id == null OR todo.user_id == @user_id)
                    RETURN todo
            )
            
            LET completed_todos = (
                FOR todo IN todos
                    FILTER todo.completed == true
                    RETURN todo
            )
            
            LET pending_todos = (
                FOR todo IN todos
                    FILTER todo.completed == false
                    RETURN todo
            )
            
            LET high_priority = (
                FOR todo IN todos
                    FILTER todo.priority == "high"
                    RETURN todo
            )
            
            LET overdue_todos = (
                FOR todo IN todos
                    FILTER todo.due_date != null AND todo.due_date < DATE_NOW() AND todo.completed == false
                    RETURN todo
            )
            
            RETURN {
                total_todos: LENGTH(todos),
                completed: LENGTH(completed_todos),
                pending: LENGTH(pending_todos),
                high_priority: LENGTH(high_priority),
                overdue: LENGTH(overdue_todos),
                completion_rate: LENGTH(todos) > 0 ? (LENGTH(completed_todos) * 100 / LENGTH(todos)) : 0
            }
            """
            
            bind_vars = {'user_id': user_id}
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return cursor.next()
    
    todo_queries = TodoQueries(arango_config)
    database_available = True
except Exception as e:
    todo_queries = None
    database_available = False

# Pydantic models for request/response
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Todo title")
    description: Optional[str] = Field(None, max_length=1000, description="Todo description")
    completed: bool = Field(default=False, description="Completion status")
    priority: str = Field(default="medium", description="Priority level")
    category: Optional[str] = Field(None, max_length=50, description="Todo category")
    due_date: Optional[datetime] = Field(None, description="Due date")
    user_id: Optional[str] = Field(None, description="User ID who owns this todo")
    tags: List[str] = Field(default=[], description="Todo tags")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TodoCreateRequest(TodoBase):
    """Request model for creating todos"""
    pass

class TodoUpdateRequest(BaseModel):
    """Request model for updating todos"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TodoResponse(TodoBase):
    """Response model for todos"""
    id: str = Field(..., description="Todo ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

def convert_todo_to_response(todo_data: dict) -> TodoResponse:
    """Convert database todo to response model"""
    return TodoResponse(
        id=todo_data.get('_key', todo_data.get('id', '')),
        title=todo_data.get('title', ''),
        description=todo_data.get('description'),
        completed=todo_data.get('completed', False),
        priority=todo_data.get('priority', 'medium'),
        category=todo_data.get('category'),
        due_date=todo_data.get('due_date'),
        user_id=todo_data.get('user_id'),
        tags=todo_data.get('tags', []),
        created_at=todo_data.get('created_at', datetime.now().isoformat()),
        updated_at=todo_data.get('updated_at', datetime.now().isoformat())
    )

# API Endpoints

@router.get("/todos", response_model=List[TodoResponse])
async def list_todos(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all todos with optional filtering"""
    if not database_available or not todo_queries:
        return []
    
    try:
        raw_todos = todo_queries.get_all_todos(user_id=user_id, completed=completed)
        todos = []
        
        for todo_data in raw_todos[:limit]:
            try:
                # Apply additional filters
                if category and todo_data.get('category') != category:
                    continue
                if priority and todo_data.get('priority') != priority:
                    continue
                    
                todo_response = convert_todo_to_response(todo_data)
                todos.append(todo_response)
            except Exception as e:
                continue
                
        return todos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading todos: {str(e)}")

@router.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str):
    """Get a specific todo by ID"""
    if not database_available or not todo_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        todo_data = todo_queries.get_todo_by_id(todo_id)
        if not todo_data:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return convert_todo_to_response(todo_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/todos", response_model=TodoResponse)
async def create_todo(todo_request: TodoCreateRequest):
    """Create a new todo"""
    if not database_available or not todo_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if todo_request.priority not in valid_priorities:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        
        todo_data = {
            'title': todo_request.title,
            'description': todo_request.description,
            'completed': todo_request.completed,
            'priority': todo_request.priority,
            'category': todo_request.category,
            'due_date': todo_request.due_date.isoformat() if todo_request.due_date else None,
            'user_id': todo_request.user_id,
            'tags': todo_request.tags
        }
        
        created_todo = todo_queries.create_todo(todo_data)
        return convert_todo_to_response(created_todo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")

@router.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: str, todo_update: TodoUpdateRequest):
    """Update an existing todo"""
    if not database_available or not todo_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Check if todo exists
        existing_todo = todo_queries.get_todo_by_id(todo_id)
        if not existing_todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # Prepare update data (only include non-None values)
        update_data = {}
        if todo_update.title is not None:
            update_data['title'] = todo_update.title
        if todo_update.description is not None:
            update_data['description'] = todo_update.description
        if todo_update.completed is not None:
            update_data['completed'] = todo_update.completed
        if todo_update.priority is not None:
            # Validate priority
            valid_priorities = ["low", "medium", "high", "urgent"]
            if todo_update.priority not in valid_priorities:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
                )
            update_data['priority'] = todo_update.priority
        if todo_update.category is not None:
            update_data['category'] = todo_update.category
        if todo_update.due_date is not None:
            update_data['due_date'] = todo_update.due_date.isoformat()
        if todo_update.user_id is not None:
            update_data['user_id'] = todo_update.user_id
        if todo_update.tags is not None:
            update_data['tags'] = todo_update.tags
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        updated_todo = todo_queries.update_todo(todo_id, update_data)
        if not updated_todo:
            raise HTTPException(status_code=500, detail="Failed to update todo")
        
        return convert_todo_to_response(updated_todo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")

@router.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a todo"""
    if not database_available or not todo_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Check if todo exists
        existing_todo = todo_queries.get_todo_by_id(todo_id)
        if not existing_todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        success = todo_queries.delete_todo(todo_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete todo")
        
        return {"message": f"Todo {todo_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting todo: {str(e)}")

@router.get("/todos/stats/summary")
async def get_todo_stats(
    user_id: Optional[str] = Query(None, description="Get stats for specific user")
):
    """Get todo statistics"""
    if not database_available or not todo_queries:
        return {
            "total_todos": 0,
            "completed": 0,
            "pending": 0,
            "high_priority": 0,
            "overdue": 0,
            "completion_rate": 0,
            "note": "Database not available"
        }
    
    try:
        stats = todo_queries.get_todo_statistics(user_id=user_id)
        return {
            "total_todos": stats.get('total_todos', 0),
            "completed": stats.get('completed', 0),
            "pending": stats.get('pending', 0),
            "high_priority": stats.get('high_priority', 0),
            "overdue": stats.get('overdue', 0),
            "completion_rate": round(stats.get('completion_rate', 0), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/todos/categories")
async def get_todo_categories():
    """Get all todo categories"""
    if not database_available or not todo_queries:
        return {
            "categories": [],
            "count": 0,
            "note": "Database not available"
        }
    
    try:
        query = """
        FOR todo IN todos
            FILTER todo.category != null
            COLLECT category = todo.category WITH COUNT INTO count
            SORT category ASC
            RETURN {category: category, count: count}
        """
        
        cursor = todo_queries.db.aql.execute(query)
        results = list(cursor)
        categories = [r['category'] for r in results]
        
        return {
            "categories": categories,
            "count": len(categories),
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/todos/priorities")
async def get_todo_priorities():
    """Get todo priority distribution"""
    if not database_available or not todo_queries:
        return {
            "priorities": [],
            "note": "Database not available"
        }
    
    try:
        query = """
        FOR todo IN todos
            COLLECT priority = todo.priority WITH COUNT INTO count
            SORT priority ASC
            RETURN {priority: priority, count: count}
        """
        
        cursor = todo_queries.db.aql.execute(query)
        results = list(cursor)
        
        return {
            "priorities": results,
            "available_priorities": ["low", "medium", "high", "urgent"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.patch("/todos/{todo_id}/complete")
async def toggle_todo_completion(todo_id: str):
    """Toggle todo completion status"""
    if not database_available or not todo_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        existing_todo = todo_queries.get_todo_by_id(todo_id)
        if not existing_todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        new_status = not existing_todo.get('completed', False)
        update_data = {'completed': new_status}
        
        updated_todo = todo_queries.update_todo(todo_id, update_data)
        if not updated_todo:
            raise HTTPException(status_code=500, detail="Failed to update todo")
        
        return {
            "message": f"Todo marked as {'completed' if new_status else 'pending'}",
            "todo": convert_todo_to_response(updated_todo)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")