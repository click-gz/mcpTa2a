import os
import json

import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult
from contextlib import AsyncExitStack

class Tool:
    """ 工具类，返回供llm查看的解释 """
    def __init__(self, name, description, function):
        self.name = name
        self.description = description
        self.function = function
    
    def format_tool(self):
        args_desc = []
        if "properties" in self.function:
            for param_name, param_info in self.function["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.function.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)
                
        return f"""
            "name": {self.name},
            "description": {self.description},
            "arguments": {chr(10).join(args_desc)}
        """

class Server:
    """ 管理所有服务，工具使用 """
    def __init__(self, name, config):
        self.name = name
        self.config = config

    def initialize(self):
        server_params = StdioServerParameters(
            command=self.config['command'],
            args=self.config['args'],
            env={**os.environ, **self.config.get('env', {})}
        )
        try:
            with stdio_client(server_params) as read, write:
                with ClientSession(read, write) as session:
                    session.initialize()
                    self.session = session
        except Exception as e:
            raise RuntimeError(f"Failed to start server: {e}")

    async def cleanup(self):
        await self.session.close()
        
        
