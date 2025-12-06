"""Address-related tools for Neo blockchain"""

from spoon_ai.tools.base import BaseTool, ToolResult
from .base import get_provider

class GetAddressCountTool(BaseTool):
    name: str = "get_address_count"
    description: str = "Get total number of addresses on Neo blockchain. Useful when you need to understand network scale or analyze Neo blockchain adoption. Returns an integer representing the total address count."
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
                response = await provider._make_request("GetAddressCount", {})
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                result = provider._handle_response(response)
                return ToolResult(output=f"Address count: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetAddressInfoTool(BaseTool):
    name: str = "get_address_info"
    description: str = "Get detailed address information on Neo blockchain. Useful when you need to analyze address activity or verify address details. Returns a JSON object with keys: address, firstusetime, lastusetime, transactionssent."
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
                result = await provider.get_address_info(address)
                return ToolResult(output=f"Address info: {result}")
        except Exception as e:
            return ToolResult(error=str(e))


class ValidateAddressTool(BaseTool):
    name: str = "validate_address"
    description: str = "Validate a Neo address using the RPC `validateaddress` method. Useful for confirming address ownership metadata or script hash conversion details. Returns the RPC validation payload."
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
                result = await provider.validate_address(address)
                return ToolResult(output=f"Validation result: {result}")
        except Exception as e:
            return ToolResult(error=str(e))



class GetActiveAddressesTool(BaseTool):
    name: str = "get_active_addresses"
    description: str = "Get active address counts for specified days on Neo blockchain. Useful when you need to analyze network activity patterns or understand network participation trends. Returns a list of daily active address counts."
    parameters: dict = {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to query for active addresses",
                "minimum": 1,
                "maximum": 365
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["days"]
    }

    async def execute(self, days: int, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                result = await provider.get_active_addresses(days)
                
                # Format output with clear information
                if not result:
                    return ToolResult(output=f"No active addresses data available for {days} days on {network}")
                
                # Format the result list
                if isinstance(result, list):
                    result_count = len(result)
                    output = f"Retrieved active address counts for {days} days on {network}.\n"
                    output += f"Total data points: {result_count}\n"
                    output += f"Daily active address counts: {result}"
                    return ToolResult(output=output)
                else:
                    return ToolResult(output=f"Active addresses data: {result}")
        except ValueError as e:
            return ToolResult(error=f"Invalid parameter: {str(e)}")
        except Exception as e:
            return ToolResult(error=str(e))


class GetTotalSentAndReceivedTool(BaseTool):
    name: str = "get_total_sent_and_received"
    description: str = "Get total sent and received amounts for a specific token contract and address on Neo blockchain. Useful when you need to analyze token transaction patterns or calculate total volume for a specific token. Returns a JSON object with keys: Address, ContractHash, received, sent."
    parameters: dict = {
        "type": "object",
        "properties": {
            "contract_hash": {
                "type": "string",
                "description": "Contract hash, must be a valid Neo contract hash format"
            },
            "address": {
                "type": "string",
                "description": "Neo address, must be a valid Neo address format"
            },
            "network": {
                "type": "string",
                "description": "Neo network type, must be 'mainnet' or 'testnet'",
                "enum": ["mainnet", "testnet"],
                "default": "testnet"
            }
        },
        "required": ["contract_hash", "address"]
    }

    async def execute(self, contract_hash: str, address: str, network: str = "testnet") -> ToolResult:
        try:
            async with get_provider(network) as provider:
                # Normalize address to Base58 format and get script hash for comparison
                normalized_address, script_hash = provider._normalize_address(address)
                target_script_hash = str(script_hash).lower().replace("0x", "")
                
                # Normalize contract hash for comparison (remove 0x prefix, lowercase)
                normalized_contract_hash = contract_hash.lower().replace("0x", "")

                # Use GetNep17TransferByAddress API to get transfer history
                # Try both Base58 address and script hash format to ensure compatibility
                # Some APIs may prefer script hash format
                request_params_base58 = {"Address": normalized_address}
                request_params_script_hash = {"Address": f"0x{target_script_hash}"}
                
                # First try with Base58 address
                result = await provider._make_request("GetNep17TransferByAddress", request_params_base58)
                
                # Check if result is empty - extract transfers list first to check
                transfers_list_temp = []
                if isinstance(result, dict):
                    if "result" in result and isinstance(result["result"], dict) and "result" in result["result"]:
                        transfers_list_temp = result["result"].get("result", [])
                    elif "result" in result:
                        transfers_list_temp = result.get("result", [])
                elif isinstance(result, list):
                    transfers_list_temp = result
                
                # If no transfers found with Base58, try with script hash format
                if len(transfers_list_temp) == 0 and not isinstance(result, str):
                    result_script_hash = await provider._make_request("GetNep17TransferByAddress", request_params_script_hash)
                    # Only use script hash result if it's not an error and has data
                    if not isinstance(result_script_hash, str) and result_script_hash is not None:
                        # Check if script hash result has transfers
                        transfers_list_temp2 = []
                        if isinstance(result_script_hash, dict):
                            if "result" in result_script_hash and isinstance(result_script_hash["result"], dict) and "result" in result_script_hash["result"]:
                                transfers_list_temp2 = result_script_hash["result"].get("result", [])
                            elif "result" in result_script_hash:
                                transfers_list_temp2 = result_script_hash.get("result", [])
                        elif isinstance(result_script_hash, list):
                            transfers_list_temp2 = result_script_hash
                        
                        if len(transfers_list_temp2) > 0:
                            result = result_script_hash
                
                # Handle error response (string indicates error)
                if isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower()):
                    return ToolResult(error=f"GetNep17TransferByAddress API error: {result}")

                # Calculate totals from transfer history
                sent_total = 0
                received_total = 0

                # API response format: {"result": [...], "totalCount": <number>}
                # _make_request already extracts the "result" field from JSON-RPC response
                transfers_list = []
                if isinstance(result, dict):
                    # Check if result has nested "result" field (double nesting)
                    if "result" in result and isinstance(result["result"], dict) and "result" in result["result"]:
                        transfers_list = result["result"].get("result", [])
                    # Check if result has direct "result" field
                    elif "result" in result:
                        transfers_list = result.get("result", [])
                    # If result itself is a dict but no "result" key, check if it's a list-like structure
                    elif isinstance(result, dict) and not any(k in result for k in ["result", "totalCount"]):
                        # Might be a list of transfers wrapped in a dict with other keys
                        # Try to find list values
                        for key, value in result.items():
                            if isinstance(value, list):
                                transfers_list = value
                                break
                elif isinstance(result, list):
                    transfers_list = result
                
                # Debug: Add raw response info if no transfers found
                debug_info = ""
                if len(transfers_list) == 0:
                    debug_info = f"\n\n  Debug Information:"
                    debug_info += f"\n  - Raw API response type: {type(result).__name__}"
                    debug_info += f"\n  - Address used (Base58): {normalized_address}"
                    debug_info += f"\n  - Address used (Script Hash): 0x{target_script_hash}"
                    debug_info += f"\n  - Contract hash: {contract_hash}"
                    debug_info += f"\n  - Normalized contract hash: {normalized_contract_hash}"
                    if isinstance(result, dict):
                        debug_info += f"\n  - Response keys: {list(result.keys())}"
                        debug_info += f"\n  - Response structure: {str(result)[:300]}"
                    elif isinstance(result, list):
                        debug_info += f"\n  - Response is a list with {len(result)} items"
                        if len(result) > 0:
                            debug_info += f"\n  - First item: {str(result[0])[:200]}"
                    elif result is None:
                        debug_info += f"\n  - Response is None (API may have returned empty/null)"
                    else:
                        debug_info += f"\n  - Response value: {str(result)[:300]}"

                # Process each transfer
                matching_transfers = 0
                for transfer in transfers_list:
                    if not isinstance(transfer, dict):
                        continue
                    
                    # Get contract hash from transfer (may be in different formats)
                    # Try multiple possible field names
                    transfer_contract = (
                        transfer.get("contract") or 
                        transfer.get("ContractHash") or 
                        transfer.get("contractHash") or
                        transfer.get("Contract") or
                        transfer.get("asset") or
                        transfer.get("Asset")
                    )
                    if not transfer_contract:
                        continue
                    
                    # Normalize transfer contract hash for comparison
                    normalized_transfer_contract = str(transfer_contract).lower().replace("0x", "")
                    
                    # Check if this transfer matches the requested contract
                    if normalized_transfer_contract != normalized_contract_hash:
                        continue
                    
                    matching_transfers += 1
                    
                    # Get amount (may be in different field names)
                    amount = (
                        transfer.get("amount") or 
                        transfer.get("Amount") or 
                        transfer.get("value") or 
                        transfer.get("Value") or
                        transfer.get("quantity") or
                        transfer.get("Quantity") or
                        0
                    )
                    
                    # Get from/to addresses (try multiple field name formats)
                    from_addr = (
                        transfer.get("from") or 
                        transfer.get("From") or 
                        transfer.get("fromAddress") or
                        transfer.get("FromAddress") or
                        transfer.get("sender") or
                        transfer.get("Sender") or
                        ""
                    )
                    to_addr = (
                        transfer.get("to") or 
                        transfer.get("To") or 
                        transfer.get("toAddress") or
                        transfer.get("ToAddress") or
                        transfer.get("receiver") or
                        transfer.get("Receiver") or
                        ""
                    )
                    
                    # Normalize addresses for comparison - convert to script hash for accurate comparison
                    # API may return addresses in Base58 or script hash format
                    from_script_hash = None
                    to_script_hash = None
                    
                    if from_addr and str(from_addr).strip():
                        try:
                            _, from_sh = provider._normalize_address(str(from_addr).strip())
                            from_script_hash = str(from_sh).lower().replace("0x", "")
                        except Exception as e:
                            # Fallback: try direct comparison if normalization fails
                            # This handles cases where the address might already be in script hash format
                            from_str = str(from_addr).strip().lower().replace("0x", "")
                            # If it looks like a script hash (hex string), use it directly
                            if len(from_str) == 40 and all(c in '0123456789abcdef' for c in from_str):
                                from_script_hash = from_str
                            # Otherwise, try to normalize the target address to Base58 and compare
                            elif from_str == normalized_address.lower():
                                from_script_hash = target_script_hash
                    
                    if to_addr and str(to_addr).strip():
                        try:
                            _, to_sh = provider._normalize_address(str(to_addr).strip())
                            to_script_hash = str(to_sh).lower().replace("0x", "")
                        except Exception as e:
                            # Fallback: try direct comparison if normalization fails
                            # This handles cases where the address might already be in script hash format
                            to_str = str(to_addr).strip().lower().replace("0x", "")
                            # If it looks like a script hash (hex string), use it directly
                            if len(to_str) == 40 and all(c in '0123456789abcdef' for c in to_str):
                                to_script_hash = to_str
                            # Otherwise, try to normalize the target address to Base58 and compare
                            elif to_str == normalized_address.lower():
                                to_script_hash = target_script_hash
                    
                    # Calculate sent (address is sender)
                    if from_script_hash and from_script_hash == target_script_hash:
                        try:
                            amount_value = int(amount) if isinstance(amount, (int, str)) else 0
                            sent_total += amount_value
                        except (ValueError, TypeError):
                            pass
                    
                    # Calculate received (address is receiver)
                    if to_script_hash and to_script_hash == target_script_hash:
                        try:
                            amount_value = int(amount) if isinstance(amount, (int, str)) else 0
                            received_total += amount_value
                        except (ValueError, TypeError):
                            pass

                # Format output with detailed information
                output = f"Total sent and received for address {address} and contract {contract_hash}:\n"
                output += f"  Sent: {sent_total}\n"
                output += f"  Received: {received_total}\n"
                output += f"  Total transfers found: {len(transfers_list)}\n"
                output += f"  Matching contract transfers: {matching_transfers}\n"
                output += f"  Target address (normalized): {normalized_address}\n"
                output += f"  Target script hash: {target_script_hash}\n"
                output += f"  Contract hash (normalized): {normalized_contract_hash}"
                
                # Add debug info
                output += debug_info
                
                # Add debug info if no matching transfers found but transfers exist
                if matching_transfers == 0 and len(transfers_list) > 0:
                    output += f"\n\n  Debug: Found {len(transfers_list)} transfers but none matched contract {contract_hash}"
                    output += f"\n  Debug: Normalized contract hash: {normalized_contract_hash}"
                    # Show first few transfer contracts for debugging
                    sample_contracts = []
                    for i, t in enumerate(transfers_list[:3]):
                        if isinstance(t, dict):
                            tc = (
                                t.get("contract") or 
                                t.get("ContractHash") or 
                                t.get("contractHash") or
                                t.get("Contract") or
                                t.get("asset") or
                                t.get("Asset") or
                                "N/A"
                            )
                            sample_contracts.append(f"Transfer {i+1}: {tc}")
                    if sample_contracts:
                        output += f"\n  Debug: Sample transfer contracts: {', '.join(sample_contracts)}"
                
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Failed to get total sent and received: {str(e)}")

class GetTransferByAddressTool(BaseTool):
    name: str = "get_transfer_by_address"
    description: str = "Get transfer records by address on Neo blockchain. Useful when you need to track asset transfers or analyze transfer patterns for a specific address. Supports pagination with Skip and Limit parameters to avoid timeout. Returns transfer data."
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
                
                # Use GetNep17TransferByAddress RPC API which supports pagination and returns more complete data
                response = await provider._make_request("GetNep17TransferByAddress", request_params)
                
                # Check if response is an error string
                if isinstance(response, str) and ("error" in response.lower() or "failed" in response.lower() or "unexpected" in response.lower() or "timeout" in response.lower()):
                    return ToolResult(error=response)
                
                result = provider._handle_response(response)
                return ToolResult(output=f"Transfer data: {result}")
        except Exception as e:
            return ToolResult(error=str(e))

