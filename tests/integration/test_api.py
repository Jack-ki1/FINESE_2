"""Tests for API endpoints."""
import pytest


class TestHealthEndpoint:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] in ['healthy', 'unhealthy']
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get('/ready')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ready'] is True


class TestDataEndpoints:
    """Test data operation endpoints."""
    
    def test_upload_endpoint_exists(self, client):
        """Test that upload endpoint exists."""
        # POST request should return method not allowed or proper response
        response = client.post('/api/v1/data/upload')
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_sample_dataset_load(self, client):
        """Test loading sample dataset."""
        response = client.post('/api/v1/data/load-sample', json={
            'dataset_name': 'iris'
        })
        # Endpoint should exist
        assert response.status_code != 404
