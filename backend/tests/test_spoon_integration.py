"""
SpoonOS Integration Tests

Tests for Story 1.2: SpoonOS Integration

Acceptance Criteria:
- [ ] spoon_ai package installed and importable
- [ ] ChatBot configured with OpenAI
- [ ] Basic SpoonReactMCP agent instantiable
- [ ] StateGraph can be created and compiled
- [ ] Integration test passes

All tests verify against actual SpoonOS source code patterns.
"""

import pytest
import asyncio
from typing import TypedDict
import logging

# Skip entire module if spoon_ai not available
pytest.importorskip("spoon_ai", reason="spoon_ai package not installed")

# Test imports - if these fail, SpoonOS is not properly installed
from spoon_ai.chat import ChatBot
from spoon_ai.agents import SpoonReactMCP, SpoonReactAI
from spoon_ai.graph import StateGraph, CompiledGraph, add_messages
from spoon_ai.tools import ToolManager
from spoon_ai.tools.base import BaseTool

# Test our service
from app.services.spoon_service import (
    SpoonOSService,
    get_spoon_service,
    DemoTool,
    DemoWorkflowState,
    demo_process_node,
    test_chatbot,
    test_spoon_react_mcp,
    test_state_graph,
    run_all_tests
)

logger = logging.getLogger(__name__)


class TestSpoonOSImports:
    """
    Test AC: spoon_ai package installed and importable
    """

    def test_import_chatbot(self):
        """Verify ChatBot can be imported"""
        assert ChatBot is not None
        logger.info("✓ ChatBot import successful")

    def test_import_spoon_react_ai(self):
        """Verify SpoonReactAI can be imported"""
        assert SpoonReactAI is not None
        logger.info("✓ SpoonReactAI import successful")

    def test_import_spoon_react_mcp(self):
        """Verify SpoonReactMCP can be imported"""
        assert SpoonReactMCP is not None
        logger.info("✓ SpoonReactMCP import successful")

    def test_import_state_graph(self):
        """Verify StateGraph can be imported"""
        assert StateGraph is not None
        logger.info("✓ StateGraph import successful")

    def test_import_compiled_graph(self):
        """Verify CompiledGraph can be imported"""
        assert CompiledGraph is not None
        logger.info("✓ CompiledGraph import successful")

    def test_import_tool_manager(self):
        """Verify ToolManager can be imported"""
        assert ToolManager is not None
        logger.info("✓ ToolManager import successful")

    def test_import_base_tool(self):
        """Verify BaseTool can be imported"""
        assert BaseTool is not None
        logger.info("✓ BaseTool import successful")

    def test_import_add_messages(self):
        """Verify add_messages reducer can be imported"""
        assert add_messages is not None
        logger.info("✓ add_messages import successful")


class TestChatBotConfiguration:
    """
    Test AC: ChatBot configured with OpenAI
    """

    def test_chatbot_instantiation(self):
        """Verify ChatBot can be instantiated with OpenAI provider"""
        # This will use the OPENAI_API_KEY from environment
        service = SpoonOSService()
        chatbot = service.chatbot

        assert chatbot is not None
        logger.info("✓ ChatBot instantiated successfully")

    def test_chatbot_singleton(self):
        """Verify ChatBot is reused (singleton pattern)"""
        service = SpoonOSService()
        chatbot1 = service.chatbot
        chatbot2 = service.chatbot

        assert chatbot1 is chatbot2
        logger.info("✓ ChatBot singleton pattern working")

    @pytest.mark.asyncio
    async def test_chatbot_service_function(self):
        """Verify test_chatbot() service function works"""
        result = await test_chatbot()
        assert result is True
        logger.info("✓ ChatBot service function test passed")


