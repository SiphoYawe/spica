"""NEP standard tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetNep11BalanceTool(BaseTool):
    name: str = "get_nep11_balance"
    description: str = "Gets the Nep11 balance by contract script hash user's address and tokenId of the Nep11 standard."
    parameters: dict = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Neo address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "contract_hash": {
                "type": "string",
                "description": "contract hash, must be valid hexadecimal format (e.g., 0x1234567890abcdef)"
            },
            "token_id": {
                "type": "string",
                "description": "NFT token ID, base64 format (e.g., QmxpbmQgQm94IDIxNQ==)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["address", "contract_hash", "token_id"]
    }

    async def execute(self, address: str, contract_hash: str, token_id: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                # Ensure ContractHash has 0x prefix
                contract_hash_normalized = provider._ensure_0x_prefix(contract_hash)
                
                response = await provider._make_request("GetNep11BalanceByContractHashAddressTokenId", {
                    "ContractHash": contract_hash_normalized,
                    "Address": address_script_hash,
                    "TokenId": token_id
                })
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-11 balance: {result}")
        except Exception as e:
                return ToolResult(error=str(e))


class GetNep11ByAddressAndHashTool(BaseTool):
    name: str = "get_nep11_by_address_and_hash"
    description: str = "Get detailed NEP-11 token information by address and asset hash on Neo blockchain. Useful when you need to get detailed NFT information for a specific address and asset combination. Returns NEP-11 token details."
    parameters: dict = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Neo address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "asset_hash": {
                "type": "string",
                "description": "Asset hash, must be valid hexadecimal format (e.g., 0x1234567890abcdef)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["address", "asset_hash"]
    }

    async def execute(self, address: str, asset_hash: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                # Ensure ContractHash has 0x prefix
                asset_hash_normalized = provider._ensure_0x_prefix(asset_hash)
                
                request_params = {
                    "Address": address_script_hash,
                    "ContractHash": asset_hash_normalized
                }

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep11OwnedByContractHashAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-11 tokens: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep11TransferByAddressTool(BaseTool):
    name: str = "get_nep11_transfer_by_address"
    description: str = "Get NEP-11 token transfer records by address on Neo blockchain. Useful when you need to track NFT transfer history or analyze NFT transaction patterns for a specific address. Returns NEP-11 transfer data."
    parameters: dict = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Neo address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["address"]
    }

    async def execute(self, address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                
                request_params = {"Address": address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep11TransferByAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-11 transfers: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep11TransferByBlockHeightTool(BaseTool):
    name: str = "get_nep11_transfer_by_block_height"
    description: str = "Get NEP-11 token transfer records in a block by block height on Neo blockchain. Useful when you need to analyze NFT transfers in a specific block or track NFT activity by block position. Returns NEP-11 transfer data."
    parameters: dict = {
        "type": "object",
        "properties": {
            "block_height": {
                "type": "integer",
                "description": "Block height, must be greater than or equal to 0"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["block_height"]
    }

    async def execute(self, block_height: int, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                request_params = {"BlockHeight": block_height}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep11TransferByBlockHeight", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-11 transfers: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetNep11TransferByTransactionHashTool(BaseTool):
    name: str = "get_nep11_transfer_by_transaction_hash"
    description: str = "Get NEP-11 token transfer details by transaction hash on Neo blockchain. Useful when you need to analyze specific NFT transfer transactions or verify NFT transfer details. Returns NEP-11 transfer details."
    parameters: dict = {
        "type": "object",
        "properties": {
            "transaction_hash": {
                "type": "string",
                "description": "Transaction hash, must be valid hexadecimal format (e.g., 0x1234567890abcdef)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["transaction_hash"]
    }

    async def execute(self, transaction_hash: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                request_params = {"TransactionHash": transaction_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep11TransferByTransactionHash", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                
                # Handle None response
                if response is None:
                    debug_info = f"Transaction Hash: {transaction_hash}, Network: {network}, Params: {request_params}"
                    return ToolResult(error=f"GetNep11TransferByTransactionHash returned null. {debug_info}. This may indicate the transaction has no NEP-11 transfers, or there may be an API issue.")
                
                result = provider._handle_response(response)
                
                # Handle nested result structure (some APIs return {"result": {"result": [...]}})
                if isinstance(result, dict):
                    # Check for double nesting: {"result": {"result": [...]}}
                    if "result" in result and isinstance(result["result"], dict) and "result" in result["result"]:
                        transfers_list = result["result"].get("result", [])
                    # Check for single nesting: {"result": [...]}
                    elif "result" in result:
                        transfers_list = result.get("result", [])
                    else:
                        # If it's a dict but no "result" key, try to use it as-is
                        transfers_list = result
                    
                    # Ensure transfers_list is a list
                    if not isinstance(transfers_list, list):
                        transfers_list = [transfers_list] if transfers_list is not None else []
                    
                    result = transfers_list
                
                # Handle empty list result
                if isinstance(result, list) and len(result) == 0:
                    debug_info = f"Transaction Hash: {transaction_hash}, Network: {network}, Params: {request_params}, Response type: list (empty)"
                    return ToolResult(output=f"NEP-11 transfers: [] (empty - no NEP-11 transfers found for this transaction. {debug_info})")
                
                # Handle None result (shouldn't happen after _handle_response, but just in case)
                if result is None:
                    debug_info = f"Transaction Hash: {transaction_hash}, Network: {network}, Params: {request_params}, Response type: None"
                    return ToolResult(error=f"GetNep11TransferByTransactionHash returned null result. {debug_info}. This may indicate the transaction has no NEP-11 transfers, or there may be an API issue.")
                
                # Add debug info for successful results
                debug_info = f"Transaction Hash: {transaction_hash}, Network: {network}, Params: {request_params}, Response type: {type(result).__name__}, Result length: {len(result) if isinstance(result, list) else 'N/A'}"
                return ToolResult(output=f"NEP-11 transfers: {result}. {debug_info}")
        except RuntimeError as e:
            if "Empty response" in str(e):
                debug_info = f"Transaction Hash: {transaction_hash}, Network: {network}, Params: {request_params if 'request_params' in locals() else 'unknown'}"
                return ToolResult(error=f"GetNep11TransferByTransactionHash returned empty response. {debug_info}. The transaction may not have any NEP-11 transfers, or there may be an API issue.")
            return ToolResult(error=str(e))
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep11TransferCountByAddressTool(BaseTool):
    name: str = "get_nep11_transfer_count_by_address"
    description: str = "Get NEP-11 token transfer count statistics by address on Neo blockchain. Useful when you need to analyze NFT activity level or track NFT transfer frequency for a specific address. Returns an integer representing the transfer count."
    parameters: dict = {
        "type": "object",
        "properties": {
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
        "required": ["address"]
    }

    async def execute(self, address: str, network: str = "testnet") -> ToolResult:
        normalized_address = None
        address_script_hash = None
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                # Get normalized address for debug info
                try:
                    normalized_address, _ = provider._normalize_address(address if not address.startswith("0x") else address)
                except:
                    normalized_address = None
                
                response = await provider._make_request("GetNep11TransferCountByAddress", {"Address": address_script_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                
                result = provider._handle_response(response)
                
                # Handle nested result structure (some APIs return {"result": <value>})
                if isinstance(result, dict):
                    # Check for nested result
                    if "result" in result:
                        result = result.get("result")
                    # If it's a dict with a numeric value, try to extract it
                    elif len(result) == 1:
                        result = list(result.values())[0]
                
                return ToolResult(output=f"NEP-11 transfer count: {result}")
        except RuntimeError as e:
            # Handle case where _handle_response raises RuntimeError for None
            if "Empty response" in str(e):
                debug_info = f"Address: {normalized_address or address} (Script Hash: {address_script_hash or 'unknown'}), Network: {network}"
                return ToolResult(error=f"GetNep11TransferCountByAddress returned empty response. {debug_info}. The address may not have any NEP-11 transfers, or there may be an API issue.")
            return ToolResult(error=str(e))
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep17TransferByAddressTool(BaseTool):
    name: str = "get_nep17_transfer_by_address"
    description: str = "Get NEP-17 token transfer records by address on Neo blockchain. Useful when you need to track fungible token transfer history or analyze token transaction patterns for a specific address. Returns NEP-17 transfer data."
    parameters: dict = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Neo address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["address"]
    }

    async def execute(self, address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                
                request_params = {"Address": address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep17TransferByAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-17 transfers: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep17TransferByBlockHeightTool(BaseTool):
    name: str = "get_nep17_transfer_by_block_height"
    description: str = "Get NEP-17 token transfer records in a block by block height on Neo blockchain. Useful when you need to analyze fungible token transfers in a specific block or track token activity by block position. Returns NEP-17 transfer data."
    parameters: dict = {
        "type": "object",
        "properties": {
            "block_height": {
                "type": "integer",
                "description": "Block height, must be greater than or equal to 0"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["block_height"]
    }

    async def execute(self, block_height: int, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                request_params = {"BlockHeight": block_height}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep17TransferByBlockHeight", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-17 transfers: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep17TransferByContractHashTool(BaseTool):
    name: str = "get_nep17_transfer_by_contract_hash"
    description: str = "Get NEP-17 token transfer records by contract hash on Neo blockchain. Useful when you need to analyze token transfers for a specific contract or track contract token activity. Returns NEP-17 transfer data."
    parameters: dict = {
        "type": "object",
        "properties": {
            "contract_hash": {
                "type": "string",
                "description": "Contract hash, must be valid hexadecimal format (e.g., 0x1234567890abcdef)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["contract_hash"]
    }

    async def execute(self, contract_hash: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure ContractHash has 0x prefix
                contract_hash_normalized = provider._ensure_0x_prefix(contract_hash)
                
                request_params = {"ContractHash": contract_hash_normalized}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep17TransferByContractHash", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-17 transfers: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep17TransferByTransactionHashTool(BaseTool):
    name: str = "get_nep17_transfer_by_transaction_hash"
    description: str = "Get NEP-17 token transfer details by transaction hash on Neo blockchain. Useful when you need to analyze specific token transfer transactions or verify token transfer details. Returns NEP-17 transfer details."
    parameters: dict = {
        "type": "object",
        "properties": {
            "transaction_hash": {
                "type": "string",
                "description": "Transaction hash, must be valid hexadecimal format (e.g., 0x1234567890abcdef)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of items to skip"
            },
            "Limit": {
                "type": "integer",
                "description": "the number of items to return"
            }
        },
        "required": ["transaction_hash"]
    }

    async def execute(self, transaction_hash: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                request_params = {"TransactionHash": transaction_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetNep17TransferByTransactionHash", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-17 transfers: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetNep17TransferCountByAddressTool(BaseTool):
    name: str = "get_nep17_transfer_count_by_address"
    description: str = "Get NEP-17 token transfer count statistics by address on Neo blockchain. Useful when you need to analyze token activity level or track token transfer frequency for a specific address. Returns an integer representing the transfer count."
    parameters: dict = {
        "type": "object",
        "properties": {
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
        "required": ["address"]
    }

    async def execute(self, address: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format (0x...) if not already
                if address.startswith("0x"):
                    address_script_hash = address
                else:
                    _, script_hash = provider._normalize_address(address)
                    address_script_hash = f"0x{str(script_hash).replace('0x', '')}"
                
                response = await provider._make_request("GetNep17TransferCountByAddress", {"Address": address_script_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"NEP-17 transfer count: {result}")
        except Exception as e:
                return ToolResult(error=str(e)) 