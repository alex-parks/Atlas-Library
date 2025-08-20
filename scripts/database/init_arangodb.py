#!/usr/bin/env python3
"""Initialize ArangoDB for Blacksmith Atlas"""

from arango import ArangoClient
import os
import sys

def init_database():
    # Connect to ArangoDB system database
    host = os.getenv('ARANGO_HOST', 'localhost')
    port = os.getenv('ARANGO_PORT', '8529')
    username = os.getenv('ARANGO_USER', 'root')
    password = os.getenv('ARANGO_PASSWORD', 'atlas_password')
    database_name = os.getenv('ARANGO_DATABASE', 'blacksmith_atlas')
    
    # Create connection URL
    url = f"http://{host}:{port}"
    
    print(f"Connecting to ArangoDB at {url}...")
    
    try:
        # Connect to system database
        client = ArangoClient(hosts=[url])
        sys_db = client.db('_system', username=username, password=password)
        
        # Create database if it doesn't exist
        if not sys_db.has_database(database_name):
            print(f"Creating database '{database_name}'...")
            sys_db.create_database(database_name)
            print(f"Database '{database_name}' created successfully!")
        else:
            print(f"Database '{database_name}' already exists.")
        
        # Connect to the new database
        db = client.db(database_name, username=username, password=password)
        
        # Create Atlas_Library collection only
        collections = ['Atlas_Library']
        
        for collection_name in collections:
            if not db.has_collection(collection_name):
                print(f"Creating collection '{collection_name}'...")
                db.create_collection(collection_name)
                print(f"Collection '{collection_name}' created successfully!")
            else:
                print(f"Collection '{collection_name}' already exists.")
        
        # Only using Atlas_Library collection for assets
        
        print("\nDatabase initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nError initializing database: {e}")
        return False

if __name__ == "__main__":
    # Set environment variables for Docker
    if 'ARANGO_HOST' not in os.environ:
        os.environ['ARANGO_HOST'] = 'localhost'
    
    success = init_database()
    sys.exit(0 if success else 1)