class TestSpoonReactMCPAgent:
    """
    Test AC: Basic SpoonReactMCP agent instantiable
    """

    @pytest.mark.asyncio
    async def test_agent_creation_basic(self):
        """Verify basic SpoonReactMCP agent can be created"""
        service = SpoonOSService()
        # CR-1.2-003: create_spoon_react_mcp is now async
        agent = await service.create_spoon_react_mcp(
            name="test_agent",
            description="Test agent"
        )

        assert agent is not None
        assert isinstance(agent, SpoonReactMCP)
        assert agent.name == "test_agent"
        assert agent.description == "Test agent"
        logger.info("✓ Basic SpoonReactMCP agent created")

    @pytest.mark.asyncio
    async def test_agent_creation_with_tools(self):
        """Verify SpoonReactMCP agent can be created with tools"""
        service = SpoonOSService()
        # CR-1.2-003: create_spoon_react_mcp is now async
        agent = await service.create_spoon_react_mcp(
            name="tool_agent",
            description="Agent with tools",
            tools=[DemoTool()]
        )

        assert agent is not None
        assert isinstance(agent, SpoonReactMCP)
        assert agent.available_tools is not None
        assert len(agent.available_tools.tool_map) == 1
        logger.info("✓ SpoonReactMCP agent with tools created")

    @pytest.mark.asyncio
    async def test_agent_has_llm(self):
        """Verify agent has ChatBot attached"""
        service = SpoonOSService()
        # CR-1.2-003: create_spoon_react_mcp is now async
        agent = await service.create_spoon_react_mcp(name="llm_test")

        assert agent.llm is not None
        assert isinstance(agent.llm, ChatBot)
        logger.info("✓ Agent has ChatBot LLM attached")

    @pytest.mark.asyncio
    async def test_agent_service_function(self):
        """Verify test_spoon_react_mcp() service function works"""
        result = await test_spoon_react_mcp()
        assert result is True
        logger.info("✓ SpoonReactMCP service function test passed")


class TestStateGraphCreation:
    """
    Test AC: StateGraph can be created and compiled
    """

    def test_state_graph_creation(self):
        """Verify StateGraph can be created"""
        service = SpoonOSService()
        graph = service.create_state_graph(state_schema=DemoWorkflowState)

        assert graph is not None
        assert isinstance(graph, StateGraph)
        logger.info("✓ StateGraph created successfully")

    def test_state_graph_with_nodes(self):
        """Verify StateGraph can have nodes added"""
        service = SpoonOSService()

        async def test_node(state: DemoWorkflowState) -> dict:
            return {"status": "processed"}

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"test": test_node}
        )

        assert graph is not None
        logger.info("✓ StateGraph with nodes created")

    def test_state_graph_with_edges(self):
        """Verify StateGraph can have edges added"""
        service = SpoonOSService()

        async def node1(state: DemoWorkflowState) -> dict:
            return {"status": "node1"}

        async def node2(state: DemoWorkflowState) -> dict:
            return {"status": "node2"}

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"node1": node1, "node2": node2},
            edges=[("__start__", "node1"), ("node1", "node2"), ("node2", "END")]
        )

        assert graph is not None
        logger.info("✓ StateGraph with edges created")

    def test_state_graph_compilation(self):
        """Verify StateGraph can be compiled"""
        service = SpoonOSService()

        async def simple_node(state: DemoWorkflowState) -> dict:
            return {"status": "done"}

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"process": simple_node},
            edges=[("__start__", "process"), ("process", "END")]
        )

        compiled = service.compile_graph(graph)
        assert compiled is not None
        assert isinstance(compiled, CompiledGraph)
        logger.info("✓ StateGraph compiled successfully")

    @pytest.mark.asyncio
    async def test_state_graph_execution(self):
        """Verify compiled StateGraph can execute"""
        service = SpoonOSService()

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"process": demo_process_node},
            edges=[("__start__", "process"), ("process", "END")]
        )

        compiled = service.compile_graph(graph)

        initial_state = {
            "workflow_id": "test_exec_001",
            "query": "test execution",
            "result": "",
            "status": "pending"
        }

        result = await compiled.invoke(initial_state)

        assert result is not None
        assert result["status"] == "completed"
        assert "Processed query" in result["result"]
        logger.info("✓ StateGraph execution successful")

    @pytest.mark.asyncio
    async def test_state_graph_service_function(self):
        """Verify test_state_graph() service function works"""
        result = await test_state_graph()
        assert result is True
        logger.info("✓ StateGraph service function test passed")


class TestToolSystem:
    """
    Test tool management and execution
    """

    @pytest.mark.asyncio
    async def test_demo_tool_execution(self):
        """Verify DemoTool can execute"""
        tool = DemoTool()
        result = await tool.execute(input="test")

        assert result is not None
        assert "DemoTool processed" in result
        assert "test" in result
        logger.info("✓ DemoTool execution successful")

    def test_tool_manager_creation(self):
        """Verify ToolManager can manage tools"""
        tools = [DemoTool()]
        manager = ToolManager(tools)

        assert manager is not None
        assert len(manager.tool_map) == 1
        assert "demo_tool" in manager.tool_map
        logger.info("✓ ToolManager created and managing tools")


