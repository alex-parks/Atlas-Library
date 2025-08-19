#!/usr/bin/env python3
"""
Test Suite for Houdini ArangoDB Integration
==========================================

Comprehensive unit and integration tests for the houdini_arango_insert.py module.
Tests database connection, metadata validation, document insertion, and error handling.
"""

import os
import sys
import json
import pytest
import tempfile
import unittest.mock as mock
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add backend path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Import the module under test
from assetlibrary.houdini.tools.houdini_arango_insert import HoudiniArangoInserter


class TestHoudiniArangoInserter:
    """Test class for HoudiniArangoInserter functionality"""
    
    @pytest.fixture
    def sample_metadata(self) -> Dict[str, Any]:
        """Sample metadata for testing"""
        return {
            "id": "test_asset_001",
            "name": "Test Blacksmith Asset",
            "asset_type": "Assets",
            "category": "Test Category",
            "subcategory": "Test Subcategory",
            "render_engine": "Redshift",
            "created_by": "test_artist",
            "houdini_version": "20.0.547",
            "description": "Test asset for unit testing",
            "tags": ["test", "unittest", "geometry"],
            "created_at": "2024-08-13T10:30:00Z",
            "export_time": "2024-08-13T10:35:00Z",
            "export_context": "houdini_shelf_export",
            "template_file": "/path/to/template.hip",
            "source_hip_file": "/path/to/source.hip",
            "asset_folder": "/net/library/atlaslib/3D/Assets/Test/test_asset_001",
            "metadata_file": "/net/library/atlaslib/3D/Assets/Test/test_asset_001/metadata.json",
            "geometry_folder": "/net/library/atlaslib/3D/Assets/Test/test_asset_001/Geometry",
            "textures_folder": "/net/library/atlaslib/3D/Assets/Test/test_asset_001/Textures"
        }
    
    @pytest.fixture
    def invalid_metadata(self) -> Dict[str, Any]:
        """Invalid metadata for negative testing"""
        return {
            "name": "Asset Without ID",
            "asset_type": "",
            # Missing required fields: id, category
        }
    
    @pytest.fixture
    def temp_asset_folder(self, sample_metadata):
        """Create temporary asset folder with metadata.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_folder = Path(temp_dir) / "test_asset_001"
            asset_folder.mkdir()
            
            # Create metadata.json file
            metadata_file = asset_folder / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(sample_metadata, f, indent=2)
            
            yield str(asset_folder)
    
    def test_initialization_with_mocked_dependencies(self):
        """Test inserter initialization with mocked dependencies"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config:
            
            # Mock configuration
            mock_config.get_database_config.return_value = {
                'hosts': ['http://localhost:8529'],
                'database': 'test_database',
                'username': 'root',
                'password': 'test_password'
            }
            
            with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient'):
                inserter = HoudiniArangoInserter(environment='development')
                
                assert inserter.environment == 'development'
                assert inserter.max_retries == 3
                assert inserter.retry_delay == 1.0
    
    def test_metadata_validation_success(self, sample_metadata):
        """Test successful metadata validation and transformation"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            result = inserter.validate_metadata(sample_metadata)
            
            assert result['valid'] is True
            assert len(result['errors']) == 0
            assert result['transformed_data'] is not None
            
            # Check transformed data structure
            transformed = result['transformed_data']
            assert transformed['_key'] == 'test_asset_001_Test_Blacksmith_Asset'
            assert transformed['id'] == 'test_asset_001'
            assert transformed['name'] == 'Test Blacksmith Asset'
            assert transformed['asset_type'] == 'Assets'
            assert transformed['dimension'] == '3D'
            assert 'hierarchy' in transformed
            assert 'metadata' in transformed
            assert 'paths' in transformed
    
    def test_metadata_validation_failure(self, invalid_metadata):
        """Test metadata validation with invalid data"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            result = inserter.validate_metadata(invalid_metadata)
            
            assert result['valid'] is False
            assert len(result['errors']) > 0
            assert 'Missing required field: id' in result['errors']
            assert 'Missing required field: category' in result['errors']
    
    def test_document_key_sanitization(self):
        """Test document key sanitization for ArangoDB compatibility"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            # Test metadata with problematic characters
            problematic_metadata = {
                "id": "test/asset:001",
                "name": "Asset With <Special> Characters!",
                "asset_type": "Assets",
                "category": "Test"
            }
            
            result = inserter.validate_metadata(problematic_metadata)
            
            assert result['valid'] is True
            transformed = result['transformed_data']
            
            # Check that problematic characters are replaced
            document_key = transformed['_key']
            assert '/' not in document_key
            assert ':' not in document_key
            assert '<' not in document_key
            assert '>' not in document_key
            assert document_key == 'test_asset_001_Asset_With__Special__Characters_'
    
    @mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient')
    def test_database_connection_success(self, mock_arango_client):
        """Test successful database connection"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config:
            
            # Mock configuration
            mock_config.get_database_config.return_value = {
                'hosts': ['http://localhost:8529'],
                'database': 'test_database',
                'username': 'root',
                'password': 'test_password'
            }
            
            # Mock database objects
            mock_db = mock.MagicMock()
            mock_db.properties.return_value = {'name': 'test_database'}
            mock_db.has_collection.return_value = True
            mock_collection = mock.MagicMock()
            mock_db.collection.return_value = mock_collection
            
            mock_client = mock.MagicMock()
            mock_client.db.return_value = mock_db
            mock_arango_client.return_value = mock_client
            
            inserter = HoudiniArangoInserter()
            
            assert inserter.is_connected() is True
            assert inserter.db == mock_db
            assert inserter.asset_collection == mock_collection
    
    @mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient')
    def test_database_connection_failure(self, mock_arango_client):
        """Test database connection failure handling"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config:
            
            # Mock configuration
            mock_config.get_database_config.return_value = {
                'hosts': ['http://localhost:8529'],
                'database': 'test_database',
                'username': 'root',
                'password': 'test_password'
            }
            
            # Mock connection failure
            mock_arango_client.side_effect = Exception("Connection failed")
            
            inserter = HoudiniArangoInserter()
            
            assert inserter.is_connected() is False
            assert inserter.connected is False
    
    def test_document_insertion_success(self, sample_metadata):
        """Test successful document insertion"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            # Mock successful connection
            inserter.connected = True
            mock_collection = mock.MagicMock()
            mock_collection.get.side_effect = Exception("Document not found")  # New document
            mock_collection.insert.return_value = {'_key': 'test_key'}
            inserter.asset_collection = mock_collection
            
            # Validate metadata first
            validation_result = inserter.validate_metadata(sample_metadata)
            document = validation_result['transformed_data']
            
            # Test insertion
            result = inserter.insert_asset_document(document)
            
            assert result is True
            mock_collection.insert.assert_called_once_with(document)
    
    def test_document_update_success(self, sample_metadata):
        """Test successful document update for existing asset"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            # Mock successful connection
            inserter.connected = True
            mock_collection = mock.MagicMock()
            mock_collection.get.return_value = {'_key': 'existing_key'}  # Existing document
            mock_collection.update.return_value = {'_key': 'existing_key'}
            inserter.asset_collection = mock_collection
            
            # Validate metadata first
            validation_result = inserter.validate_metadata(sample_metadata)
            document = validation_result['transformed_data']
            
            # Test update
            result = inserter.insert_asset_document(document)
            
            assert result is True
            mock_collection.update.assert_called_once_with(document)
    
    def test_process_exported_asset_success(self, temp_asset_folder, sample_metadata):
        """Test successful processing of exported asset folder"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            # Mock successful connection and insertion
            inserter.connected = True
            mock_collection = mock.MagicMock()
            mock_collection.get.side_effect = Exception("Document not found")
            mock_collection.insert.return_value = {'_key': 'test_key'}
            inserter.asset_collection = mock_collection
            
            # Test processing
            result = inserter.process_exported_asset(temp_asset_folder)
            
            assert result is True
            mock_collection.insert.assert_called_once()
    
    def test_process_exported_asset_missing_folder(self):
        """Test processing with missing asset folder"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            result = inserter.process_exported_asset("/nonexistent/path")
            
            assert result is False
    
    def test_process_exported_asset_missing_metadata(self):
        """Test processing with missing metadata.json file"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                asset_folder = Path(temp_dir) / "test_asset"
                asset_folder.mkdir()
                # Don't create metadata.json file
                
                result = inserter.process_exported_asset(str(asset_folder))
                
                assert result is False
    
    def test_batch_processing_success(self, sample_metadata):
        """Test successful batch processing of multiple assets"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True):
            
            inserter = HoudiniArangoInserter()
            
            # Mock successful connection
            inserter.connected = True
            mock_collection = mock.MagicMock()
            mock_collection.get.side_effect = Exception("Document not found")
            mock_collection.insert.return_value = {'_key': 'test_key'}
            inserter.asset_collection = mock_collection
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create multiple asset folders
                for i in range(3):
                    asset_folder = Path(temp_dir) / f"test_asset_{i:03d}"
                    asset_folder.mkdir()
                    
                    # Modify metadata for each asset
                    metadata = sample_metadata.copy()
                    metadata['id'] = f"test_asset_{i:03d}"
                    metadata['name'] = f"Test Asset {i:03d}"
                    
                    metadata_file = asset_folder / "metadata.json"
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f)
                
                # Test batch processing
                stats = inserter.batch_process_assets(temp_dir)
                
                assert stats['processed'] == 3
                assert stats['successful'] == 3
                assert stats['failed'] == 0
                assert mock_collection.insert.call_count == 3
    
    def test_retry_logic_on_connection_failure(self):
        """Test retry logic with exponential backoff"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config, \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient') as mock_client, \
             mock.patch('time.sleep') as mock_sleep:
            
            # Mock configuration
            mock_config.get_database_config.return_value = {
                'hosts': ['http://localhost:8529'],
                'database': 'test_database',
                'username': 'root',
                'password': 'test_password'
            }
            
            # Mock connection failure for first 2 attempts, success on 3rd
            mock_client.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                mock.MagicMock()  # Success
            ]
            
            # Mock successful database operations on 3rd attempt
            mock_db = mock.MagicMock()
            mock_db.properties.return_value = {'name': 'test_database'}
            mock_db.has_collection.return_value = True
            mock_collection = mock.MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_client.return_value.db.return_value = mock_db
            
            inserter = HoudiniArangoInserter(max_retries=3)
            
            # Verify retry attempts
            assert mock_client.call_count == 3
            assert mock_sleep.call_count == 2  # 2 retry delays
            
            # Verify exponential backoff delays
            expected_delays = [1.0, 2.0]  # 1.0 * 2^0, 1.0 * 2^1
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays


