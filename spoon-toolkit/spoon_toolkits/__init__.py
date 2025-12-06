# Spoon Toolkits - Comprehensive blockchain and cryptocurrency tools
__version__ = "0.1.0"

from .crypto.crypto_data_tools.predict_price import PredictPrice
from .crypto.crypto_data_tools.token_holders import TokenHolders
from .crypto.crypto_data_tools.trading_history import TradingHistory
from .crypto.crypto_data_tools.uniswap_liquidity import UniswapLiquidity
from .crypto.crypto_data_tools.wallet_analysis import WalletAnalysis
from .crypto.crypto_data_tools.price_data import GetTokenPriceTool, Get24hStatsTool, GetKlineDataTool
from .crypto.crypto_data_tools.price_alerts import PriceThresholdAlertTool, LpRangeCheckTool, SuddenPriceIncreaseTool
from .crypto.crypto_data_tools.lending_rates import LendingRateMonitorTool

from .crypto.crypto_powerdata import (
    CryptoPowerDataCEXTool,
    CryptoPowerDataDEXTool,
    CryptoPowerDataIndicatorsTool,
    CryptoPowerDataPriceTool,
    start_crypto_powerdata_mcp_stdio,
    start_crypto_powerdata_mcp_sse,
    start_crypto_powerdata_mcp_auto,
    CryptoPowerDataMCPServer,
    get_server_manager,
)

from .data_platforms.third_web.third_web_tools import (
    GetContractEventsFromThirdwebInsight,
    GetMultichainTransfersFromThirdwebInsight,
    GetTransactionsTool,
    GetContractTransactionsTool,
    GetContractTransactionsBySignatureTool,
    GetBlocksFromThirdwebInsight,
    GetWalletTransactionsFromThirdwebInsight
)

from .data_platforms.desearch.ai_search_official import search_ai_data, search_social_media, search_academic
from .data_platforms.desearch.builtin_tools import (
    DesearchAISearchTool,
    DesearchWebSearchTool,
    DesearchAcademicSearchTool,
    DesearchTwitterSearchTool
)

from .crypto.neo import (
    # Address tools (6)
    GetAddressCountTool,
    GetAddressInfoTool,
    ValidateAddressTool,
    GetActiveAddressesTool,
    GetTotalSentAndReceivedTool,
    GetTransferByAddressTool,

    # Asset tools (5)
    GetAssetCountTool,
    GetAssetInfoByHashTool,
    GetAssetInfoByNameTool,
    GetAssetInfosTool,
    GetAssetInfoByAssetAndAddressTool,

    # Block tools (6)
    GetBlockCountTool,
    GetBlockByHashTool,
    GetBlockByHeightTool,
    GetBestBlockHashTool,
    GetRecentBlocksInfoTool,
    GetBlockRewardByHashTool,

    # Contract tools (5)
    GetContractCountTool,
    GetContractByHashTool,
    GetContractListByNameTool,
    GetVerifiedContractByContractHashTool,
    GetVerifiedContractTool,

    # Transaction tools (9)
    GetTransactionCountTool,
    GetTransactionCountByAddressTool,
    GetRawTransactionByBlockHashTool,
    GetRawTransactionByBlockHeightTool,
    GetRawTransactionByTransactionHashTool,
    GetTransferByBlockHashTool,
    GetTransferByBlockHeightTool,
    GetTransferEventByTransactionHashTool,

    # Voting tools (9)
    GetCandidateCountTool,
    GetCandidateByAddressTool,
    GetCandidateByVoterAddressTool,
    GetScVoteCallByCandidateAddressTool,
    GetScVoteCallByTransactionHashTool,
    GetScVoteCallByVoterAddressTool,
    GetVotersByCandidateAddressTool,
    GetVotesByCandidateAddressTool,
    GetTotalVotesTool,

    # NEP tools (11)
    GetNep11BalanceTool,
    GetNep11ByAddressAndHashTool,
    GetNep11TransferByAddressTool,
    GetNep11TransferByBlockHeightTool,
    GetNep11TransferByTransactionHashTool,
    GetNep11TransferCountByAddressTool,
    GetNep17TransferByAddressTool,
    GetNep17TransferByBlockHeightTool,
    GetNep17TransferByContractHashTool,
    GetNep17TransferByTransactionHashTool,
    GetNep17TransferCountByAddressTool,

    # Smart Contract Call tools (3)
    GetScCallByContractHashTool,
    GetScCallByContractHashAddressTool,
    GetScCallByTransactionHashTool,

    # Application Log and State tools (2)
    GetApplicationLogTool,
    GetApplicationStateTool,

    # Governance tools (1)
    GetCommitteeInfoTool,

    # Provider
    NeoProvider,
    get_provider,
)

# EVM tools
from .crypto.evm import (
    EvmTransferTool,
    EvmSwapTool,
    EvmBridgeTool,
    EvmErc20TransferTool,
    EvmBalanceTool,
    EvmSwapQuoteTool,
)

from .memory.mem0_tools import (
    AddMemoryTool,
    SearchMemoryTool,
    GetAllMemoryTool,
    UpdateMemoryTool,
    DeleteMemoryTool,
)
from .web import WebScraperTool



