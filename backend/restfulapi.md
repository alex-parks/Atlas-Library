
# Blacksmith Atlas RESTful API Documentation

## **PRD: ArangoDB FastAPI Backend**

**Version:** 1.0  
**Date:** August 19, 2025  
**Author:** Gemini

---

### **1. Objective** 🎯

To develop a high-performance, RESTful API using **Python FastAPI** that serves as a backend for an existing **ArangoDB** instance running in a Docker container. The primary goal is to provide a standardized, robust interface for interacting with the database, supporting core data manipulation and advanced query operations.

---

### **2. Core Features & Functionality** ✨

This API will expose common endpoints for one or more database collections (e.g., `products`, `users`). The following functionalities are required for each resource:

* **Create (POST)**: Add a new document to a collection.
* **Read (GET)**: Retrieve a single document by its unique key (`_key`).
* **Update (PUT/PATCH)**: Modify an existing document. `PUT` will replace the document, while `PATCH` will apply partial updates.
* **Delete (DELETE)**: Remove a document from a collection.
* **List (GET)**: Retrieve a paginated list of all documents in a collection. This endpoint must support query parameters for `limit` and `offset`.
* **Search (GET)**: A flexible search endpoint that allows querying documents based on specific field values (e.g., `GET /products/search?name=Laptop`).
* **Expand / Graph Traversal (GET)**: An endpoint to retrieve a document and its connected documents from related collections (e.g., a `user` and their `orders`). This will leverage ArangoDB's graph capabilities. Example: `GET /users/{key}/expand?relations=orders`.

---

### **3. Technical Requirements** 💻

* **Framework**: Python 3.10+ with **FastAPI**.
* **Database Driver**: The official `python-arango` driver.
* **Database**: **ArangoDB** (running in a provided Docker container). The API must be configurable to connect to the database instance.
* **API Specification**: The API should automatically generate **OpenAPI (Swagger UI)** and **ReDoc** documentation, a native feature of FastAPI.
* **Data Validation**: Use Pydantic models to define request/response schemas and enforce data validation.
* **Containerization**: The final FastAPI application should also be containerized using **Docker** for easy deployment and scalability.

---

## **Current Implementation Status**

### **Existing API Architecture**

The Blacksmith Atlas API is currently implemented with the following structure:

```
backend/
├── main.py                 # FastAPI application entry point
├── api/
│   ├── assets.py          # Asset management endpoints
│   ├── asset_sync.py      # Admin sync operations
│   └── simple_assets.py   # Simplified asset endpoints
└── assetlibrary/
    ├── config.py          # Configuration management
    ├── database/
    │   ├── arango_queries.py    # ArangoDB query handlers
    │   └── arango_collection_manager.py
    └── models.py          # Pydantic models
```

### **Database Configuration**

- **Host**: `arangodb` (Docker container)
- **Port**: `8529`
- **Database**: `blacksmith_atlas`
- **Collections**: `Atlas_Library`
- **Authentication**: Root user with password

---

## **API Endpoints Documentation**

### **Base URL**
```
http://localhost:8000
```

### **API Versioning**
All API endpoints are versioned under `/api/v1/`

### **Available Endpoints**

#### **1. Asset Management Endpoints** (`/api/v1/assets`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| **GET** | `/api/v1/assets` | List all assets with filtering | ✅ Implemented |
| **GET** | `/api/v1/assets/{asset_id}` | Get specific asset by ID | ✅ Implemented |
| **POST** | `/api/v1/assets` | Create new asset | ✅ Implemented |
| **PUT** | `/api/v1/assets/{asset_id}` | Update entire asset | ❌ Not Implemented |
| **PATCH** | `/api/v1/assets/{asset_id}` | Partial asset update | ❌ Not Implemented |
| **DELETE** | `/api/v1/assets/{asset_id}` | Delete asset | ❌ Not Implemented |
| **GET** | `/api/v1/assets/stats/summary` | Get asset statistics | ✅ Implemented |
| **GET** | `/api/v1/assets/recent/{limit}` | Get recent assets | ✅ Implemented |
| **POST** | `/api/v1/assets/{asset_id}/open-folder` | Open asset folder | ✅ Implemented |

**Query Parameters for GET /api/v1/assets:**
- `search`: Search term for asset names
- `category`: Filter by category
- `tags`: Filter by tags (array)
- `limit`: Maximum results (default: 100)

