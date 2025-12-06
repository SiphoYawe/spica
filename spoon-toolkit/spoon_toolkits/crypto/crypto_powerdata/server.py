"""Crypto PowerData MCP server startup functions"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any
import threading
import time

logger = logging.getLogger(__name__)


def start_crypto_powerdata_mcp_stdio(
    env_vars: Optional[Dict[str, str]] = None,
    background: bool = False
) -> Optional[threading.Thread]:
    """
    Start Crypto PowerData MCP server in stdio mode
    
    Args:
        env_vars: Optional environment variables for configuration
        background: If True, run in background thread
        
    Returns:
        Thread object if background=True, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from .main import main
        
        def run_server():
            try:
                main(env_vars=env_vars, transport_mode="stdio")
            except Exception as e:
                logger.error(f"Error running stdio MCP server: {e}")
                raise
        
        if background:
            # Run in background thread
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            logger.info("Crypto PowerData MCP stdio server started in background")
            return thread
        else:
            # Run in current thread (blocking)
            logger.info("Starting Crypto PowerData MCP stdio server...")
            run_server()
            return None
            
    except Exception as e:
        logger.error(f"Failed to start Crypto PowerData MCP stdio server: {e}")
        raise


def start_crypto_powerdata_mcp_sse(
    port: int = 8000,
    host: str = "127.0.0.1",
    env_vars: Optional[Dict[str, str]] = None,
    background: bool = False
) -> Optional[threading.Thread]:
    """
    Start Crypto PowerData MCP server in HTTP/SSE mode
    
    Args:
        port: Port number for HTTP server
        host: Host address for HTTP server
        env_vars: Optional environment variables for configuration
        background: If True, run in background thread
        
    Returns:
        Thread object if background=True, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from .dual_transport_server import run_dual_server
        
        def run_server():
            try:
                asyncio.run(run_dual_server(
                    mode="http",
                    http_port=port,
                    http_host=host,
                    env_vars=env_vars
                ))
            except Exception as e:
                logger.error(f"Error running HTTP/SSE MCP server: {e}")
                raise
        
        if background:
            # Run in background thread
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            logger.info(f"Crypto PowerData MCP HTTP/SSE server started in background on {host}:{port}")
            return thread
        else:
            # Run in current thread (blocking)
            logger.info(f"Starting Crypto PowerData MCP HTTP/SSE server on {host}:{port}...")
            run_server()
            return None
            
    except Exception as e:
        logger.error(f"Failed to start Crypto PowerData MCP HTTP/SSE server: {e}")
        raise


def start_crypto_powerdata_mcp_auto(
    port: int = 8000,
    host: str = "127.0.0.1",
    env_vars: Optional[Dict[str, str]] = None,
    background: bool = False
) -> Optional[threading.Thread]:
    """
    Start Crypto PowerData MCP server in auto-detect mode
    
    Auto-detects whether to use stdio or HTTP/SSE based on environment.
    
    Args:
        port: Port number for HTTP server (if HTTP mode is selected)
        host: Host address for HTTP server (if HTTP mode is selected)
        env_vars: Optional environment variables for configuration
        background: If True, run in background thread
        
    Returns:
        Thread object if background=True, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from .dual_transport_server import run_dual_server
        
        def run_server():
            try:
                asyncio.run(run_dual_server(
                    mode="auto",
                    http_port=port,
                    http_host=host,
                    env_vars=env_vars
                ))
            except Exception as e:
                logger.error(f"Error running auto-mode MCP server: {e}")
                raise
        
        if background:
            # Run in background thread
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            logger.info("Crypto PowerData MCP server started in background (auto-detect mode)")
            return thread
        else:
            # Run in current thread (blocking)
            logger.info("Starting Crypto PowerData MCP server (auto-detect mode)...")
            run_server()
            return None
            
    except Exception as e:
        logger.error(f"Failed to start Crypto PowerData MCP server in auto mode: {e}")
        raise


class CryptoPowerDataMCPServer:
    """
    Crypto PowerData MCP Server manager class
    
    Provides a convenient interface for managing MCP server instances.
    """
    
    def __init__(self):
        self.stdio_thread: Optional[threading.Thread] = None
        self.sse_thread: Optional[threading.Thread] = None
        self.auto_thread: Optional[threading.Thread] = None
    
    def start_stdio(self, env_vars: Optional[Dict[str, str]] = None) -> threading.Thread:
        """Start stdio mode server in background"""
        if self.stdio_thread and self.stdio_thread.is_alive():
            logger.warning("Stdio MCP server is already running")
            return self.stdio_thread
            
        self.stdio_thread = start_crypto_powerdata_mcp_stdio(
            env_vars=env_vars,
            background=True
        )
        return self.stdio_thread
    
    def start_sse(
        self,
        port: int = 8000,
        host: str = "127.0.0.1",
        env_vars: Optional[Dict[str, str]] = None
    ) -> threading.Thread:
        """Start HTTP/SSE mode server in background"""
        if self.sse_thread and self.sse_thread.is_alive():
            logger.warning(f"HTTP/SSE MCP server is already running on {host}:{port}")
            return self.sse_thread
            
        self.sse_thread = start_crypto_powerdata_mcp_sse(
            port=port,
            host=host,
            env_vars=env_vars,
            background=True
        )
        return self.sse_thread
    
    def start_auto(
        self,
        port: int = 8000,
        host: str = "127.0.0.1",
        env_vars: Optional[Dict[str, str]] = None
    ) -> threading.Thread:
        """Start auto-detect mode server in background"""
        if self.auto_thread and self.auto_thread.is_alive():
            logger.warning("Auto-mode MCP server is already running")
            return self.auto_thread
            
        self.auto_thread = start_crypto_powerdata_mcp_auto(
            port=port,
            host=host,
            env_vars=env_vars,
            background=True
        )
        return self.auto_thread
    
    def stop_all(self):
        """Stop all running servers (note: threads are daemon threads and will stop when main process exits)"""
        logger.info("Stopping all Crypto PowerData MCP servers...")
        # Note: Since we're using daemon threads, they will automatically stop
        # when the main process exits. For graceful shutdown, you might want to
        # implement proper shutdown mechanisms in the server code.
        
    def status(self) -> Dict[str, Any]:
        """Get status of all server threads"""
        return {
            "stdio": {
                "running": self.stdio_thread is not None and self.stdio_thread.is_alive(),
                "thread_id": self.stdio_thread.ident if self.stdio_thread else None
            },
            "sse": {
                "running": self.sse_thread is not None and self.sse_thread.is_alive(),
                "thread_id": self.sse_thread.ident if self.sse_thread else None
            },
            "auto": {
                "running": self.auto_thread is not None and self.auto_thread.is_alive(),
                "thread_id": self.auto_thread.ident if self.auto_thread else None
            }
        }


# Global server manager instance
_server_manager = CryptoPowerDataMCPServer()


def get_server_manager() -> CryptoPowerDataMCPServer:
    """Get the global server manager instance"""
    return _server_manager