class TestCompleteIntegration:
    """
    Test AC: Integration test passes

    Complete end-to-end integration test combining all components
    """

    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self):
        """
        Complete workflow simulation:
        1. Create service
        2. Create agent with tools
        3. Create and compile StateGraph
        4. Execute workflow
        """
        # 1. Create service
        service = get_spoon_service()
        assert service is not None
        logger.info("Step 1: Service created")

        # 2. Create agent with tools
        # CR-1.2-003: create_spoon_react_mcp is now async
        agent = await service.create_spoon_react_mcp(
            name="workflow_agent",
            description="Test workflow agent",
            tools=[DemoTool()],
            system_prompt="You are a test workflow agent."
        )
        assert agent is not None
        logger.info("Step 2: Agent created")

        # 3. Create and compile StateGraph
        async def workflow_node(state: DemoWorkflowState) -> dict:
            return {
                "result": f"Workflow processed: {state['query']}",
                "status": "completed"
            }

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"workflow": workflow_node},
            edges=[("__start__", "workflow"), ("workflow", "END")]
        )
        compiled = service.compile_graph(graph)
        assert compiled is not None
        logger.info("Step 3: StateGraph created and compiled")

        # 4. Execute workflow
        initial_state = {
            "workflow_id": "integration_test_001",
            "query": "Complete integration test",
            "result": "",
            "status": "pending"
        }
        result = await compiled.invoke(initial_state)

        assert result["status"] == "completed"
        assert "Workflow processed" in result["result"]
        logger.info("Step 4: Workflow executed successfully")

        logger.info("✓ COMPLETE INTEGRATION TEST PASSED")

    @pytest.mark.asyncio
    async def test_all_integration_tests(self):
        """Run all integration tests via service function"""
        results = await run_all_tests()

        assert results["chatbot"] is True
        assert results["spoon_react_mcp"] is True
        assert results["state_graph"] is True

        logger.info("✓ ALL INTEGRATION TESTS PASSED")


