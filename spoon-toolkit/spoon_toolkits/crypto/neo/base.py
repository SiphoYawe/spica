"""Base module for Neo blockchain tools"""

from .neo_provider import NeoProvider

def get_provider(network: str = "testnet") -> NeoProvider:
    """Get Neo provider instance"""
    return NeoProvider(network) 