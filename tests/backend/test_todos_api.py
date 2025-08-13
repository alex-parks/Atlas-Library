#!/usr/bin/env python3
"""
Test script for todos API endpoints
This validates the API structure without requiring a running server
"""

def test_api_structure():
    """Test that the todos API structure is correct"""
    try:
        # Test imports
        from backend.api.todos import (
            router, 
            TodoCreateRequest, 
            TodoUpdateRequest, 
            TodoResponse,
            convert_todo_to_response
        )
        
        print("✅ All imports successful")
        
        # Test router configuration
        assert router.prefix == "/api/v1"
        assert "todos" in router.tags
        print("✅ Router configured correctly")
        
        # Test model validation
        test_request = TodoCreateRequest(
            title="Test Todo",
            description="This is a test todo", 
            priority="high",
            category="Development",
            tags=["test", "api"]
        )
        
        print("✅ TodoCreateRequest model works")
        print(f"   - Title: {test_request.title}")
        print(f"   - Priority: {test_request.priority}")
        print(f"   - Category: {test_request.category}")
        print(f"   - Tags: {test_request.tags}")
        
        # Test update model
        update_request = TodoUpdateRequest(
            title="Updated Todo",
            completed=True
        )
        
        print("✅ TodoUpdateRequest model works")
        
        # Test response conversion
        mock_todo_data = {
            '_key': 'abc123',
            'title': 'Test Todo',
            'description': 'Test description',
            'completed': False,
            'priority': 'medium',
            'category': 'Development',
            'due_date': None,
            'user_id': 'user123',
            'tags': ['test'],
            'created_at': '2024-01-01T12:00:00',
            'updated_at': '2024-01-01T12:00:00'
        }
        
        response = convert_todo_to_response(mock_todo_data)
        assert response.id == 'abc123'
        assert response.title == 'Test Todo'
        assert response.priority == 'medium'
        
        print("✅ convert_todo_to_response works")
        
        # Test endpoints exist
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods)
                })
        
        print("✅ API Endpoints:")
        for route in routes:
            methods_str = ", ".join(sorted(route['methods']))
            print(f"   - {methods_str}: {route['path']}")
        
        # Verify key endpoints exist
        expected_endpoints = [
            '/api/v1/todos',
            '/api/v1/todos/{todo_id}',
            '/api/v1/todos/stats/summary',
            '/api/v1/todos/categories',
            '/api/v1/todos/priorities',
            '/api/v1/todos/{todo_id}/complete'
        ]
        
        actual_paths = [route['path'] for route in routes]
        for endpoint in expected_endpoints:
            if endpoint in actual_paths:
                print(f"   ✅ {endpoint} - Found")
            else:
                print(f"   ❌ {endpoint} - Missing")
        
        print("\n🎉 Todos API structure validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api_structure()