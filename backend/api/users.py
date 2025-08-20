# backend/api/users.py - Users API using generic CRUD handler
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re
from backend.api.generic_crud import GenericCRUDHandler

# Pydantic models for users
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: str = Field("user", description="User role")
    department: Optional[str] = Field(None, description="Department")
    phone: Optional[str] = Field(None, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    preferences: dict = Field(default_factory=dict, description="User preferences")
    is_active: bool = Field(True, description="Whether user is active")

    @validator('email')
    def validate_email(cls, v):
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v

    @validator('username')
    def validate_username(cls, v):
        # Username should contain only alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['user', 'admin', 'manager', 'artist', 'producer', 'viewer']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

class UserCreate(UserBase):
    """Model for creating a user"""
    password: str = Field(..., min_length=8, description="Password")

    @validator('password')
    def validate_password(cls, v):
        # Password should contain at least one uppercase, one lowercase, and one number
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    """Model for updating a user - all fields optional"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    preferences: Optional[dict] = None
    is_active: Optional[bool] = None

    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v

    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['user', 'admin', 'manager', 'artist', 'producer', 'viewer']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

class UserResponse(UserBase):
    """Model for user responses - excludes sensitive information"""
    id: str
    created_at: str
    updated_at: str
    last_login: Optional[str] = None
    
    class Config:
        populate_by_name = True

# Create users CRUD handler
users_crud = GenericCRUDHandler(
    collection_name="users",
    response_model=UserResponse,
    create_model=UserCreate,
    update_model=UserUpdate,
    id_prefix="user",
    searchable_fields=["username", "email", "first_name", "last_name", "department"],
    expandable_relations=["projects", "assets", "permissions"]
)

# Get the router
router = users_crud.get_router()

# Add custom endpoints specific to users
from fastapi import Query, HTTPException, Depends
from typing import Dict
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt, stored_hash = hashed.split(':')
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex() == stored_hash
    except:
        return False

# Override the create method to handle password hashing
@router.post("", response_model=UserResponse)
async def create_user_with_password(user: UserCreate):
    """Create a new user with password hashing"""
    db = users_crud.get_db()
    collection = db.collection("users")
    
    try:
        # Check if username or email already exists
        existing_query = """
        FOR doc IN users
            FILTER doc.username == @username OR doc.email == @email
            RETURN doc
        """
        cursor = db.aql.execute(existing_query, bind_vars={
            "username": user.username,
            "email": user.email
        })
        existing_users = list(cursor)
        
        if existing_users:
            existing_user = existing_users[0]
            if existing_user.get('username') == user.username:
                raise HTTPException(status_code=409, detail="Username already exists")
            if existing_user.get('email') == user.email:
                raise HTTPException(status_code=409, detail="Email already exists")
        
        # Generate ID and hash password
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = hash_password(user.password)
        
        # Create document (exclude password from response)
        doc = user.dict()
        del doc['password']  # Remove plain password
        doc["_key"] = user_id
        doc["id"] = user_id
        doc["password_hash"] = password_hash  # Store hashed password
        doc["created_at"] = datetime.now().isoformat()
        doc["updated_at"] = datetime.now().isoformat()
        
        # Insert into database
        result = collection.insert(doc)
        
        # Remove password_hash from response
        response_doc = {k: v for k, v in doc.items() if k != 'password_hash'}
        
        return UserResponse(**response_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/by-role/{role}")
async def get_users_by_role(
    role: str,
    department: Optional[str] = Query(None, description="Filter by department"),
    active_only: bool = Query(True, description="Only show active users")
):
    """Get users by role with optional department filtering"""
    db = users_crud.get_db()
    
    try:
        # Build query
        filters = ["doc.role == @role"]
        bind_vars = {"role": role}
        
        if department:
            filters.append("doc.department == @department")
            bind_vars["department"] = department
        
        if active_only:
            filters.append("doc.is_active == true")
        
        query = f"""
        FOR doc IN users
            FILTER {' AND '.join(filters)}
            SORT doc.last_name ASC, doc.first_name ASC
            RETURN doc
        """
        
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        users = list(cursor)
        
        # Remove password_hash from all responses
        clean_users = [
            {k: v for k, v in user.items() if k != 'password_hash'} 
            for user in users
        ]
        
        return [UserResponse(**user) for user in clean_users]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@router.post("/{user_id}/change-password")
async def change_user_password(
    user_id: str,
    current_password: str = Field(..., description="Current password"),
    new_password: str = Field(..., min_length=8, description="New password")
):
    """Change user password"""
    db = users_crud.get_db()
    collection = db.collection("users")
    
    try:
        if not collection.has(user_id):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get user with password hash
        user = collection.get(user_id)
        stored_hash = user.get("password_hash")
        
        if not stored_hash or not verify_password(current_password, stored_hash):
            raise HTTPException(status_code=403, detail="Invalid current password")
        
        # Validate new password
        if not re.search(r'[A-Z]', new_password):
            raise HTTPException(status_code=400, detail='New password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', new_password):
            raise HTTPException(status_code=400, detail='New password must contain at least one lowercase letter')
        if not re.search(r'\d', new_password):
            raise HTTPException(status_code=400, detail='New password must contain at least one number')
        
        # Hash new password and update
        new_hash = hash_password(new_password)
        
        collection.update(user_id, {
            "password_hash": new_hash,
            "updated_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Password changed successfully",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")

@router.post("/{user_id}/update-login")
async def update_last_login(user_id: str):
    """Update user's last login timestamp"""
    db = users_crud.get_db()
    collection = db.collection("users")
    
    try:
        if not collection.has(user_id):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Update last login
        collection.update(user_id, {
            "last_login": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Last login updated",
            "user_id": user_id,
            "last_login": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating login: {str(e)}")

@router.get("/statistics")
async def get_user_statistics():
    """Get user statistics"""
    db = users_crud.get_db()
    
    try:
        query = """
        FOR doc IN users
            COLLECT role = doc.role WITH COUNT INTO count
            RETURN {role: role, count: count}
        """
        
        cursor = db.aql.execute(query)
        role_stats = list(cursor)
        
        total_query = "RETURN LENGTH(users)"
        total_cursor = db.aql.execute(total_query)
        total_users = list(total_cursor)[0]
        
        active_query = """
        FOR doc IN users
            FILTER doc.is_active == true
            RETURN doc
        """
        active_cursor = db.aql.execute(active_query)
        active_users = len(list(active_cursor))
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "by_role": {stat['role']: stat['count'] for stat in role_stats}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")