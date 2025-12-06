"""Solana toolkit constants，This module defines constants used throughout the Solana toolkit"""

# Service and Cache Configuration
SOLANA_SERVICE_NAME = "chain_solana"
SOLANA_WALLET_DATA_CACHE_KEY = "solana/walletData"
BIRDEYE_API_BASE_URL = "https://public-api.birdeye.so"

# Network Units
LAMPORTS_PER_SOL = 1_000_000_000

# Token Program IDs
TOKEN_PROGRAM_ID = None
TOKEN_2022_PROGRAM_ID = None
ASSOCIATED_TOKEN_PROGRAM_ID = None

## System Program ID
SYSTEM_PROGRAM_ID = None

# Metadata Program ID (Metaplex)
METADATA_PROGRAM_ID = None

TOKEN_ADDRESSES = {
    "SOL": None, 
    "USDC": None, 
    "USDT": None, 
    "BTC": None,  
    "ETH": None,   
}

# Native SOL placeholder address (used for swaps)
NATIVE_SOL_ADDRESS = None

# Transaction Configuration
DEFAULT_PRIORITY_FEE = 5  # micro-lamports per compute unit
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Slippage Configuration
DEFAULT_SLIPPAGE_BPS = 100  # 1%
MAX_SLIPPAGE_BPS = 3000     # 30%

# Cache Configuration
UPDATE_INTERVAL = 120  # seconds
CACHE_TTL = 300       # seconds

# Account Data Lengths
TOKEN_ACCOUNT_DATA_LENGTH = 165
TOKEN_MINT_DATA_LENGTH = 82

# Environment Variable Keys
ENV_KEYS = {
    "RPC_URL": ["SOLANA_RPC_URL", "RPC_URL"],
    "PRIVATE_KEY": ["SOLANA_PRIVATE_KEY", "WALLET_PRIVATE_KEY"],
    "PUBLIC_KEY": ["SOLANA_PUBLIC_KEY", "WALLET_PUBLIC_KEY"],
    "HELIUS_API_KEY": ["HELIUS_API_KEY"],
    "BIRDEYE_API_KEY": ["BIRDEYE_API_KEY"],
}

# Priority Levels for Jupiter
JUPITER_PRIORITY_LEVELS = {
    "low": 50,
    "medium": 200,
    "high": 1000,
    "veryHigh": 4_000_000,
}

JUPITER_API_BASE_URL = "https://quote-api.jup.ag/v6"
JUPITER_QUOTE_ENDPOINT = f"{JUPITER_API_BASE_URL}/quote"
JUPITER_SWAP_ENDPOINT = f"{JUPITER_API_BASE_URL}/swap"