class TestIntegration:
    """Integration tests requiring more complex setup"""
    
    def test_environment_configuration_loading(self):
        """Test loading configuration from different environments"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config:
            
            # Test development environment
            dev_config = {
                'hosts': ['http://localhost:8529'],
                'database': 'blacksmith_atlas_dev',
                'username': 'root',
                'password': ''
            }
            mock_config.get_database_config.return_value = dev_config
            
            with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient'):
                inserter = HoudiniArangoInserter(environment='development')
                
                assert inserter.environment == 'development'
                assert inserter.db_config == dev_config
                mock_config.get_database_config.assert_called_with('development')
    
    def test_full_workflow_simulation(self, sample_metadata):
        """Test complete workflow from metadata to database insertion"""
        with mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ARANGO_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.CONFIG_AVAILABLE', True), \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.BlacksmithAtlasConfig') as mock_config, \
             mock.patch('assetlibrary.houdini.tools.houdini_arango_insert.ArangoClient') as mock_client:
            
            # Mock complete configuration
            mock_config.get_database_config.return_value = {
                'hosts': ['http://arangodb:8529'],
                'database': 'blacksmith_atlas',
                'username': 'root',
                'password': 'atlas_password'
            }
            
            # Mock database objects
            mock_db = mock.MagicMock()
            mock_db.properties.return_value = {'name': 'blacksmith_atlas'}
            mock_db.has_collection.return_value = True
            mock_collection = mock.MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_collection.get.side_effect = Exception("Document not found")
            mock_collection.insert.return_value = {'_key': 'test_asset_001_Test_Blacksmith_Asset'}
            
            mock_client_instance = mock.MagicMock()
            mock_client_instance.db.return_value = mock_db
            mock_client.return_value = mock_client_instance
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create asset folder with metadata
                asset_folder = Path(temp_dir) / "test_asset_001"
                asset_folder.mkdir()
                
                metadata_file = asset_folder / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(sample_metadata, f, indent=2)
                
                # Initialize inserter and process asset
                inserter = HoudiniArangoInserter(environment='production')
                result = inserter.process_exported_asset(str(asset_folder))
                
                # Verify success
                assert result is True
                
                # Verify database operations
                mock_client.assert_called_once()
                mock_client_instance.db.assert_called_once()
                mock_collection.insert.assert_called_once()
                
                # Verify document structure
                inserted_document = mock_collection.insert.call_args[0][0]
                assert inserted_document['_key'] == 'test_asset_001_Test_Blacksmith_Asset'
                assert inserted_document['id'] == 'test_asset_001'
                assert inserted_document['name'] == 'Test Blacksmith Asset'
                assert inserted_document['asset_type'] == 'Assets'
                assert inserted_document['dimension'] == '3D'
                assert 'metadata' in inserted_document
                assert 'hierarchy' in inserted_document
                assert 'paths' in inserted_document


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])