"""
Solana Toolkit Agent Demo - Comprehensive Agent-Based Demonstration

This example demonstrates Solana blockchain tools using spoon_ai agents, showcasing:
- Agent-based tool interaction with 4 specialist agents
- 3 core demonstration scenarios covering major Solana operations
- Real-world usage patterns with LLM-powered analysis
- Devnet integration with actual wallet data

Total scenarios: 4
Network: Devnet
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.tools import ToolManager
from spoon_ai.chat import ChatBot
from spoon_ai.llm.manager import get_llm_manager
from spoon_ai.schema import Message
from pydantic import Field

# Import Solana tools
from spoon_toolkits.crypto.solana import (
    SolanaWalletInfoTool,
    SolanaTransferTool,
    SolanaSwapTool,
    SolanaService,
    get_rpc_url,
)

load_dotenv()

class SolanaToolkitDemo:
    """Solana Toolkit Agent-based comprehensive demonstration"""

    TEST_DATA = {
        "network": "devnet",
        "rpc_url": "https://api.devnet.solana.com",
        "wallet_addresses": {
            "wallet_1": "BJyWLDo4xYDs2bp2dK2BcMFBJuRxnUBcJkNqjxgg81hR",  # Generated wallet (has private key)
            "wallet_2": "GMkCtcMmLTQ3jwxExRvSqCE5u4ypFYNa6TxVMZ9smuud",
            "wallet_3": "5ZZKpFcZDqJtgFH1Vq8WXCP8QJnwhtXV7CEe1JnjkADZ",
        },
        "wallet_info": {
            "wallet_1": {"balance_sol": 3.5, "description": "Primary test wallet"},
            "wallet_2": {"balance_sol": 2.5, "description": "Secondary test wallet"},
            "wallet_3": {"balance_sol": 0.0, "description": "Third test wallet"},
        },
        "devnet_tokens": {
            # Devnet address
            "USDC": {
                "mint": "4zMMC9srt5Ri5X14GAgupooMv52GivLm5dge1twNQXJH",
                "symbol": "USDC",
                "decimals": 6,
                "network": "devnet",
            },
            "USDT": {
                "mint": "BWSQFkBUx4nMCMXvUAaoKoXXn8FA5NqXDhcNqFtz93mD",
                "symbol": "USDT",
                "decimals": 6,
                "network": "devnet",
            },
            "SOL": {
                "mint": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "decimals": 9,
                "network": "devnet",
            },
        },
        "invalid_addresses": [
            "invalid_address_format",
            "11111111111111111111111111111111",
        ],
    }

    def __init__(self):
        """Initialize the demo with embedded test data"""
        self.load_test_data()
        self.agents = {}
        self.demo_results: List[Dict[str, Any]] = []

    def load_test_data(self):
        """Load test data from embedded TEST_DATA configuration"""
        try:
            data = self.TEST_DATA
            self.network = data.get("network", "devnet")
            self.rpc_url = data.get("rpc_url", get_rpc_url())
            self.demo_address = data["wallet_addresses"]["wallet_1"]
            self.demo_addresses = list(data["wallet_addresses"].values())
            self.wallet_info = data.get("wallet_info", {})
            self.devnet_tokens = data.get("devnet_tokens", {})
            self.invalid_addresses = data.get("invalid_addresses", [])

            print(f" Loaded test data from embedded configuration")
            print(f"   Network: {self.network}")
            print(f"   Addresses: {len(self.demo_addresses)}")
            print(f"   Tokens: {len(self.devnet_tokens)}\n")

        except Exception as e:
            print(f" Failed to load test data: {e}")
            raise

    def create_agent(self, name: str, tools: List, description: str) -> ToolCallAgent:
        """Create a specialized agent with specific tools"""
        network = self.network

        class SolanaSpecialistAgent(ToolCallAgent):
            agent_name: str = name
            agent_description: str = description
            system_prompt: str = f"""
            You are a Solana blockchain specialist focused on {description}.
            Use the available tools to analyze Solana blockchain data and provide comprehensive insights.
            
            **CRITICAL - RPC URL Configuration:**
            - You MUST provide the rpc_url parameter when calling tools
            - For Solana {network}, use: "https://api.{network}.solana.com"
            - Example: solana_wallet_info(address="...", rpc_url="https://api.devnet.solana.com")
            - NEVER omit the rpc_url parameter - it is required for proper network connection
            
            **CRITICAL - Private Key Handling:**
            - Private keys are automatically read from environment variables (SOLANA_PRIVATE_KEY or WALLET_PRIVATE_KEY)
            - NEVER ask the user for their private key - it's already configured in the environment
            - Do NOT include private_key parameter in tool calls unless explicitly provided by the user
            - Tools will automatically use the private key from environment variables when needed
            
            **Network Information:**
            - Current network: {network}
            - RPC URL: https://api.{network}.solana.com
            
            Provide clear, informative responses based on the tool results.
            """
            max_steps: int = 5

        # Create ToolManager with the provided tools
        tool_manager = ToolManager(tools)
        
        agent = SolanaSpecialistAgent(
            llm=ChatBot(
                
            ),
            available_tools=tool_manager
        )
        return agent

    def setup_agents(self):
        """Setup specialized agents for different Solana operations"""

        # Agent 1: Wallet Specialist
        wallet_tools = [SolanaWalletInfoTool()]
        self.agents["wallet"] = self.create_agent(
            "Wallet Specialist",
            wallet_tools,
            "wallet management and portfolio analysis",
        )

        # Agent 2: Transfer Specialist
        transfer_tools = [SolanaTransferTool()]
        self.agents["transfer"] = self.create_agent(
            "Transfer Specialist",
            transfer_tools,
            "token transfers and transaction management",
        )

        # Agent 3: DeFi Trader
        swap_tools = [SolanaSwapTool(), SolanaWalletInfoTool()]
        self.agents["trader"] = self.create_agent(
            "DeFi Trader",
            swap_tools,
            "token swaps and DeFi operations",
        )

        # Agent 4: Data Analyst 
        analyst_tools = [SolanaWalletInfoTool()]  
        self.agents["analyst"] = self.create_agent(
            "Data Analyst",
            analyst_tools,
            "token metadata, address validation, and security analysis",
        )

    def print_section_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")

    async def run_agent_scenario(
        self, agent_name: str, scenario_title: str, user_message: str
    ):
        """Run a specific scenario with an agent"""
        print(f" Scenario: {scenario_title}")
        print(f" Query: {user_message}")
    
        try:
            self.agents[agent_name].clear()
            response = await self.agents[agent_name].run(user_message)
            print(f"✅ Agent Response: {response}")
            return response

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    async def _generate_llm_analysis(self, scenario_data: Dict[str, Any]) -> str:
        """Generate LLM analysis for scenario results"""
        try:
            llm_manager = get_llm_manager()
            prompt = f"""
            Analyze this Solana blockchain operation and provide insights:

            Scenario: {scenario_data.get('scenario', 'Unknown')}
            Data: {scenario_data}

            Please provide:
            1. Key findings
            2. Relevant insights
            3. Recommendations

            Keep response concise and actionable.
            """
            messages = [Message(role="user", content=prompt)]
            response = await llm_manager.chat(messages)
            return response.content.strip()

        except Exception as e:
            return f"Analysis unavailable: {str(e)}"

    async def scenario_1_wallet_analysis(self):
        """Scenario 1: Wallet Balance & Portfolio Analysis"""
        self.print_section_header("Scenario 1: Wallet Balance & Portfolio Analysis")

        scenario_data = {
            "scenario": "wallet_analysis",
            "timestamp": datetime.now().isoformat(),
            "addresses": self.demo_addresses,
        }

        print(f"\n Analyzing wallets: {self.demo_addresses[0][:16]}... and {self.demo_addresses[1][:16]}...")
        user_query = f"What are the SOL balances and token holdings for these wallets: {self.demo_address} and {self.demo_addresses[1]}? Use rpc_url='{self.rpc_url}' when calling solana_wallet_info tool. Provide a comprehensive portfolio analysis."

        response = await self.run_agent_scenario(
            "wallet", "Wallet Balance & Portfolio Analysis", user_query
        )

        if response:
            scenario_data["agent_response"] = response
            scenario_data["llm_analysis"] = await self._generate_llm_analysis(
                scenario_data
            )
            self.demo_results.append(scenario_data)

            print("\n LLM ANALYSIS:")
            print("-" * 40)
            print(scenario_data["llm_analysis"])

    async def scenario_2_transfer_planning_and_execution(self):
        """Scenario 2: Transfer Planning & Execution"""
        self.print_section_header("Scenario 2: Transfer Planning & Execution")

        scenario_data = {
            "scenario": "transfer_execution",
            "timestamp": datetime.now().isoformat(),
            "from": self.demo_address,
            "to": self.demo_addresses[1],
            "amount": 0.5,
        }

        print(
            f"\n Planning transfer of 0.5 SOL from {self.demo_address[:16]}... to {self.demo_addresses[1][:16]}..."
        )
        
        # Check if private key is configured
        import os
        has_private_key = bool(os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("WALLET_PRIVATE_KEY"))
        
        if has_private_key:
            user_query = f"""
            Execute a 0.5 SOL transfer from {self.demo_address} to {self.demo_addresses[1]}.
            
            Please:
            1. Use solana_wallet_info tool with rpc_url='{self.rpc_url}' to check the sender's balance
            2. Validate the recipient address format
            3. If balance is sufficient, execute the transfer using solana_transfer tool with:
               - recipient: {self.demo_addresses[1]}
               - amount: 0.5
               - rpc_url: '{self.rpc_url}'
            4. Provide transaction confirmation details
            
            Use rpc_url='{self.rpc_url}' for all tool calls.
            """
        else:
            user_query = f"""
            Plan and analyze a 0.5 SOL transfer from {self.demo_address} to {self.demo_addresses[1]}.
            
            **NOTE**: No private key configured. This is a PLANNING scenario only.
            
            Please:
            1. Use solana_wallet_info tool with rpc_url='{self.rpc_url}' to check the sender's balance
            2. Validate the recipient address format
            3. Estimate transaction fees (typically ~0.000005 SOL)
            4. Provide a transfer plan summary
            
            Do NOT call solana_transfer tool - private key is required for execution.
            """

        response = await self.run_agent_scenario(
            "transfer", "Transfer Planning & Execution", user_query
        )

        if response:
            scenario_data["agent_response"] = response
            scenario_data["llm_analysis"] = await self._generate_llm_analysis(
                scenario_data
            )
            self.demo_results.append(scenario_data)

            print("\n LLM ANALYSIS:")
            print("-" * 40)
            print(scenario_data["llm_analysis"])

    async def scenario_4_swap_analysis_and_execution(self):
        """Scenario 4: DeFi Swap Analysis & Strategy"""
        self.print_section_header("Scenario 4: DeFi Swap Analysis & Strategy")

        sol_mint = self.devnet_tokens["SOL"]["mint"]
        usdc_mint = self.devnet_tokens["USDC"]["mint"]

        scenario_data = {
            "scenario": "swap_analysis",
            "timestamp": datetime.now().isoformat(),
            "input_token": "SOL",
            "output_token": "USDC",
            "amount": 0.5,
            "note": "Jupiter Quote API has limited support on Solana Devnet. This scenario demonstrates educational analysis.",
        }

        print(f"\n Analyzing DeFi swap opportunity: SOL → USDC")
        print(f" ℹ️  Note: Jupiter Aggregator Quote API has limited availability on Solana Devnet.")
        print(f"    This scenario provides educational analysis of swap mechanics.\n")
        # Check if private key is configured for actual swap execution
        import os
        has_private_key = bool(os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("WALLET_PRIVATE_KEY"))
        
        if has_private_key:
            user_query = f"""
            Execute a SOL to USDC token swap:
            
            **IMPORTANT**: The private key is already configured in environment variables (SOLANA_PRIVATE_KEY).
            You do NOT need to ask for the private key - the tools will automatically use it from the environment.
            
            Please:
            1. Use solana_wallet_info tool with rpc_url='{self.rpc_url}' and address='{self.demo_address}' to check the wallet balance
            2. If balance is sufficient (at least 0.5 SOL + fees), execute the swap using solana_swap tool with:
               - input_token: "SOL" (use the string "SOL" for native SOL, not the mint address)
               - output_token: "{usdc_mint}"
               - amount: 0.5
               - rpc_url: '{self.rpc_url}'
               - Do NOT provide private_key parameter - it will be read from environment automatically
            3. Provide transaction confirmation details
            
            **CRITICAL**: 
            - For native SOL swaps, you MUST use input_token="SOL" (the string), NOT the mint address
            - The private key is already available in environment variables - do NOT ask for it
            - Use rpc_url='{self.rpc_url}' for all tool calls
            """
        else:
            user_query = f"""
            Please provide a comprehensive analysis of a potential SOL to USDC token swap:

            1. Token Information:
               - Source: SOL (native SOL, use "SOL" string for input_token)
               - Target: USDC (mint: {usdc_mint})
               - Amount: 0.5 SOL

            2. DeFi Swap Mechanics:
               - Explain how token swaps work on Solana using DEX aggregators
               - Describe slippage, price impact, and fees
               - Discuss liquidity pools and routing

            3. Execution Strategy:
               - What are the steps to execute this swap on mainnet?
               - How to minimize slippage?
               - What are risk considerations?

            4. Tools & Services:
               - Which DEX aggregators support this pair?
               - Compare Raydium, Jupiter, and other venues
               - Explain trade-offs between centralized and decentralized exchanges

            **NOTE**: No private key configured. This is an ANALYSIS scenario only.
            Use solana_wallet_info tool to check wallet balance if needed.
            Do NOT call solana_swap tool - private key is required for execution.
            
            Note: Jupiter Quote API has limited support on Devnet, but this analysis applies to mainnet execution.
            When calling tools, always use rpc_url='{self.rpc_url}'.
            """

        response = await self.run_agent_scenario(
            "trader", "Token Swap Analysis & Execution", user_query
        )

        if response:
            scenario_data["agent_response"] = response
            scenario_data["llm_analysis"] = await self._generate_llm_analysis(
                scenario_data
            )
            self.demo_results.append(scenario_data)

            print("\n LLM ANALYSIS:")
            print("-" * 40)
            print(scenario_data["llm_analysis"])

    async def scenario_3_address_validation_and_analysis(self):
        """Scenario 3: Address Validation & Token Metadata Analysis"""
        self.print_section_header("Scenario 3: Address Validation & Token Metadata Analysis")

        scenario_data = {
            "scenario": "address_validation",
            "timestamp": datetime.now().isoformat(),
            "test_addresses": [self.demo_address] + self.invalid_addresses,
            "test_tokens": list(self.devnet_tokens.keys()),
        }

        print(f"\n Validating addresses and analyzing token metadata")

        # Build token info string
        token_info = ", ".join([
            f"{t['symbol']} ({t['mint'][:8]}...)"
            for t in self.devnet_tokens.values()
        ])

        user_query = f"""
        Please perform the following analysis:

        1. Address Validation: Validate these addresses and identify which are valid Solana addresses:
           - Valid address: {self.demo_address}
           - Invalid address 1: {self.invalid_addresses[0]}
           - Invalid address 2: {self.invalid_addresses[1]}

        2. Token Metadata Analysis: Provide information about these Solana tokens:
           {token_info}

        3. Security Analysis: What are the key security considerations when validating Solana addresses?

        When calling solana_wallet_info tool, always use rpc_url='{self.rpc_url}'.
        Provide clear explanations for each analysis point.
        """

        response = await self.run_agent_scenario(
            "analyst", "Address Validation & Token Metadata Analysis", user_query
        )

        if response:
            scenario_data["agent_response"] = response
            scenario_data["llm_analysis"] = await self._generate_llm_analysis(
                scenario_data
            )
            self.demo_results.append(scenario_data)

            print("\n LLM ANALYSIS:")
            print("-" * 40)
            print(scenario_data["llm_analysis"])

    async def run_comprehensive_demo(self):

        try:
            # Initialize specialized agents once before running scenarios
            if not self.agents:
                self.setup_agents()

            # await self.scenario_1_wallet_analysis()
            # await asyncio.sleep(1)

            # await self.scenario_2_transfer_planning_and_execution()
            # await asyncio.sleep(1)

            # await self.scenario_3_address_validation_and_analysis()
            # await asyncio.sleep(1)

            await self.scenario_4_swap_analysis_and_execution()

            self.print_section_header("DEMO COMPLETED")
            print(f"\n✅ All {len(self.demo_results)} scenarios executed successfully!")
            print(f"\n Scenarios Completed:")
            for i, result in enumerate(self.demo_results, 1):
                scenario_name = result.get("scenario", "Unknown").replace("_", " ")
                print(f"   {i}. {scenario_name.title()}")

            print(f"\n AI Agents Used:")
            for agent_name, agent in self.agents.items():
                print(f"   - {agent.agent_name}")

        except Exception as e:
            print(f"\n❌ Demo error: {str(e)}")
            raise


async def main():
    """Main demonstration function"""
    print("\n" + "=" * 70)
    print("SOLANA TOOLKIT - AGENT-BASED COMPREHENSIVE DEMONSTRATION")
    print("=" * 70)
    print(
        "Showcasing Solana blockchain tools through specialized AI agents"
    )
    print("=" * 70 + "\n")

    demo = SolanaToolkitDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())
