"""Contract-related tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetContractCountTool(BaseTool):
    name: str = "get_contract_count"
    description: str = "Get total number of smart contracts on Neo blockchain. Useful when you need to understand the scale of smart contracts on the network or analyze contract deployment trends. Returns an integer representing the total contract count."
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
                response = await provider._make_request("GetContractCount", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Contract count: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetContractByHashTool(BaseTool):
    name: str = "get_contract_by_hash"
    description: str = "Get detailed contract information by contract hash on Neo blockchain. Useful when you need to verify contract details or analyze specific smart contract properties. Returns contract information."
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
            }
        },
        "required": ["contract_hash"]
    }

    async def execute(self, contract_hash: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure ContractHash has 0x prefix
                normalized_contract_hash = provider._ensure_0x_prefix(contract_hash)
                response = await provider._make_request("GetContractByContractHash", {"ContractHash": normalized_contract_hash})
                result =  provider._handle_response(response)
                return ToolResult(output=f"Contract info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetContractListByNameTool(BaseTool):
    name: str = "get_contract_list_by_name"
    description: str = "Get contract list by contract name with partial matching support on Neo blockchain. Useful when you need to find contracts by name or search for similar contracts. Returns contract list information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "contract_name": {
                "type": "string",
                "description": "Contract name, supports partial matching"
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
        "required": ["contract_name"]
    }

    async def execute(self, contract_name: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Build request parameters
                request_params = {"Name": contract_name}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetContractListByName", request_params)
                result = provider._handle_response(response)
                return ToolResult(output=f"Contract list: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetVerifiedContractByContractHashTool(BaseTool):
    name: str = "get_verified_contract_by_contract_hash"
    description: str = "Get verified contract information by contract hash on Neo blockchain. Useful when you need to verify contract authenticity or access verified contract details. Returns verified contract information."
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
            "UpdateCounter": {
                "type": "integer",
                "description": "update counts of a certain contract"
            },
        },
        "required": ["contract_hash"]
    }

    async def execute(self, contract_hash: str, network: str = "testnet", UpdateCounter: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure ContractHash has 0x prefix
                normalized_contract_hash = provider._ensure_0x_prefix(contract_hash)
                # Build request parameters
                request_params = {"ContractHash": normalized_contract_hash}

                # Add optional parameters if provided
                if UpdateCounter is not None:
                    request_params["UpdateCounter"] = UpdateCounter

                response = await provider._make_request("GetVerifiedContractByContractHash", request_params)
                result = provider._handle_response(response)
                return ToolResult(output=f"Verified contract info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetVerifiedContractTool(BaseTool):
    name: str = "get_verified_contract"
    description: str = "Get all verified contracts list on Neo blockchain. Useful when you need to find trusted contracts or analyze verified contract distribution. Returns verified contracts information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            },
            "Skip": {
                "type": "integer",
                "description": "the number of results to skip",
            },
            "Limit": {
                "type": "integer",
                "description": "the number of results to return",
            }
        },
        "required": []
    }

    async def execute(self, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Build request parameters
                request_params = {}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetVerifiedContracts", request_params)
                result = provider._handle_response(response)
                return ToolResult(output=f"Verified contracts: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