class TestErrorHandling:
    """
    CR-1.2-004: Test error cases and edge conditions

    Comprehensive error handling tests for:
    - Invalid API key handling
    - Agent creation failures
    - Graph execution with failing nodes
    - Graph compilation with invalid schema
    """

    @pytest.mark.asyncio
    async def test_missing_openai_api_key(self, monkeypatch):
        """Test that service fails gracefully when OPENAI_API_KEY is missing"""
        # Temporarily remove the API key
        from app.config import settings as config_settings
        original_key = config_settings.openai_api_key

        try:
            # Set empty API key
            monkeypatch.setattr(config_settings, "openai_api_key", "")

            # Should raise RuntimeError on initialization
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY is required"):
                SpoonOSService()

            logger.info("✓ Service properly rejects missing OPENAI_API_KEY")
        finally:
            # Restore original key
            monkeypatch.setattr(config_settings, "openai_api_key", original_key)

    @pytest.mark.asyncio
    async def test_chatbot_creation_error_handling(self, monkeypatch):
        """Test ChatBot creation error handling"""
        service = SpoonOSService()

        # Force chatbot creation to fail by mocking ChatBot constructor
        def mock_chatbot_fail(*args, **kwargs):
            raise ValueError("Simulated ChatBot creation failure")

        from spoon_ai import chat
        original_chatbot = chat.ChatBot

        try:
            monkeypatch.setattr(chat, "ChatBot", mock_chatbot_fail)
            service._chatbot = None  # Reset cached chatbot

            # Should raise RuntimeError with descriptive message
            with pytest.raises(RuntimeError, match="Failed to create ChatBot"):
                _ = service.chatbot

            logger.info("✓ ChatBot creation error properly handled")
        finally:
            monkeypatch.setattr(chat, "ChatBot", original_chatbot)

    @pytest.mark.asyncio
    async def test_agent_creation_failure(self, monkeypatch):
        """Test agent creation error handling"""
        service = SpoonOSService()

        # Force agent creation to fail
        from spoon_ai import agents
        original_agent = agents.SpoonReactMCP

        def mock_agent_fail(*args, **kwargs):
            raise ValueError("Simulated agent creation failure")

        try:
            monkeypatch.setattr(agents, "SpoonReactMCP", mock_agent_fail)

            with pytest.raises(RuntimeError, match="Failed to create SpoonReactMCP agent"):
                await service.create_spoon_react_mcp(name="failing_agent")

            logger.info("✓ Agent creation error properly handled")
        finally:
            monkeypatch.setattr(agents, "SpoonReactMCP", original_agent)

    @pytest.mark.asyncio
    async def test_graph_execution_with_failing_node(self):
        """Test graph execution when a node raises an exception"""
        service = SpoonOSService()

        # Create a node that always fails
        async def failing_node(state: DemoWorkflowState) -> dict:
            raise ValueError("Simulated node failure")

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"failing": failing_node},
            edges=[("__start__", "failing"), ("failing", "END")]
        )

        compiled = service.compile_graph(graph)

        initial_state = {
            "workflow_id": "error_test_001",
            "query": "test",
            "result": "",
            "status": "pending"
        }

        # Graph execution should propagate the error
        with pytest.raises(ValueError, match="Simulated node failure"):
            await compiled.invoke(initial_state)

        logger.info("✓ Graph execution error properly propagated")

    @pytest.mark.asyncio
    async def test_graph_compilation_with_invalid_schema(self):
        """Test graph compilation error handling"""
        service = SpoonOSService()

        # Create graph with invalid schema (not a TypedDict)
        class InvalidSchema:
            pass

        # Should raise error during graph creation or compilation
        with pytest.raises((RuntimeError, TypeError, ValueError)):
            graph = service.create_state_graph(
                state_schema=InvalidSchema,  # Invalid - not TypedDict
                nodes={},
                edges=[]
            )

        logger.info("✓ Graph creation with invalid schema properly rejected")

    @pytest.mark.asyncio
    async def test_graph_with_disconnected_nodes(self):
        """Test graph compilation with disconnected nodes"""
        service = SpoonOSService()

        async def node1(state: DemoWorkflowState) -> dict:
            return {"status": "node1"}

        async def orphan_node(state: DemoWorkflowState) -> dict:
            return {"status": "orphan"}

        # Create graph with orphaned node (no edges connecting it)
        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"node1": node1, "orphan": orphan_node},
            edges=[("__start__", "node1"), ("node1", "END")]
            # Note: orphan_node is not connected
        )

        # Compilation should still succeed (orphan nodes are allowed)
        compiled = service.compile_graph(graph)
        assert compiled is not None

        logger.info("✓ Graph with disconnected nodes handled")

    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self):
        """Test tool execution error handling"""

        # Create a tool that fails
        class FailingTool(BaseTool):
            name: str = "failing_tool"
            description: str = "A tool that always fails"
            parameters: dict = {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }

            async def execute(self, input: str) -> str:
                raise RuntimeError("Simulated tool execution failure")

        tool = FailingTool()

        # Tool execution should raise the error
        with pytest.raises(RuntimeError, match="Simulated tool execution failure"):
            await tool.execute(input="test")

        logger.info("✓ Tool execution error properly raised")

    @pytest.mark.asyncio
    async def test_state_graph_compilation_error(self, monkeypatch):
        """Test StateGraph compilation error handling"""
        service = SpoonOSService()

        async def simple_node(state: DemoWorkflowState) -> dict:
            return {"status": "done"}

        graph = service.create_state_graph(
            state_schema=DemoWorkflowState,
            nodes={"process": simple_node},
            edges=[("__start__", "process"), ("process", "END")]
        )

        # Mock compile to fail
        original_compile = graph.compile

        def mock_compile_fail(*args, **kwargs):
            raise ValueError("Simulated compilation failure")

        try:
            monkeypatch.setattr(graph, "compile", mock_compile_fail)

            with pytest.raises(RuntimeError, match="Failed to compile StateGraph"):
                service.compile_graph(graph)

            logger.info("✓ Graph compilation error properly handled")
        finally:
            monkeypatch.setattr(graph, "compile", original_compile)


# Pytest markers for running specific test groups
pytestmark = pytest.mark.asyncio


if __name__ == "__main__":
    """
    Run tests directly:
    python -m pytest backend/tests/test_spoon_integration.py -v
    """
    pytest.main([__file__, "-v", "-s"])
