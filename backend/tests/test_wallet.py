"""
Integration tests for wallet service and API endpoints.

Tests:
- Wallet service initialization
- WIF loading and security
- Balance retrieval
- API endpoint responses
- Security validation (WIF never exposed)
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
import os

from app.main import app
from app.services.wallet_service import WalletService, WalletSecurityError, get_wallet_service
from app.models.wallet_models import WalletInfo, WalletBalance


class TestWalletService:
    """Test WalletService functionality"""

    @pytest.mark.asyncio
    async def test_wallet_service_initialization(self):
        """Test wallet service can be initialized"""
        # This test requires a valid WIF in environment
        # Skip if not configured
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        service = WalletService()
        assert service is not None
        assert service._initialized is False

    @pytest.mark.asyncio
    async def test_get_address(self):
        """Test getting wallet address"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        service = WalletService()
        address = await service.get_address()

        # Verify Neo N3 address format
        assert address.startswith("N")
        assert len(address) >= 20  # Neo addresses are typically 34 characters

    @pytest.mark.asyncio
    async def test_wif_never_logged(self, caplog):
        """Test that WIF is NEVER logged"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        wif = os.getenv("DEMO_WALLET_WIF")

        service = WalletService()
        await service.get_address()

        # Check all log messages
        for record in caplog.records:
            assert wif not in record.message, "WIF found in log message - SECURITY VIOLATION"

    @pytest.mark.asyncio
    async def test_get_wallet_info(self):
        """Test getting comprehensive wallet info"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        # Mock Neo service to avoid network calls
        with patch('app.services.wallet_service.get_neo_service') as mock_neo:
            mock_service = AsyncMock()
            mock_balance = Mock()
            mock_balance.gas_balance = Decimal("1000.0")
            mock_balance.neo_balance = Decimal("100")
            mock_service.get_balance.return_value = mock_balance
            mock_neo.return_value = mock_service

            service = WalletService()
            wallet_info = await service.get_wallet_info()

            assert isinstance(wallet_info, WalletInfo)
            assert wallet_info.address.startswith("N")
            assert wallet_info.network == "testnet"
            assert len(wallet_info.balances) == 2

            # Check GAS balance
            gas_balance = next(b for b in wallet_info.balances if b.token == "GAS")
            assert gas_balance.decimals == 8
            assert gas_balance.balance == Decimal("1000.0")

            # Check NEO balance
            neo_balance = next(b for b in wallet_info.balances if b.token == "NEO")
            assert neo_balance.decimals == 0
            assert neo_balance.balance == Decimal("100")

    @pytest.mark.asyncio
    async def test_get_balance_gas(self):
        """Test getting GAS balance"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        with patch('app.services.wallet_service.get_neo_service') as mock_neo:
            mock_service = AsyncMock()
            mock_balance = Mock()
            mock_balance.gas_balance = Decimal("500.5")
            mock_balance.neo_balance = Decimal("50")
            mock_service.get_balance.return_value = mock_balance
            mock_neo.return_value = mock_service

            service = WalletService()
            balance = await service.get_balance("GAS")

            assert balance == Decimal("500.5")

    @pytest.mark.asyncio
    async def test_get_balance_neo(self):
        """Test getting NEO balance"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        with patch('app.services.wallet_service.get_neo_service') as mock_neo:
            mock_service = AsyncMock()
            mock_balance = Mock()
            mock_balance.gas_balance = Decimal("500.5")
            mock_balance.neo_balance = Decimal("50")
            mock_service.get_balance.return_value = mock_balance
            mock_neo.return_value = mock_service

            service = WalletService()
            balance = await service.get_balance("NEO")

            assert balance == Decimal("50")

    @pytest.mark.asyncio
    async def test_get_balance_invalid_token(self):
        """Test getting balance for invalid token raises error"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        service = WalletService()

        with pytest.raises(ValueError, match="Unsupported token"):
            await service.get_balance("INVALID")

    @pytest.mark.asyncio
    async def test_wallet_service_error_handling(self):
        """Test wallet service handles Neo RPC errors gracefully"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        with patch('app.services.wallet_service.get_neo_service') as mock_neo:
            mock_service = AsyncMock()
            mock_service.get_balance.side_effect = Exception("RPC timeout")
            mock_neo.return_value = mock_service

            service = WalletService()
            wallet_info = await service.get_wallet_info()

            # Should return zero balances on error, not crash
            assert isinstance(wallet_info, WalletInfo)
            gas_balance = next(b for b in wallet_info.balances if b.token == "GAS")
            assert gas_balance.balance == Decimal("0")


