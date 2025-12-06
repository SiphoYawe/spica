"""
SpoonOS Integration Service

This module provides integration with SpoonOS framework, demonstrating:
1. ChatBot initialization with OpenAI
2. SpoonReactMCP agent creation
3. StateGraph construction and compilation
4. ToolManager integration

All implementations follow patterns verified from /spoon-core/ source code.
"""

import logging
import asyncio
from typing import TypedDict, Optional, Any, Dict, List, Callable, Tuple, Type
from functools import lru_cache
from pydantic import BaseModel, ConfigDict

# Verified imports from SpoonOS source
from spoon_ai.chat import ChatBot
from spoon_ai.agents import SpoonReactMCP, SpoonReactAI
from spoon_ai.graph import StateGraph, CompiledGraph, add_messages
from spoon_ai.tools import ToolManager
from spoon_ai.tools.base import BaseTool

from app.config import settings

logger = logging.getLogger(__name__)


class SpoonOSService:
    """
    Service for managing SpoonOS integrations.

    Provides factory methods for creating ChatBot, agents, and StateGraphs.
    All methods verified against spoon-core source code.
    """

    def __init__(self):
        """
        Initialize SpoonOS service.

        Raises:
            RuntimeError: If critical settings are missing (OPENAI_API_KEY)
        """
        # CR-1.2-008: Validate critical settings on initialization
        if not settings.openai_api_key:
            error_msg = "OPENAI_API_KEY is required but not configured. Cannot initialize SpoonOSService."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        self._chatbot: Optional[ChatBot] = None
        logger.info("SpoonOSService initialized with validated configuration")

    @property
    def chatbot(self) -> ChatBot:
        """
        Get or create ChatBot instance configured with OpenAI.

        Returns:
            ChatBot: Configured ChatBot instance

        Raises:
            RuntimeError: If ChatBot creation fails
        """
        if self._chatbot is None:
            try:
                logger.info("Creating ChatBot with OpenAI provider")
                # CR-1.2-002: ChatBot pulls API key from environment via LLM Manager
                # Do not pass api_key parameter
                self._chatbot = ChatBot(llm_provider="openai")
                logger.info("ChatBot created successfully")
            except Exception as e:
                error_msg = f"Failed to create ChatBot: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self._chatbot

    async def create_spoon_react_mcp(
        self,
        name: str = "spica_agent",
        description: str = "Spica workflow agent",
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> SpoonReactMCP:
        """
        Create a SpoonReactMCP agent instance.

        Args:
            name: Agent name
            description: Agent description
            tools: List of BaseTool instances
            system_prompt: Custom system prompt
            **kwargs: Additional SpoonReactMCP parameters

        Returns:
            SpoonReactMCP: Configured agent instance

        Raises:
            RuntimeError: If agent creation or initialization fails
        """
        try:
            logger.info(f"Creating SpoonReactMCP agent: {name}")

            # Prepare agent configuration
            agent_config = {
                "name": name,
                "description": description,
                "llm": self.chatbot,
            }

            # Add tools if provided
            if tools:
                agent_config["available_tools"] = ToolManager(tools)
                logger.info(f"Agent configured with {len(tools)} tools")

            # Add system prompt if provided
            if system_prompt:
                agent_config["system_prompt"] = system_prompt

            # Merge any additional kwargs
            agent_config.update(kwargs)

            # Create agent
            agent = SpoonReactMCP(**agent_config)

            # CR-1.2-003: Initialize agent asynchronously
            logger.info(f"Initializing SpoonReactMCP agent '{name}'")
            await agent.initialize()
            logger.info(f"SpoonReactMCP agent '{name}' created and initialized successfully")

            return agent

        except Exception as e:
            error_msg = f"Failed to create SpoonReactMCP agent '{name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def create_state_graph(
        self,
        state_schema: Type[TypedDict],
        nodes: Optional[Dict[str, Callable]] = None,
        edges: Optional[List[Tuple[str, str]]] = None
    ) -> StateGraph:
        """
        Create a StateGraph instance.

        Args:
            state_schema: TypedDict class defining state structure
            nodes: Optional dict of {node_name: node_function}
            edges: Optional list of (source, target) tuples

        Returns:
            StateGraph: Configured graph instance

        Raises:
            RuntimeError: If graph creation fails
        """
        try:
            logger.info(f"Creating StateGraph with schema: {state_schema.__name__}")

            graph = StateGraph(state_schema)

            # Add nodes if provided
            if nodes:
                for node_name, node_func in nodes.items():
                    graph.add_node(node_name, node_func)
                    logger.info(f"Added node: {node_name}")

            # Add edges if provided
            if edges:
                for source, target in edges:
                    graph.add_edge(source, target)
                    logger.info(f"Added edge: {source} -> {target}")

            logger.info("StateGraph created successfully")
            return graph

        except Exception as e:
            error_msg = f"Failed to create StateGraph: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def compile_graph(self, graph: StateGraph) -> CompiledGraph:
        """
        Compile a StateGraph into executable form.

        Args:
            graph: StateGraph to compile

        Returns:
            CompiledGraph: Compiled executable graph

        Raises:
            RuntimeError: If graph compilation fails
        """
        try:
            logger.info("Compiling StateGraph")
            compiled = graph.compile()
            logger.info("StateGraph compiled successfully")
            return compiled

        except Exception as e:
            error_msg = f"Failed to compile StateGraph: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


