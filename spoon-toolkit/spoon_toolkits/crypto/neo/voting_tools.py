"""Voting-related tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetCandidateCountTool(BaseTool):
    name: str = "get_candidate_count"
    description: str = "Get total number of candidates in Neo network. Useful when you need to understand the scale of consensus participation or analyze governance structure. Returns an integer representing the total candidate count."
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
                response = await provider._make_request("GetCandidateCount", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Candidate count: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetCandidateByAddressTool(BaseTool):
    name: str = "get_candidate_by_address"
    description: str = "Get detailed candidate information by address on Neo blockchain. Useful when you need to verify candidate status or analyze specific candidate information. Returns candidate information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Candidate address in script hash format (e.g., 0xaa606e99a6d1cb45ba34872864a3578c8a668143) or standard format. This is a required parameter."
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
                # Convert address to script hash format
                address_script_hash = provider._address_to_script_hash(address)
                # Address is required parameter for GetCandidateByAddress API
                response = await provider._make_request("GetCandidateByAddress", {"Address": address_script_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Candidate info: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetCandidateByVoterAddressTool(BaseTool):
    name: str = "get_candidate_by_voter_address"
    description: str = "Get candidate information by voter address on Neo blockchain. Useful when you need to track voting relationships or analyze voter-candidate connections. Returns candidate information for the voter."
    parameters: dict = {
        "type": "object",
        "properties": {
            "voter_address": {
                "type": "string",
                "description": "Voter address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
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
        "required": ["voter_address"]
    }

    async def execute(self, voter_address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert Base58 address to script hash format if needed
                if voter_address.startswith("0x"):
                    # Already in script hash format
                    voter_address_script_hash = voter_address
                else:
                    # Convert Base58 address to script hash format
                    _, script_hash = provider._normalize_address(voter_address)
                    voter_address_script_hash = f"0x{str(script_hash).replace('0x', '')}"
                request_params = {"VoterAddress": voter_address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetCandidateByVoterAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Candidate info: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetScVoteCallByCandidateAddressTool(BaseTool):
    name: str = "get_sc_vote_call_by_candidate_address"
    description: str = "Get vote call records by candidate address on Neo blockchain. Useful when you need to analyze voting activity for a specific candidate or track vote calls. Returns vote call information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "candidate_address": {
                "type": "string",
                "description": "Candidate address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
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
        "required": ["candidate_address"]
    }

    async def execute(self, candidate_address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                candidate_address_script_hash = provider._address_to_script_hash(candidate_address)
                request_params = {"CandidateAddress": candidate_address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetScVoteCallByCandidateAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Vote calls: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetScVoteCallByTransactionHashTool(BaseTool):
    name: str = "get_sc_vote_call_by_transaction_hash"
    description: str = "Get vote call details by transaction hash on Neo blockchain. Useful when you need to analyze specific voting transactions or verify vote call details. Returns vote call details."
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
            }
        },
        "required": ["transaction_hash"]
    }

    async def execute(self, transaction_hash: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Ensure transaction hash has 0x prefix
                normalized_hash = provider._ensure_0x_prefix(transaction_hash)
                response = await provider._make_request("GetScVoteCallByTransactionHash", {"TransactionHash": normalized_hash})
                result = provider._handle_response(response)
                return ToolResult(output=f"Vote calls: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetScVoteCallByVoterAddressTool(BaseTool):
    name: str = "get_sc_vote_call_by_voter_address"
    description: str = "Get vote call records by voter address on Neo blockchain. Useful when you need to track voting history or analyze voting patterns for a specific voter. Returns vote call records."
    parameters: dict = {
        "type": "object",
        "properties": {
            "voter_address": {
                "type": "string",
                "description": "Voter address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
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
        "required": ["voter_address"]
    }

    async def execute(self, voter_address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert Base58 address to script hash format if needed
                if voter_address.startswith("0x"):
                    # Already in script hash format
                    voter_address_script_hash = voter_address
                else:
                    # Convert Base58 address to script hash format
                    _, script_hash = provider._normalize_address(voter_address)
                    voter_address_script_hash = f"0x{str(script_hash).replace('0x', '')}"
                request_params = {"VoterAddress": voter_address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetScVoteCallByVoterAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Vote calls: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetVotersByCandidateAddressTool(BaseTool):
    name: str = "get_voters_by_candidate_address"
    description: str = "Get voters list by candidate address on Neo blockchain. Useful when you need to analyze candidate support or track voter distribution for a specific candidate. Returns voters information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "candidate_address": {
                "type": "string",
                "description": "Candidate address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
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
        "required": ["candidate_address"]
    }

    async def execute(self, candidate_address: str, network: str = "testnet", Skip: int = None, Limit: int = None) -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                candidate_address_script_hash = provider._address_to_script_hash(candidate_address)
                request_params = {"CandidateAddress": candidate_address_script_hash}

                # Add optional parameters if provided
                if Skip is not None:
                    request_params["Skip"] = Skip
                if Limit is not None:
                    request_params["Limit"] = Limit

                response = await provider._make_request("GetVotersByCandidateAddress", request_params)
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Voters: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetVotesByCandidateAddressTool(BaseTool):
    name: str = "get_votes_by_candidate_address"
    description: str = "Get detailed voting information by candidate address on Neo blockchain. Useful when you need to analyze voting statistics or track vote distribution for a specific candidate. Returns voting information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "candidate_address": {
                "type": "string",
                "description": "Candidate address, supports standard format and script hash format (e.g., NiEtVMWVYgpXrWkRTMwRaMJtJ41gD3912N, 0xaad8073e6df9caaf6abc0749250eb0b800c0e6f4)"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["candidate_address"]
    }

    async def execute(self, candidate_address: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Convert address to script hash format
                candidate_address_script_hash = provider._address_to_script_hash(candidate_address)
                response = await provider._make_request("GetVotesByCandidateAddress", {"CandidateAddress": candidate_address_script_hash})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Votes: {result}")
        except Exception as e:
                return ToolResult(error=str(e))

class GetTotalVotesTool(BaseTool):
    name: str = "get_total_votes"
    description: str = "Get total number of votes in Neo network. Useful when you need to understand overall voting participation or analyze governance engagement. Returns an integer representing the total vote count."
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
                response = await provider._make_request("GetTotalVotes", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Total votes: {result}")
        except Exception as e:
                return ToolResult(error=str(e)) 