"""Block-related tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetBlockCountTool(BaseTool):
    name: str = "get_block_count"
    description: str = "Get total number of blocks on Neo blockchain. Useful when you need to understand blockchain growth or verify current block height. Returns an integer representing the total block count."
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
                result = await provider.get_block_count()
                return ToolResult(output=f"Block count: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetBlockByHashTool(BaseTool):
    name: str = "get_block_by_hash"
    description: str = "Get detailed block information by block hash on Neo blockchain. Useful when you need to analyze specific block details or verify block data. Returns block information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "block_hash": {
                "type": "string",
                "description": "Block hash, must be a valid hexadecimal format"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["block_hash"]
    }

    async def execute(self, block_hash: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure BlockHash has 0x prefix
                normalized_hash = provider._ensure_0x_prefix(block_hash)
                
                response = await provider._make_request("GetBlockByBlockHash", {"BlockHash": normalized_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Block info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetBlockByHeightTool(BaseTool):
    name: str = "get_block_by_height"
    description: str = "Get block information by block height on Neo blockchain. Useful when you need to retrieve block data by position or analyze historical blocks. Returns block information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "block_height": {
                "type": "integer",
                "description": "Block height, must be a non-negative integer",
                "minimum": 0
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["block_height"]
    }

    async def execute(self, block_height: int, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                response = await provider._make_request("GetBlockByBlockHeight", {"BlockHeight":block_height})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Block info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetBestBlockHashTool(BaseTool):
    name: str = "get_best_block_hash"
    description: str = "Get the current best block hash on Neo blockchain. Useful when you need to identify the latest block or verify blockchain tip. Returns the best block hash."
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
                response = await provider._make_request("GetBestBlockHash", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Best block hash: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetRecentBlocksInfoTool(BaseTool):
    name: str = "get_recent_blocks_info"
    description: str = "Get recent blocks information list on Neo blockchain. Useful when you need to monitor recent blockchain activity or analyze recent blocks. IMPORTANT: Always specify the Limit parameter to control how many blocks to return. If user requests a specific number (e.g., '100 blocks'), you MUST use Limit parameter with that exact number. Returns recent blocks information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Limit": {
                "type": "integer",
                "description": "The number of blocks to return. REQUIRED when user specifies a number of blocks (e.g., '100 blocks', '50 blocks'). If not specified, API may return a default smaller number. Always use this parameter when user requests a specific count."
            },
            "Skip": {
                "type": "integer",
                "description": "The number of blocks to skip from the beginning. Use 0 to start from the most recent blocks."
            }
        },
        "required": []
    }

    async def execute(self, network: str = "testnet", Limit: int = None, Skip: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Build request parameters
                request_params = {}

                # Add optional parameters if provided
                if Limit is not None:
                    request_params["Limit"] = Limit
                if Skip is not None:
                    request_params["Skip"] = Skip

                response = await provider._make_request("GetBlockInfoList", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                
                # # Extract and format the response
                # # API returns: {'result': [...], 'totalCount': ...}
                # if isinstance(result, dict) and "result" in result:
                #     blocks_list = result.get("result", [])
                #     total_count = result.get("totalCount", 0)
                    
                #     blocks_count = len(blocks_list) if isinstance(blocks_list, list) else 0
                    
                #     # Create informative output
                #     output = f"Retrieved {blocks_count} block(s)"
                    
                #     if Limit is not None:
                #         output += f" (requested: {Limit}"
                #         if total_count:
                #             output += f", out of {total_count} total blocks"
                #         output += ")"
                #     elif total_count:
                #         output += f" (out of {total_count} total blocks)"
                    
                #     output += ".\n\n"
                #     output += f"Block list: {blocks_list}"
                    
                #     return ToolResult(output=output)
                # else:
                #     # Fallback for unexpected response format
                return ToolResult(output=f"Recent blocks info: {result}")
                    
        except Exception as e:
                return ToolResult(error=str(e))

class GetBlockRewardByHashTool(BaseTool):
    name: str = "get_block_reward_by_hash"
    description: str = "Get block reward information by block hash on Neo blockchain. Useful when you need to analyze mining rewards or verify block reward distribution. Returns block reward information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "block_hash": {
                "type": "string",
                "description": "Block hash, must be a valid hexadecimal format"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["block_hash"]
    }

    async def execute(self, block_hash: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure BlockHash has 0x prefix
                if not block_hash.startswith("0x"):
                    normalized_hash = f"0x{block_hash}"
                else:
                    normalized_hash = block_hash
                
                response = await provider._make_request("GetBlockRewardByBlockHash", {"BlockHash": normalized_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Block reward info: {result}")
        except Exception as e:
                return ToolResult(error=str(e))