__all__ = [
    "PredictPrice",
    "TokenHolders",
    "TradingHistory",
    "UniswapLiquidity",
    "WalletAnalysis",
    "GetTokenPriceTool",
    "Get24hStatsTool",
    "GetKlineDataTool",
    "PriceThresholdAlertTool",
    "LpRangeCheckTool",
    "SuddenPriceIncreaseTool",
    "LendingRateMonitorTool",

    "GetContractEventsFromThirdwebInsight",
    "GetMultichainTransfersFromThirdwebInsight",
    "GetTransactionsTool",
    "GetContractTransactionsTool",
    "GetContractTransactionsBySignatureTool",
    "GetBlocksFromThirdwebInsight",
    "GetWalletTransactionsFromThirdwebInsight",

    # Crypto PowerData tools
    "CryptoPowerDataCEXTool",
    "CryptoPowerDataDEXTool",
    "CryptoPowerDataIndicatorsTool",
    "CryptoPowerDataPriceTool",
    "start_crypto_powerdata_mcp_stdio",
    "start_crypto_powerdata_mcp_sse",
    "start_crypto_powerdata_mcp_auto",
    "CryptoPowerDataMCPServer",
    "get_server_manager",

    # Desearch AI tools
    "search_ai_data",
    "search_social_media",
    "search_academic",

    # Desearch Builtin Tools
    "DesearchAISearchTool",
    "DesearchWebSearchTool",
    "DesearchAcademicSearchTool",
    "DesearchTwitterSearchTool",

    # Neo Address tools (6)
    "GetAddressCountTool",
    "GetAddressInfoTool",
    "ValidateAddressTool",
    "GetActiveAddressesTool",
    "GetTotalSentAndReceivedTool",
    "GetTransferByAddressTool",

    # Neo Asset tools (5)
    "GetAssetCountTool",
    "GetAssetInfoByHashTool",
    "GetAssetInfoByNameTool",
    "GetAssetInfosTool",
    "GetAssetInfoByAssetAndAddressTool",

    # Neo Block tools (6)
    "GetBlockCountTool",
    "GetBlockByHashTool",
    "GetBlockByHeightTool",
    "GetBestBlockHashTool",
    "GetRecentBlocksInfoTool",
    "GetBlockRewardByHashTool",

    # Neo Contract tools (6)
    "GetContractCountTool",
    "GetContractByHashTool",
    "GetContractListByNameTool",
    "GetVerifiedContractByContractHashTool",
    "GetVerifiedContractTool",
    "GetSourceCodeByContractHashTool",

    # Neo Transaction tools (9)
    "GetTransactionCountTool",
    "GetTransactionCountByAddressTool",
    "GetRawTransactionByBlockHashTool",
    "GetRawTransactionByBlockHeightTool",
    "GetRawTransactionByTransactionHashTool",
    "GetRawTransactionByAddressTool",
    "GetTransferByBlockHashTool",
    "GetTransferByBlockHeightTool",
    "GetTransferEventByTransactionHashTool",

    # Neo Voting tools (9)
    "GetCandidateCountTool",
    "GetCandidateByAddressTool",
    "GetCandidateByVoterAddressTool",
    "GetScVoteCallByCandidateAddressTool",
    "GetScVoteCallByTransactionHashTool",
    "GetScVoteCallByVoterAddressTool",
    "GetVotersByCandidateAddressTool",
    "GetVotesByCandidateAddressTool",
    "GetTotalVotesTool",

    # Neo NEP tools (11)
    "GetNep11BalanceTool",
    "GetNep11ByAddressAndHashTool",
    "GetNep11TransferByAddressTool",
    "GetNep11TransferByBlockHeightTool",
    "GetNep11TransferByTransactionHashTool",
    "GetNep11TransferCountByAddressTool",
    "GetNep17TransferByAddressTool",
    "GetNep17TransferByBlockHeightTool",
    "GetNep17TransferByContractHashTool",
    "GetNep17TransferByTransactionHashTool",
    "GetNep17TransferCountByAddressTool",

    # Neo Smart Contract Call tools (2)
    "InvokeContractTool",
    "TestInvokeContractTool",

    # Neo Application Log and State tools (2)
    "GetApplicationLogTool",
    "GetApplicationStateTool",

    # Neo Statistics and Monitoring tools (4)
    "GetNetworkStatisticsTool",
    "GetTransactionStatisticsTool",
    "GetAddressStatisticsTool",
    "GetContractStatisticsTool",

    # Neo Governance tools (1)
    "GetCommitteeInfoTool",

    # Neo Utility tools (3)
    "ValidateAddressTool",
    "ConvertAddressTool",
    "GetNetworkInfoTool",

    # Neo Provider
    "NeoProvider",
    "get_provider",

    # EVM Tools
    "EvmTransferTool",
    "EvmSwapTool",
    "EvmBridgeTool",
    "EvmErc20TransferTool",
    "EvmBalanceTool",
    "EvmSwapQuoteTool",

    # Memory tools
    "AddMemoryTool",
    "SearchMemoryTool",
    "GetAllMemoryTool",
    "UpdateMemoryTool",
    "DeleteMemoryTool",

    # Web tools
    "WebScraperTool",
]