#### **2. Database & Admin Endpoints**

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| **GET** | `/api/v1/database/status` | Database connection status | ✅ Implemented |
| **GET** | `/api/v1/categories` | List all categories | ✅ Implemented |
| **GET** | `/api/v1/creators` | List all creators | ✅ Implemented |
| **POST** | `/admin/sync` | Sync filesystem to database | ✅ Implemented |
| **POST** | `/admin/sync-bidirectional` | Bidirectional sync | ✅ Implemented |
| **POST** | `/admin/save-config` | Save configuration | ✅ Implemented |

#### **3. System Endpoints**

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| **GET** | `/` | API root information | ✅ Implemented |
| **GET** | `/health` | Health check endpoint | ✅ Implemented |
| **GET** | `/debug/routes` | List all routes | ✅ Implemented |
| **GET** | `/debug/test-connection` | Test DB connection | ✅ Implemented |
| **GET** | `/test-assets` | Test asset query | ✅ Implemented |
| **GET** | `/thumbnails/{asset_id}` | Get asset thumbnail | ✅ Implemented |

---

## **Data Models (Pydantic Schemas)**

### **AssetResponse Model**
```python
{
    "id": "string",
    "name": "string",
    "category": "string",
    "asset_type": "string",
    "paths": {
        "asset_folder": "string",
        "thumbnail": "string",
        "textures": "string",
        "geometry": "string"
    },
    "file_sizes": {},
    "tags": ["string"],
    "metadata": {
        "dimension": "string",
        "asset_type": "string",
        "subcategory": "string",
        "render_engine": "string"
    },
    "created_at": "string",
    "thumbnail_path": "string",
    "artist": "string",
    "file_format": "string",
    "description": "string"
}
```

### **AssetCreateRequest Model**
```python
{
    "name": "string",
    "category": "string",
    "paths": {},
    "metadata": {},
    "file_sizes": {}
}
```

---

## **OpenAPI Documentation**

The API automatically generates interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## **Gap Analysis: PRD vs Current Implementation**

### **Implemented Features** ✅
1. FastAPI framework with Python 3.10+
2. ArangoDB integration with python-arango driver
3. Docker containerization
4. OpenAPI/Swagger documentation
5. Pydantic models for validation
6. Basic CRUD operations (partial)
7. List endpoints with filtering
8. Search functionality

### **Missing Features** ❌
1. Complete CRUD operations (UPDATE, DELETE for assets)
2. Pagination support (offset parameter)
3. Graph traversal/expand endpoints
4. Generic resource endpoints (products, users)
5. Standardized error handling
6. Response time optimization
7. Connection pooling for performance

---

## **Detailed TODO List**

### **High Priority Tasks** 🔴

1. **Complete Asset CRUD Operations**
   - [ ] Implement PUT `/api/v1/assets/{asset_id}` for full update
   - [ ] Implement PATCH `/api/v1/assets/{asset_id}` for partial update
   - [ ] Implement DELETE `/api/v1/assets/{asset_id}` for deletion
   - [ ] Add proper error handling and validation

2. **Add Pagination Support**
   - [ ] Add `offset` parameter to list endpoints
   - [ ] Implement cursor-based pagination for large datasets
   - [ ] Return total count with paginated results

3. **Implement Graph Traversal**
   - [ ] Create expand endpoint for assets with dependencies
   - [ ] Implement graph queries for related data
   - [ ] Add relationship management endpoints

### **Medium Priority Tasks** 🟡

4. **Create Generic Resource Endpoints**
   - [ ] Design generic CRUD handler class
   - [ ] Implement products collection endpoints
   - [ ] Implement users collection endpoints
   - [ ] Add dynamic collection routing

5. **Performance Optimization**
   - [ ] Implement caching layer - implement redis into docker container
 

6. **Error Handling & Validation**
   - [ ] Standardize error response format
   - [ ] Add request validation middleware
   - [ ] Implement rate limiting
   - [ ] Add request logging

### **Low Priority Tasks** 🟢

7. **Documentation & Testing**
   - [ ] Write unit tests for all endpoints
   - [ ] Add integration tests
   - [ ] Create API usage examples
   - [ ] Document deployment process

8. **Monitoring & Analytics**
   - [ ] Add performance metrics
   - [ ] Implement health check improvements
   - [ ] Add database query profiling
   - [ ] Create admin dashboard

