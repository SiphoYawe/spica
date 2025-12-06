"""EVM toolkit tools for SpoonAI

This package provides EVM-related tools aligned with plugin-evm capabilities:
- Native token transfer
- Token swap (via aggregators)
- Cross-chain bridge (via LiFi)
- Governance actions (propose, vote, queue, execute)

All tools follow the BaseTool interface and are designed for readability and robustness.

Unified signing support:
- Local private key signing via web3.py
- Secure Turnkey API signing for enhanced security
"""

from .transfer import EvmTransferTool
from .swap import EvmSwapTool
from .bridge import EvmBridgeTool
from .erc20 import EvmErc20TransferTool
from .balance import EvmBalanceTool
from .quote import EvmSwapQuoteTool
from .signers import EvmSigner, LocalSigner, TurnkeySigner, SignerManager, get_default_signer, set_default_signer

__all__ = [
    "EvmTransferTool",
    "EvmSwapTool",
    "EvmBridgeTool",
    "EvmErc20TransferTool",
    "EvmBalanceTool",
    "EvmSwapQuoteTool",
    # Signers
    "EvmSigner",
    "LocalSigner",
    "TurnkeySigner",
    "SignerManager",
    "get_default_signer",
    "set_default_signer",
]


