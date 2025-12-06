"""
Integration tests for API structure (Story 1.4)

Tests:
- CORS configuration
- Health check endpoints
- API versioning structure
- Pydantic model validation
- OpenAPI documentation
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app

client = TestClient(app)


class TestCORSConfiguration:
    """Test CORS middleware configuration"""

    def test_cors_allows_localhost_5173(self):
        """CORS should allow requests from Vite dev server (localhost:5173)"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

    def test_cors_allows_credentials(self):
        """CORS should allow credentials"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_allows_required_methods(self):
        """CORS should allow GET, POST, PUT, DELETE, OPTIONS"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            }
        )
        assert response.status_code == 200
        allowed_methods = response.headers.get("access-control-allow-methods", "").upper()
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "DELETE" in allowed_methods

    def test_cors_allows_x402_headers(self):
        """CORS should allow x402 payment headers"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-PAYMENT-REQUEST,X-PAYMENT",
            }
        )
        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "x-payment-request" in allowed_headers
        assert "x-payment" in allowed_headers

    def test_cors_exposes_payment_headers(self):
        """CORS should expose X-PAYMENT-REQUEST header to frontend"""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        exposed_headers = response.headers.get("access-control-expose-headers", "").lower()
        assert "x-payment-request" in exposed_headers


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Root endpoint should return basic service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Spica API"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data
        assert "docs" in data

    def test_legacy_health_endpoint(self):
        """Legacy /health endpoint should work for backward compatibility"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_health_endpoint(self):
        """GET /api/health should return basic health status"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data

        # Validate values
        assert data["status"] == "ok"
        assert data["service"] == "Spica API"
        assert data["version"] == "0.1.0"

        # Validate timestamp is valid ISO format
        assert datetime.fromisoformat(data["timestamp"].replace("Z", ""))

    def test_api_v1_health_endpoint(self):
        """GET /api/v1/health should return detailed health status"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert "timestamp" in data

        # Validate services
        assert "api" in data["services"]
        assert "neo_rpc" in data["services"]
        assert "spoonos" in data["services"]

        # Validate service status structure
        for service_name, service_status in data["services"].items():
            assert "status" in service_status
            assert service_status["status"] in ["ok", "degraded", "down"]
            assert "message" in service_status or service_status.get("message") is None

        # Overall status should be healthy when all services are ok
        if all(s["status"] == "ok" for s in data["services"].values()):
            assert data["status"] == "healthy"

    def test_api_v1_health_simple_endpoint(self):
        """GET /api/v1/health/simple should return simple health check"""
        response = client.get("/api/v1/health/simple")
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data

        # Validate values
        assert data["status"] == "ok"
        assert data["service"] == "Spica API"


class TestAPIVersioning:
    """Test API versioning structure"""

    def test_v1_prefix_exists(self):
        """API v1 endpoints should be accessible with /api/v1 prefix"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_non_versioned_endpoint_exists(self):
        """Non-versioned /api/health should exist for backward compatibility"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_api_routing_structure(self):
        """Verify proper API routing structure"""
        # Test that both versioned and non-versioned endpoints work
        v1_response = client.get("/api/v1/health")
        root_response = client.get("/api/health")

        assert v1_response.status_code == 200
        assert root_response.status_code == 200

        # They should return different structures
        # v1 is detailed, root is simple
        v1_data = v1_response.json()
        root_data = root_response.json()

        assert "services" in v1_data  # v1 has services
        assert "services" not in root_data  # root doesn't


class TestPydanticModels:
    """Test Pydantic model validation in responses"""

    def test_health_check_response_model(self):
        """Health check responses should match HealthCheckResponse model"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # Required fields from HealthCheckResponse
        required_fields = ["status", "service", "version", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_detailed_health_response_model(self):
        """Detailed health responses should match DetailedHealthResponse model"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()

        # Required fields from DetailedHealthResponse
        required_fields = ["status", "version", "services", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Services should be a dict
        assert isinstance(data["services"], dict)

        # Each service should have status
        for service_name, service_data in data["services"].items():
            assert "status" in service_data

    def test_timestamp_format(self):
        """Timestamps should be valid ISO format"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # Should be parseable as datetime
        timestamp = data["timestamp"]
        # Try parsing - will raise if invalid
        datetime.fromisoformat(timestamp.replace("Z", ""))


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation accessibility"""

    def test_openapi_json_accessible(self):
        """OpenAPI JSON schema should be accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()

        # Validate OpenAPI structure
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # Validate API info
        assert data["info"]["title"] == "Spica API"
        assert data["info"]["version"] == "0.1.0"

    def test_swagger_docs_accessible(self):
        """Swagger UI should be accessible at /docs"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_accessible(self):
        """ReDoc should be accessible at /redoc"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()

    def test_health_endpoint_in_openapi(self):
        """Health endpoints should be documented in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        paths = schema.get("paths", {})

        # Check that health endpoints are documented
        assert "/api/health" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/health/simple" in paths

        # Validate health endpoint has GET method
        assert "get" in paths["/api/health"]

    def test_response_models_in_openapi(self):
        """Response models should be documented in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check components/schemas exist
        assert "components" in schema
        assert "schemas" in schema["components"]

        schemas = schema["components"]["schemas"]

        # Our Pydantic models should be in the schema
        # Note: Pydantic v2 may split models into -Input/-Output variants
        expected_models = [
            "HealthCheckResponse",
            "ServiceStatus"
        ]

        for model_name in expected_models:
            assert model_name in schemas, f"Model {model_name} not in OpenAPI schema"

        # DetailedHealthResponse may appear as -Input/-Output variants in Pydantic v2
        assert (
            "DetailedHealthResponse" in schemas or
            "DetailedHealthResponse-Input" in schemas or
            "DetailedHealthResponse-Output" in schemas
        ), "DetailedHealthResponse (or variant) not in OpenAPI schema"


class TestErrorHandling:
    """Test error handling and error response models"""

    def test_404_for_nonexistent_endpoint(self):
        """Non-existent endpoints should return 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Wrong HTTP method should return 405"""
        # Health endpoints only accept GET
        response = client.post("/api/health")
        assert response.status_code == 405


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
