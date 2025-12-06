"""Asset-related tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetAssetCountTool(BaseTool):
    name: str = "get_asset_count"
    description: str = "Get total number of assets on Neo blockchain. Useful when you need to understand the scale of assets on the network or analyze asset distribution. Returns an integer representing the total asset count."
    parameters: dict = {
        "type": "object",
        "properties": {
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": []
    }

    async def execute(self, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                response = await provider._make_request("GetAssetCount", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Asset count: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetAssetInfoByHashTool(BaseTool):
    name: str = "get_asset_info_by_hash"
    description: str = "Get detailed asset information by asset hash on Neo blockchain. Useful when you need to verify asset details or analyze specific asset properties. Returns asset information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "asset_hash": {
                "type": "string",
                "description": "Asset hash, must be a valid hexadecimal format (e.g., 0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["asset_hash"]
    }

    async def execute(self, asset_hash: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure ContractHash has 0x prefix
                contract_hash = provider._ensure_0x_prefix(asset_hash)
                
                response = await provider._make_request("GetAssetInfoByContractHash", {"ContractHash": contract_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Asset info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetAssetInfoByNameTool(BaseTool):
    name: str = "get_asset_info_by_name"
    description: str = "Search Neo blockchain assets by human-readable name with fuzzy matching support. Useful when you need to verify NEP-17 or NEP-11 asset details. Returns a JSON object with keys: type, hash, symbol, tokenname, decimals, totalsupply, holders, firsttransfertime, ispopular."
    parameters: dict = {
        "type": "object",
        "properties": {
            "asset_name": {
                "type": "string",
                "description": "Asset name on Neo blockchain, supports fuzzy matching, e.g., 'NEO', 'GAS', 'FLM'"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            }
        },
        "required": ["asset_name"]
    }

    async def execute(self, asset_name: str, network: str = "testnet", Limit: int = None, Skip: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Build request parameters
                request_params = {"Name": asset_name}

                # Add optional parameters if provided
                if Limit is not None:
                    request_params["Limit"] = Limit
                if Skip is not None:
                    request_params["Skip"] = Skip

                response = await provider._make_request("GetAssetInfosByName", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Asset info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetAssetInfosTool(BaseTool):
    name: str = "get_asset_infos"
    description: str = (
        "Query assets metadata by script hash(es). "
        "Useful when you need to check token decimals, symbol, total supply "
        "or identify asset type (NEP-17 or NEP-11)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "addresses": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Script hash of the asset contract",
                },
                "description": (
                    "List of asset contract script hashes, "
                    "e.g., ['0xd2a4cff31913016155e38e474a2c06d08be276cf']"
                ),
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet",
            },
            "Limit": {
                "type": "integer",
                "description": "Limit the number of returned items",
            },
            "Skip": {
                "type": "integer",
                "description": "Number of items to skip",
            },
        },
        "required": ["addresses"],
    }

    async def execute(
        self,
        addresses: list[str],
        network: str = "testnet",
        Limit: int | None = None,
        Skip: int | None = None,
    ) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # GetAssetInfos API expects contract script hashes with 0x prefix
                # Ensure all hashes have 0x prefix
                normalized_hashes = []
                for addr in addresses:
                    if addr.startswith("0x"):
                        # Already has 0x prefix
                        normalized_hashes.append(addr)
                    else:
                        # Check if it's a valid hex string (40 chars for UInt160)
                        hash_str = addr.replace("0x", "").replace("0X", "")
                        if len(hash_str) == 40 and all(c in '0123456789abcdefABCDEF' for c in hash_str):
                            # Valid hash format, add 0x prefix
                            normalized_hashes.append(f"0x{hash_str}")
                        else:
                            # If it's not a valid hash format, try to get script hash from address
                            try:
                                _, script_hash = provider._normalize_address(addr)
                                script_hash_str = str(script_hash).replace("0x", "")
                                normalized_hashes.append(f"0x{script_hash_str}")
                            except Exception:
                                # If normalization fails, add 0x prefix anyway
                                normalized_hashes.append(f"0x{hash_str}")

                request_params = {"Addresses": normalized_hashes}
                if Limit is not None:
                    request_params["Limit"] = Limit
                if Skip is not None:
                    request_params["Skip"] = Skip

                response = await provider._make_request("GetAssetInfos", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=str(e))


class GetAssetInfoByAssetAndAddressTool(BaseTool):
    name: str = "get_asset_info_by_asset_and_address"
    description: str = "Get specific asset balance and details for a particular address on Neo blockchain. Useful when you need to check specific asset balance or details for a particular address. Returns a JSON object with asset and balance information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "asset_hash": {
                "type": "string",
                "description": "Asset hash, must be a valid hexadecimal format"
            },
            "address": {
                "type": "string",
                "description": "Neo address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["asset_hash", "address"]
    }

    async def execute(self, asset_hash: str, address: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # GetAssetsHeldByContractHashAddress API requires Address in script hash format (0x...)
                # If address is not already in script hash format, convert it
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                # Ensure ContractHash has 0x prefix
                contract_hash = provider._ensure_0x_prefix(asset_hash)
                
                response = await provider._make_request("GetAssetsHeldByContractHashAddress",{
                    "Address": address_script_hash,    # Script hash format (0x...)
                    "ContractHash": contract_hash,      # Contract hash with 0x prefix
                    })
                result = provider._handle_response(response)
                return ToolResult(output=f"Asset info: {result}")
        except Exception as e:
            return ToolResult(error=str(e)) 