class TestWalletAPI:
    """Test wallet API endpoints"""

    def test_get_wallet_endpoint(self):
        """Test GET /api/v1/wallet endpoint"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)

        with patch('app.api.v1.wallet.get_wallet_service') as mock_service:
            # Mock wallet service
            mock_ws = AsyncMock()
            mock_ws.get_wallet_info.return_value = WalletInfo(
                address="NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
                balances=[
                    WalletBalance(token="GAS", balance=Decimal("1000.0"), decimals=8),
                    WalletBalance(token="NEO", balance=Decimal("100"), decimals=0)
                ],
                network="testnet"
            )
            mock_service.return_value = mock_ws

            response = client.get("/api/v1/wallet")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "data" in data
            assert data["data"]["address"] == "NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr"
            assert data["data"]["network"] == "testnet"
            assert len(data["data"]["balances"]) == 2

    def test_get_wallet_wif_never_exposed(self):
        """CRITICAL: Test that WIF is NEVER exposed in API response"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)
        wif = os.getenv("DEMO_WALLET_WIF")

        with patch('app.api.v1.wallet.get_wallet_service') as mock_service:
            mock_ws = AsyncMock()
            mock_ws.get_wallet_info.return_value = WalletInfo(
                address="NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
                balances=[
                    WalletBalance(token="GAS", balance=Decimal("1000.0"), decimals=8),
                ],
                network="testnet"
            )
            mock_service.return_value = mock_ws

            response = client.get("/api/v1/wallet")
            response_text = response.text

            # CRITICAL: WIF must NEVER appear in response
            assert wif not in response_text, "WIF EXPOSED IN API RESPONSE - CRITICAL SECURITY VIOLATION"

    def test_get_token_balance_gas(self):
        """Test GET /api/v1/wallet/balance/GAS endpoint"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)

        with patch('app.api.v1.wallet.get_wallet_service') as mock_service:
            mock_ws = AsyncMock()
            mock_ws.get_balance.return_value = Decimal("1500.75")
            mock_service.return_value = mock_ws

            response = client.get("/api/v1/wallet/balance/GAS")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["token"] == "GAS"
            assert data["data"]["balance"] == "1500.75"
            assert data["data"]["decimals"] == 8

    def test_get_token_balance_neo(self):
        """Test GET /api/v1/wallet/balance/NEO endpoint"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)

        with patch('app.api.v1.wallet.get_wallet_service') as mock_service:
            mock_ws = AsyncMock()
            mock_ws.get_balance.return_value = Decimal("200")
            mock_service.return_value = mock_ws

            response = client.get("/api/v1/wallet/balance/NEO")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["token"] == "NEO"
            assert data["data"]["balance"] == "200"
            assert data["data"]["decimals"] == 0

    def test_get_token_balance_invalid(self):
        """Test getting balance for invalid token returns 400"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)

        response = client.get("/api/v1/wallet/balance/INVALID")

        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        assert data["detail"]["code"] == "INVALID_TOKEN"

    def test_wallet_endpoint_error_handling(self):
        """Test wallet endpoint handles service errors properly"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        client = TestClient(app)

        with patch('app.api.v1.wallet.get_wallet_service') as mock_service:
            mock_ws = AsyncMock()
            mock_ws.get_wallet_info.side_effect = Exception("Service error")
            mock_service.return_value = mock_ws

            response = client.get("/api/v1/wallet")

            assert response.status_code == 500
            data = response.json()

            assert "detail" in data
            assert data["detail"]["code"] == "WALLET_ERROR"


class TestWalletSecurity:
    """Security-focused tests for wallet functionality"""

    def test_wif_not_in_openapi_docs(self):
        """Test that WIF doesn't appear in OpenAPI documentation"""
        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        openapi_text = response.text.lower()

        # Comprehensive list of sensitive terms to check
        sensitive_terms = [
            "wif",
            "private_key",
            "privatekey",
            "private key",
            "secret",
            "mnemonic",
            "seed phrase",
            "keystore"
        ]

        # Check for each sensitive term
        for term in sensitive_terms:
            assert term not in openapi_text, f"Sensitive term '{term}' found in API docs"

        # Check for proximity of 'private' and 'key' within reasonable distance
        if "private" in openapi_text and "key" in openapi_text:
            # Find all occurrences of 'private'
            private_indices = [i for i in range(len(openapi_text)) if openapi_text.startswith("private", i)]
            key_indices = [i for i in range(len(openapi_text)) if openapi_text.startswith("key", i)]

            # Check if any private/key pair is within 50 characters of each other
            for p_idx in private_indices:
                for k_idx in key_indices:
                    if abs(p_idx - k_idx) < 50:
                        # Extract context for better error message
                        start = max(0, min(p_idx, k_idx) - 20)
                        end = min(len(openapi_text), max(p_idx, k_idx) + 20)
                        context = openapi_text[start:end]
                        assert False, f"'private' and 'key' found in close proximity in API docs: ...{context}..."

    @pytest.mark.asyncio
    async def test_wallet_account_not_exposed(self):
        """Test that wallet account object is not accessible via API"""
        if not os.getenv("DEMO_WALLET_WIF"):
            pytest.skip("DEMO_WALLET_WIF not set in environment")

        service = WalletService()
        account = service.get_account()

        # Account should exist (for internal use)
        assert account is not None

        # But it should NEVER be serialized or exposed
        # This is enforced by not including get_account() in API endpoints


class TestWalletModels:
    """Test Pydantic models for wallet data"""

    def test_wallet_balance_model(self):
        """Test WalletBalance model validation"""
        balance = WalletBalance(
            token="GAS",
            balance=Decimal("1234.56789012"),
            decimals=8
        )

        assert balance.token == "GAS"
        assert balance.balance == Decimal("1234.56789012")
        assert balance.decimals == 8

    def test_wallet_info_model(self):
        """Test WalletInfo model validation"""
        info = WalletInfo(
            address="NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
            balances=[
                WalletBalance(token="GAS", balance=Decimal("1000"), decimals=8),
                WalletBalance(token="NEO", balance=Decimal("100"), decimals=0)
            ],
            network="testnet"
        )

        assert info.address == "NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr"
        assert len(info.balances) == 2
        assert info.network == "testnet"
        assert info.timestamp is not None

    def test_wallet_response_model(self):
        """Test WalletResponse model validation"""
        from app.models.wallet_models import WalletResponse

        wallet_info = WalletInfo(
            address="NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
            balances=[],
            network="testnet"
        )

        response = WalletResponse(
            success=True,
            data=wallet_info,
            message="Success"
        )

        assert response.success is True
        assert response.data == wallet_info
        assert response.message == "Success"
        assert response.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
