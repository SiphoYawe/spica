"""
Contract Registry & Configuration Service

Centralized registry for Neo N3 contract hashes with environment-based configuration.
Manages native contracts, Flamingo DEX contracts, and token metadata.

Verified contract hashes from:
- Neo N3 Native Contracts: https://docs.neo.org/docs/n3/reference/scapi/framework/native/
- Flamingo Finance: https://flamingo.finance/
"""

from enum import Enum
from typing import Dict, Optional


class Network(str, Enum):
    """Neo N3 network types."""
    MAINNET = "mainnet"
    TESTNET = "testnet"


class ContractRegistry:
    """
    Centralized registry for Neo N3 contract hashes.

    Supports both mainnet and testnet configurations.
    Contract addresses loaded from environment or defaults.

    Native contract hashes are identical across all Neo N3 networks.
    Flamingo DEX contracts may differ between mainnet and testnet.
    """

    # Native contracts (same on all networks)
    # Source: https://docs.neo.org/docs/n3/reference/scapi/framework/native/
    NATIVE_CONTRACTS = {
        "GAS": "0xd2a4cff31913016155e38e474a2c06d08be276cf",
        "NEO": "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5",
        "ContractManagement": "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd",
        "Policy": "0xcc5e4edd9f5f8dba8bb65734541df7a1c081c67b",
    }

    # Flamingo contracts per network
    # Source: Flamingo Finance official contracts
    FLAMINGO_CONTRACTS = {
        Network.MAINNET: {
            "SWAP_FACTORY": "0xca2d20610d7982ebe0bed124ee7e9b2d580a6efc",
            "SWAP_ROUTER": "0xf970f4ccecd765b63732b821775dc38c25d74f23",  # Router v2
            "FLM_TOKEN": "0xf0151f528127558851b39c2cd8aa47da7418ab28",
            "BNEO_TOKEN": "0x48c40d4666f93408be1bef038b6722404d9a4c2a",
            "FLUND_TOKEN": "0x7a50c6a7cbce53cb04a2e2efbc15ed544c0ac4fb",
        },
        Network.TESTNET: {
            # Testnet contracts - using mainnet hashes as baseline
            # These should be verified against testnet Flamingo deployment
            "SWAP_FACTORY": "0xca2d20610d7982ebe0bed124ee7e9b2d580a6efc",
            "SWAP_ROUTER": "0xf970f4ccecd765b63732b821775dc38c25d74f23",
            "FLM_TOKEN": "0xf0151f528127558851b39c2cd8aa47da7418ab28",
            "BNEO_TOKEN": "0x48c40d4666f93408be1bef038b6722404d9a4c2a",
            "FLUND_TOKEN": "0x7a50c6a7cbce53cb04a2e2efbc15ed544c0ac4fb",
        }
    }

    # Token metadata
    # Decimals define the smallest divisible unit for each token
    TOKEN_DECIMALS = {
        "GAS": 8,   # 1 GAS = 10^8 smallest units
        "NEO": 0,   # NEO is indivisible (whole numbers only)
        "bNEO": 8,  # Wrapped NEO with 8 decimals for DeFi compatibility
        "FLM": 8,   # Flamingo governance token
    }

    def __init__(self, network: Network = Network.TESTNET):
        """
        Initialize contract registry for specified network.

        Args:
            network: Neo N3 network (MAINNET or TESTNET)
        """
        self.network = network
        self._custom_contracts: Dict[str, str] = {}

    def get_native_hash(self, name: str) -> str:
        """
        Get native contract hash.

        Args:
            name: Contract name (GAS, NEO, ContractManagement, Policy)

        Returns:
            Contract script hash with 0x prefix

        Raises:
            KeyError: If contract name not found
        """
        return self.NATIVE_CONTRACTS[name]

    def get_flamingo_hash(self, name: str) -> str:
        """
        Get Flamingo contract hash for current network.

        Args:
            name: Contract name (SWAP_FACTORY, SWAP_ROUTER, FLM_TOKEN, BNEO_TOKEN, FLUND_TOKEN)

        Returns:
            Contract script hash with 0x prefix

        Raises:
            KeyError: If contract name not found for current network
        """
        return self.FLAMINGO_CONTRACTS[self.network][name]

    def get_token_hash(self, token: str) -> str:
        """
        Get token contract hash.

        Handles both native tokens (GAS, NEO) and Flamingo tokens (bNEO, FLM).

        Args:
            token: Token symbol (GAS, NEO, bNEO, FLM)

        Returns:
            Contract script hash with 0x prefix

        Raises:
            ValueError: If token symbol is unknown
        """
        if token in ["GAS", "NEO"]:
            return self.NATIVE_CONTRACTS[token]
        elif token == "bNEO":
            return self.get_flamingo_hash("BNEO_TOKEN")
        elif token == "FLM":
            return self.get_flamingo_hash("FLM_TOKEN")
        else:
            raise ValueError(f"Unknown token: {token}")

    def get_decimals(self, token: str) -> int:
        """
        Get token decimal places.

        Args:
            token: Token symbol (GAS, NEO, bNEO, FLM)

        Returns:
            Number of decimal places (0-8)
            Defaults to 8 if token not found
        """
        return self.TOKEN_DECIMALS.get(token, 8)

    def get_rpc_url(self) -> str:
        """
        Get RPC URL for current network.

        Returns:
            RPC endpoint URL for the configured network

        Raises:
            ImportError: If config module not available
        """
        from app.config import settings

        if self.network == Network.MAINNET:
            return settings.neo_mainnet_rpc
        else:
            return settings.neo_testnet_rpc


# Global singleton instance
_registry: Optional[ContractRegistry] = None


def get_contract_registry() -> ContractRegistry:
    """
    Get global contract registry singleton.

    Initializes registry on first call based on environment configuration.
    Subsequent calls return the same instance.

    Returns:
        ContractRegistry instance configured for current network

    Raises:
        ImportError: If config module not available
    """
    global _registry
    if _registry is None:
        from app.config import settings

        # Determine network from config
        network = Network.MAINNET if settings.neo_network == "mainnet" else Network.TESTNET
        _registry = ContractRegistry(network)

    return _registry
