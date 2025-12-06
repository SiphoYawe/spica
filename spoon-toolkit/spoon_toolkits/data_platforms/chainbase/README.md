# Chainbase Tools

This module provides a set of tools based on the Chainbase API for interacting with blockchain networks.

## Environment Setup

Before using, you need to set up your Chainbase API key:

```bash
export CHAINBASE_API_KEY="your_api_key_here"
```

Or set it in your code:

```python
import os
os.environ["CHAINBASE_API_KEY"] = "your_api_key_here"
```

## Available Tools

### Basic Tools

- `GetLatestBlockNumberTool`: Get the latest block number of a blockchain network
- `GetBlockByNumberTool`: Get block details by block number
- `GetTransactionByHashTool`: Get transaction details by hash
- `GetAccountTransactionsTool`: Get transaction history for a specified address

### Account Tools

- `GetAccountBalanceTool`: Get the native token balance for a specified address
- `GetAccountTokensTool`: Get all ERC20 token balances for a specified address
- `GetAccountNFTsTool`: Get the list of NFTs owned by a specified address

### Contract Tools

- `ContractCallTool`: Call functions of a specified contract
- `GetTokenMetadataTool`: Get token metadata information

## Usage Examples

```python
from spoon_toolkits.chainbase import GetLatestBlockNumberTool, GetAccountBalanceTool

async def example():
    # Get the latest Ethereum block
    block_tool = GetLatestBlockNumberTool()
    block_result = await block_tool.execute(chain_id=1)
    print(f"Latest block: {block_result}")

    # Get account ETH balance
    balance_tool = GetAccountBalanceTool()
    balance_result = await balance_tool.execute(
        chain_id=1,
        address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth
    )
    print(f"Account balance: {balance_result}")

# Run example
import asyncio
asyncio.run(example())
```

## Supported Blockchain Networks

The tools support multiple blockchain networks, specified through the `chain_id` parameter:

- Ethereum: 1
- Polygon: 137
- BSC: 56
- Avalanche: 43114
- Arbitrum One: 42161
- Optimism: 10
- Base: 8453
- zkSync: 324
- Merlin: 4200

## Server Mode

You can start the FastMCP server in the following ways:

```bash
python -m spoon_toolkits.chainbase
```

Or in your code:

```python
from spoon_toolkits.chainbase import mcp_server

if __name__ == "__main__":
    mcp_server.run(
        transport="sse",
        host="0.0.0.0",
        port=8000,
        path="/sse"
    )
```
