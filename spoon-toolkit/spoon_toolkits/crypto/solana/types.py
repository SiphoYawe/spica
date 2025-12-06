from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass
class ParsedTokenAmount:
    amount: str
    decimals: int
    ui_amount: Optional[float]  
    ui_amount_string: Optional[str]


@dataclass
class ParsedTokenInfo:
    mint: str
    owner: str
    tokenAmount: ParsedTokenAmount

@dataclass
class ParsedData:
    parsed_info: ParsedTokenInfo    
    type: str 

@dataclass
class AccountData:
    parsed: ParsedData              
    program: str                    
    space: int                      

@dataclass
class Account:
    lamports: int
    data: AccountData               
    owner: str                      
    executable: bool
    rent_epoch: int

@dataclass
class TokenAccountInfo:
    pubkey: str                     # The public key associated with the token account.
    account: Account                # Information about the token account

class Item(BaseModel):
    #Represents a token item in wallet portfolio.
    name: str = Field(description="The name of the token")
    address: str = Field(description="The address of the item")
    symbol: str = Field(description="The symbol of the item")
    decimals: int = Field(description="The number of decimals for the item")
    balance: str = Field(description="The balance of the item")
    ui_amount: str = Field(description="The UI amount of the item")
    price_usd: str = Field(description="The price of the item in USD")
    value_usd: str = Field(description="The value of the item in USD")
    value_sol: Optional[str] = Field(default=None, description="Optional value of the item in SOL")


class Prices(BaseModel):
    #Price information for major cryptocurrencies.
    solana: Dict[str, str] = Field(description="Solana price info")
    bitcoin: Dict[str, str] = Field(description="Bitcoin price info")
    ethereum: Dict[str, str] = Field(description="Ethereum price info")


class WalletPortfolio(BaseModel):
    #Wallet portfolio information.
    total_usd: str = Field(description="The total value in USD")
    total_sol: Optional[str] = Field(default=None, description="The total value in SOL (optional)")
    items: List[Item] = Field(description="An array of items in the wallet portfolio")
    prices: Optional[Prices] = Field(default=None, description="Optional prices of the items")
    last_updated: Optional[int] = Field(default=None, description="Timestamp of when the portfolio was last updated (optional)")


class TransferContent(BaseModel):
    """Content for transfer operations."""
    token_address: Optional[str] = Field(default=None, description="Token mint address, null for SOL")
    recipient: str = Field(description="Recipient address")
    amount: Union[str, float] = Field(description="Amount to transfer")


class SwapContent(BaseModel):
    """Content for swap operations."""
    input_token_symbol: Optional[str] = Field(default=None, description="Input token symbol")
    output_token_symbol: Optional[str] = Field(default=None, description="Output token symbol")
    input_token_ca: Optional[str] = Field(default=None, description="Input token contract address")
    output_token_ca: Optional[str] = Field(default=None, description="Output token contract address")
    amount: float = Field(gt=0, description="Amount to swap (must be positive)")


class KeypairResult(BaseModel):

    keypair: Optional[Any] = Field(default=None, description="Solana keypair object")
    public_key: Optional[Any] = Field(default=None, description="Public key (string or Pubkey object)")


class TokenMetadata(BaseModel):

    name: str = Field(description="Token name")
    symbol: str = Field(description="Token symbol")
    decimals: int = Field(description="Token decimals")
    supply: Optional[int] = Field(default=None, description="Total supply")
    description: Optional[str] = Field(default=None, description="Token description")
    image: Optional[str] = Field(default=None, description="Token image URL")


class TransactionResult(BaseModel):

    success: bool = Field(description="Whether transaction succeeded")
    signature: Optional[str] = Field(default=None, description="Transaction signature")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    fees: Optional[Dict[str, Any]] = Field(default=None, description="Transaction fees")


class SwapResult(BaseModel):

    success: bool = Field(description="Whether swap succeeded")
    signature: Optional[str] = Field(default=None, description="Transaction signature")
    input_amount: Optional[str] = Field(default=None, description="Input amount")
    output_amount: Optional[str] = Field(default=None, description="Output amount received")
    price_impact: Optional[float] = Field(default=None, description="Price impact percentage")
    fees: Optional[Dict[str, Any]] = Field(default=None, description="Transaction fees")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class JupiterQuoteResponse(BaseModel):

    input_mint: str = Field(description="Input token mint")
    in_amount: str = Field(description="Input amount")
    output_mint: str = Field(description="Output token mint")
    out_amount: str = Field(description="Output amount")
    other_amount_threshold: str = Field(description="Minimum output after slippage")
    swap_mode: str = Field(description="Swap mode")
    slippage_bps: int = Field(description="Slippage in basis points")
    platform_fee: Optional[Dict[str, Any]] = Field(default=None, description="Platform fees")
    price_impact_pct: str = Field(description="Price impact percentage")
    route_plan: List[Dict[str, Any]] = Field(description="Route plan")
    context_slot: int = Field(description="Context slot")
    time_taken: float = Field(description="Time taken for quote")


class JupiterSwapResponse(BaseModel):
   
    swap_transaction: str = Field(description="Base64 encoded transaction")
    last_valid_block_height: int = Field(description="Last valid block height")


class BalanceInfo(BaseModel):
    
    address: str = Field(description="Wallet address")
    sol_balance: float = Field(description="SOL balance")
    token_balances: List[Dict[str, Any]] = Field(description="SPL token balances")
    total_value_usd: Optional[float] = Field(default=None, description="Total value in USD")


class WalletInfo(BaseModel):
    
    public_key: str = Field(description="Wallet public key")
    private_key: Optional[str] = Field(default=None, description="Wallet private key")
    mnemonic: Optional[str] = Field(default=None, description="Wallet mnemonic")


class NetworkInfo(BaseModel):
   
    rpc_url: str = Field(description="RPC endpoint URL")
    network: str = Field(description="Network name (mainnet/devnet/testnet)")
    cluster: str = Field(description="Cluster identifier")


class ServiceConfig(BaseModel):
   
    rpc_url: str = Field(description="RPC endpoint")
    helius_api_key: Optional[str] = Field(default=None, description="Helius API key")
    birdeye_api_key: Optional[str] = Field(default=None, description="Birdeye API key")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    update_interval: int = Field(default=120, description="Update interval in seconds")


Address = str
Signature = str
Lamports = int
TokenMint = str