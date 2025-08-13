#!/usr/bin/env python3
"""Initialize Company ArangoDB for Blacksmith Atlas"""

from arango import ArangoClient
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_company_database():
    # Get configuration from environment
    host = os.getenv('ARANGO_HOST')
    port = os.getenv('ARANGO_PORT', '8529')
    username = os.getenv('ARANGO_USER')
    password = os.getenv('ARANGO_PASSWORD')
    database_name = os.getenv('ARANGO_DATABASE', 'blacksmith_atlas')
    
    # Validate configuration
    if not host or host == 'your-company-arangodb-host.com':
        print("Error: ARANGO_HOST not configured in .env file")
        return False
    
    if not username or username == 'your_username':
        print("Error: ARANGO_USER not configured in .env file")
        return False
        
    if not password or password == 'your_password':
        print("Error: ARANGO_PASSWORD not configured in .env file")
        return False
    
    # Create connection URL
    url = f"http://{host}:{port}"
    
    print(f"Connecting to ArangoDB at {url}...")
    print(f"Database: {database_name}")
    print(f"User: {username}")
    
    try:
        # Connect to system database
        client = ArangoClient(hosts=[url])
        
        # First try to connect directly to the target database
        try:
            db = client.db(database_name, username=username, password=password)
            print(f"\nSuccessfully connected to existing database '{database_name}'")
        except:
            # If that fails, try to connect to system database to create it
            print(f"\nDatabase '{database_name}' not accessible, attempting to create it...")
            sys_db = client.db('_system', username=username, password=password)
            
            if not sys_db.has_database(database_name):
                print(f"Creating database '{database_name}'...")
                sys_db.create_database(database_name)
                print(f"Database '{database_name}' created successfully!")
            
            # Now connect to the new database
            db = client.db(database_name, username=username, password=password)
        
        # Create collections
        collections = {
            'assets': False,  # Document collection
            'asset_relationships': True,  # Edge collection
            'projects': False,
            'tags': False,
            'users': False,
            'todos': False,
            'ai_jobs': False,
            'workflows': False
        }
        
        print("\nChecking collections...")
        for collection_name, is_edge in collections.items():
            if not db.has_collection(collection_name):
                print(f"Creating collection '{collection_name}'...")
                if is_edge:
                    db.create_collection(collection_name, edge=True)
                else:
                    db.create_collection(collection_name)
                print(f"✓ Collection '{collection_name}' created")
            else:
                print(f"✓ Collection '{collection_name}' already exists")
        
        # Create indexes for better performance
        print("\nCreating indexes...")
        
        # Assets collection indexes
        if db.has_collection('assets'):
            assets = db.collection('assets')
            # Index on name for search
            assets.add_hash_index(fields=['name'], unique=False)
            # Index on category
            assets.add_hash_index(fields=['category'], unique=False)
            # Index on created_at for sorting
            assets.add_skiplist_index(fields=['created_at'], unique=False)
            print("✓ Created indexes for assets collection")
        
        # Test the connection
        print("\nTesting database connection...")
        result = db.aql.execute("RETURN 1")
        print("✓ Database connection test successful!")
        
        # Get statistics
        print("\nDatabase Statistics:")
        for collection_name in collections.keys():
            if db.has_collection(collection_name):
                count = db.collection(collection_name).count()
                print(f"  {collection_name}: {count} documents")
        
        print("\n✅ Company database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your ArangoDB host is accessible")
        print("2. Verify your username and password are correct")
        print("3. Ensure you have permissions to create databases/collections")
        print("4. Check if your company's ArangoDB requires SSL (update URL to https://)")
        return False

if __name__ == "__main__":
    success = init_company_database()
    sys.exit(0 if success else 1)