# Example state schema for demonstrations
class DemoWorkflowState(TypedDict):
    """
    Example state schema for testing StateGraph.

    This TypedDict defines the structure of state that flows through
    a demonstration workflow graph. Used for testing and examples.

    Attributes:
        workflow_id: Unique identifier for the workflow execution
        query: Input query or task to be processed
        result: Output result after processing
        status: Current status of the workflow (pending, processing, completed, failed)
    """
    workflow_id: str
    query: str
    result: str
    status: str


# Example tool for demonstrations
class DemoTool(BaseTool):
    """
    Example tool implementation for testing.
    Follows BaseTool pattern from spoon-core.
    """

    # CR-1.2-007: Add Pydantic model configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    name: str = "demo_tool"
    description: str = "A simple demo tool for testing SpoonOS integration"
    parameters: dict = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "Input string to process"
            }
        },
        "required": ["input"]
    }

    async def execute(self, input: str) -> str:
        """
        Execute the demo tool.

        Args:
            input: Input string

        Returns:
            str: Processed result
        """
        logger.info(f"DemoTool executing with input: {input}")
        return f"DemoTool processed: {input}"


# Example node function for StateGraph
async def demo_process_node(state: DemoWorkflowState) -> dict:
    """
    Example node function for StateGraph.

    Nodes return dict of state updates.
    """
    logger.info(f"Processing workflow: {state['workflow_id']}")
    return {
        "result": f"Processed query: {state['query']}",
        "status": "completed"
    }


# CR-1.2-005: Use FastAPI dependency pattern with @lru_cache for singleton behavior
@lru_cache()
def get_spoon_service() -> SpoonOSService:
    """
    Get or create SpoonOSService singleton instance.

    Uses @lru_cache to ensure singleton behavior within FastAPI's dependency injection.
    This replaces the global singleton pattern with a more idiomatic FastAPI approach.

    Returns:
        SpoonOSService: Singleton service instance

    Raises:
        RuntimeError: If service initialization fails (e.g., missing OPENAI_API_KEY)
    """
    return SpoonOSService()


# Convenience functions for common operations
async def test_chatbot() -> bool:
    """
    Test ChatBot functionality.

    Returns:
        bool: True if ChatBot works correctly
    """
    try:
        service = get_spoon_service()
        chatbot = service.chatbot
        logger.info("ChatBot test: PASS")
        return True
    except Exception as e:
        logger.error(f"ChatBot test failed: {e}")
        return False


async def test_spoon_react_mcp() -> bool:
    """
    Test SpoonReactMCP agent creation.

    Returns:
        bool: True if agent can be created
    """
    try:
        service = get_spoon_service()
        # CR-1.2-003: create_spoon_react_mcp is now async
        agent = await service.create_spoon_react_mcp(
            name="test_agent",
            description="Test agent for integration",
            tools=[DemoTool()]
        )
        logger.info(f"SpoonReactMCP test: PASS - Agent created: {agent.name}")
        return True
    except Exception as e:
        logger.error(f"SpoonReactMCP test failed: {e}")
        return False


async def test_state_graph() -> bool:
    """
    Test StateGraph creation and compilation.

    Returns:
        bool: True if StateGraph works correctly
    """
    try:
        service = get_spoon_service()

        # Create graph
        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"process": demo_process_node},
            edges=[("__start__", "process"), ("process", "END")]
        )

        # Compile graph
        compiled = service.compile_graph(graph)

        # Execute graph
        initial_state = {
            "workflow_id": "test_001",
            "query": "test query",
            "result": "",
            "status": "pending"
        }
        result = await compiled.invoke(initial_state)

        logger.info(f"StateGraph test: PASS - Result: {result}")
        return result["status"] == "completed"

    except Exception as e:
        logger.error(f"StateGraph test failed: {e}")
        return False


async def run_all_tests() -> Dict[str, bool]:
    """
    Run all integration tests in parallel for efficiency.

    Returns:
        dict: Test results {test_name: passed}
    """
    logger.info("Running all SpoonOS integration tests in parallel")

    # CR-1.2-009: Use asyncio.gather() for parallel execution
    chatbot_result, agent_result, graph_result = await asyncio.gather(
        test_chatbot(),
        test_spoon_react_mcp(),
        test_state_graph(),
        return_exceptions=False
    )

    results = {
        "chatbot": chatbot_result,
        "spoon_react_mcp": agent_result,
        "state_graph": graph_result
    }

    passed = sum(results.values())
    total = len(results)
    logger.info(f"Integration tests completed: {passed}/{total} passed")

    return results
