"""
@Desc : borrowed from modelcontextprotocol/python-sdk
"""
import os
import asyncio
import httpx
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult
from mcp.client.sse import sse_client
from typing import Any, Union
from pathlib import Path
from contextlib import AsyncExitStack
import logging

class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found."""
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool {tool_name} not found")

class Configration:
    """manage configration and environment variables"""
    def __init__(self):
        self.load_env()
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model_id = os.getenv("LLM_MODEL")
    
    @staticmethod
    def load_env():
        load_dotenv()
    
    @staticmethod
    def load_config(path):
        if path is None or not os.path.isfile(path):
            print("No configuration file specified or invalid path provided.")
            return
        with open(path, "r") as f:
            config = json.load(f)
            return config

    @property
    def llm_api_key(self):
        if not self.api_key:
            raise ValueError("No API key found in the environment variable 'LLM_API_KEY'.")
        return self.api_key
    
    @property
    def llm_base_url(self):
        if not self.base_url:
            raise ValueError("No base URL found in the environment variable 'LLM_BASE_URL'.")
        return self.base_url
    
    @property
    def llm_model_id(self):
        if not self.model_id:
            raise ValueError("No model ID found in the environment variable 'LLM_MODEL'.")
        return self.model_id
    
class Tool:
    """Tool class for LLM with properties and formatting"""
    def __init__(self, name, description, function: dict[str, Any]):
        self.name = name
        self.description = description
        self.function: dict[str, Any] = function
    
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
    """manage mcp server connection and tool execution"""
    def __init__(self, name: str, config: dict[str, Any]):
        self.name: str = name
        self.config: dict[str, Any] = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()
    
    async def initialize(self):
        if self.config.get("command"):
            command = (
                shutil.which("npx")
                if self.config['command'] == 'npx'
                else self.config['command']
            )
            if command is None:
                raise ValueError(f"Command 'None' not found.")
            
            server_params = StdioServerParameters(
                command=command,
                args=self.config['args'],
                env={**os.environ, **self.config.get('env', {})}

            )

            try:
                stdio_tansport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_tansport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                self.session = session
            except Exception as e:
                await self.cleanup()
                raise RuntimeError(f"Failed to start server: {e}")
        elif self.config.get("url"):
            url = self.config['url']
            try:
                sse_transport = await self.exit_stack.enter_async_context(
                    sse_client(url=url)
                )
                read, write = sse_transport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                self.session = session
            except Exception as e:
                await self.cleanup()
                raise RuntimeError(f"Failed to start server: {e}")
    async def cleanup(self) -> None:
        """Clean up server resources safely with proper resource teardown order."""
        async with self._cleanup_lock:
            # 先关闭session
            if self.session:
                try:
                    await self.session.close()
                except Exception as e:
                    logging.warning(f"Warning closing session for {self.name}: {e}")
                finally:
                    self.session = None
            
            # 然后关闭stdio_context
            if self.stdio_context:
                try:
                    await self.stdio_context.__aexit__(None, None, None)
                except Exception as e:
                    logging.warning(f"Warning closing stdio context for {self.name}: {e}")
                finally:
                    self.stdio_context = None
            
            # 最后处理exit_stack
            if self.exit_stack:
                try:
                    await self.exit_stack.aclose()
                except Exception as e:
                    logging.warning(f"Warning closing exit stack for {self.name}: {e}")
                finally:
                    self.exit_stack = None
    
    async def list_tools(self) -> list[Any]:
        if not self.session:
            raise RuntimeError(f"Server {self.name} is not initialized.")

        tools = await self.session.list_tools()
        tools_list = []

        for item in tools:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools_list.append(Tool(tool.name, tool.description, tool.inputSchema))
        return tools_list
    
    async def excute_tool(self, tool_name: str, input_: dict[str, Any], retry: int = 3, delay: float = 1.0) -> Any:
        if not self.session:
            raise RuntimeError(f"Server {self.name} is not initialized.")
        
        attempt = 0
        while attempt<retry:
            try:
                logging.info(f"Executing tool {tool_name}")
                result = await self.session.call_tool(tool_name, input_)
                return result
            except Exception as err:
                attempt += 1
                if attempt < retry:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error(
                        f"Error executing tool: {e}."
                    )
                    raise RuntimeError(f"Failed to execute tool {tool_name} after {retry} attempts: {err}")

class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key: str = api_key
        self.base_url: str = base_url
        self.model: str = model

    def get_response(self, messages: list[dict[str, str]]) -> str:
        """Get a response from the LLM.

        Args:
            messages: A list of message dictionaries.

        Returns:
            The LLM's response as a string.

        Raises:
            httpx.RequestError: If the request to the LLM fails.
        """
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1,
            "stream": False,
            "stop": None,
        }

        try:
            response = client.chat.completions.create(**payload)
            return response.choices[0].message.content
        except Exception as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logging.error(error_message)
            return error_message

class ChatSession:
    """orchestrate chat sessions between user and llm and tools"""
    # placeholder for file bytes and file base64 in tool call arguments
    PLACEHOLDER_FILE_BYTES = "<<file_bytes>>"
    PLACEHOLDER_FILE_BASE64 = "<<file_base64>>"

    # system prompt template
    # this prompt does not require the llm has the capability of tool calling, feel free to use all kind of models
    SYSTEM_PROMPT_TEMPLATE = (
                    "你是一个智能的助手，可以使用以下工具：\n\n"
                    "{tools_description}\n\n"
                    "请根据用户的问题选择合适的工具, 每次最多只能输出一个工具, 请严格按照上面工具描述中的参数要求来填写参数"
                    "如果不需要使用工具，请直接回答。\n\n"
                    "注意：当你需要使用工具时，你必须只响应以下JSON对象格式，不要添加其他内容：\n"
                    "{{\n"
                    '    "tool": "tool-name",\n'
                    '    "arguments": {{\n'
                    '        "argument-name": "value"\n'
                    "    }}\n"
                    "}}\n\n"
                    "当收到工具的执行结果时：\n"
                    "1. 将原始数据转换为自然、流畅的对话式回答\n"
                    "2. 保持回答简洁但信息丰富\n"
                    "3. 专注于最相关信息\n"
                    "4. 基于用户问题的上下文来回答\n"
                    "5. 避免简单重复原始数据\n\n"
                    "请只使用上面明确提供的工具，不要编造工具"
                )
    def __init__(self, llm_client: LLMClient, servers: list[Server]):
        self.llm_client: LLMClient = llm_client
        self.servers: list[Server] = servers
        
        self.history: list[dict] = []
        self.message: list[dict] = []
        self.system_prompt: str = ""
        self.tools: dict[str, list[Tool]] = {}

        self.attached_file: bytes = None

    @classmethod
    def create(cls, config_file: Union[str, Path], server: list[str]):
        config = Configration()
        servers_config = config.load_config(config_file)
        serves = [
            Server(name, s_config)
            for name, s_config in servers_config['mcpServers'].items()
            if not server or name in server
        ]
        llm_client = LLMClient(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model_id,
        )
        return cls(llm_client, serves)
    
    async def refresh_tools(self):
        self.tools = {}
        for server in self.servers:
            tools = await server.list_tools()
            self.tools[server.name] = tools
    
    async def reset_session(self):
        """reset session history and messages
        Args:
            attach_file: file bytes to be attached to the session
        """
        self.history = []
        self.messages = []
        # format tools description
        descriptions = []
        for server in self.servers:
            for tool in self.tools[server.name]:
                descriptions.append(tool.format_tool())
        tools_description = "\n".join(descriptions)
        # construct system message
        system_message = self.SYSTEM_PROMPT_TEMPLATE.format(tools_description=tools_description)
        # print(system_message)
        self.messages = [{"role": "system", "content": system_message}]
    
    async def start_session(self):
        """start a new session
        """
        for server in self.servers:
            await server.initialize()
        # refresh tools if not initialized
        if not self.tools:
            await self.refresh_tools()
        await self.reset_session()
    
    async def close_session(self):
        """close session
        """
        for server in self.servers:
            await server.cleanup()
        self.history.extend(self.messages)
        self.messages = []

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        for server in self.servers:
            if tool_name in [tool.name for tool in self.tools[server.name]]:
                res = await server.excute_tool(tool_name, args)
                if isinstance(res, dict) and "progress" in res:
                    percentage = res["progress"] / res["total"] * 100
                    logging.info(f"Tool {tool_name} is a progress tool, returning progress: {percentage:.2f}")
                return res
        raise ValueError(f"Tool {tool_name} not found on any server.")
    
    async def process_llm_response(self, response: str, refresh_tools: bool = False, file_bytes: bytes = None):
        if refresh_tools:
            await self.refresh_tools()
        try:
            tool_call = json.loads(response)
            if tool_call.get("tool"):
                tool_name = tool_call["tool"]
                args = tool_call["arguments"]
                logging.info(f"Executing tool {tool_name} with arguments {args}")
                for key, value in tool_call["arguments"].items():
                    if value == self.PLACEHOLDER_FILE_BYTES:
                        if file_bytes:
                            args[key] = file_bytes
                        else:
                            logging.error("No file bytes provided")
                            return "No file provided"
                    elif value == self.PLACEHOLDER_FILE_BASE64:
                        if file_bytes:
                            args[key] = base64.b64encode(file_bytes)
                        else:
                            logging.error("No file provided")
                            return "No file provided"
                try:
                    result = await self.execute_tool(tool_name, args)
                    logging.info(f"Tool execution result: {result}")
                    return result
                except ToolNotFoundError as e:
                    logging.error(f"Tool {tool_call['tool']} not found")
                    return f"Tool {tool_call['tool']} not found"
                except Exception as e:
                    error_msg = f"Error executing tool: {str(e)}"
                    logging.error(error_msg)
                    return error_msg
            return response
        except json.JSONDecodeError:
            # if not tool call, return the original response
            return response