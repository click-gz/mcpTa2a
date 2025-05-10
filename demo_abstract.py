import abc
import json
import logging
from typing import Dict, List, Any, Optional, Protocol


# 定义抽象层
class LLMInterface(Protocol):
    """LLM接口定义，所有LLM实现需遵循此协议"""
    def generate(self, prompt: str, context: List[str]) -> str:
        ...


class ToolInterface(Protocol):
    """工具接口定义，所有工具实现需遵循此协议"""
    def execute(self, name: str, parameters: Dict[str, Any]) -> Any:
        ...


class MCPInterface(abc.ABC):
    """MCP协议接口定义"""

    @abc.abstractmethod
    def send_request(self, model_name: str, prompt: str) -> str:
        """向指定模型发送请求"""
        pass

    @abc.abstractmethod
    def update_context(self, message: str) -> None:
        """更新对话上下文"""
        pass

    @abc.abstractmethod
    def get_context(self) -> List[str]:
        """获取当前对话上下文"""
        pass

    @abc.abstractmethod
    def register_tool(self, tool_name: str, tool: ToolInterface) -> None:
        """注册外部工具"""
        pass

    @abc.abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行已注册的工具"""
        pass


# 具体实现
class OpenAILLM(LLMInterface):
    """OpenAI LLM实现"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 实际应用中初始化OpenAI客户端

    def generate(self, prompt: str, context: List[str]) -> str:
        try:
            # 实际应用中调用OpenAI API
            # 这里简单模拟生成内容
            return f"OpenAI生成内容: {prompt} (上下文长度: {len(context)})"
        except Exception as e:
            logging.error(f"OpenAI LLM生成内容时出错: {e}")
            return ""


class AnthropicLLM(LLMInterface):
    """Anthropic LLM实现"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 实际应用中初始化Anthropic客户端

    def generate(self, prompt: str, context: List[str]) -> str:
        try:
            # 实际应用中调用Anthropic API
            # 这里简单模拟生成内容
            return f"Anthropic生成内容: {prompt} (上下文长度: {len(context)})"
        except Exception as e:
            logging.error(f"Anthropic LLM生成内容时出错: {e}")
            return ""


class WeatherTool(ToolInterface):
    """天气查询工具实现"""
    def execute(self, name: str, parameters: Dict[str, Any]) -> Any:
        try:
            location = parameters.get("location", "北京")
            # 实际应用中调用天气API
            return f"查询结果: {location} 当前天气晴朗，温度25℃"
        except Exception as e:
            logging.error(f"天气工具执行时出错: {e}")
            return ""


class LocalMCP(MCPInterface):
    """本地MCP协议实现"""
    def __init__(self):
        self.context: List[str] = []
        self.models: Dict[str, LLMInterface] = {}
        self.tools: Dict[str, ToolInterface] = {}

    def register_model(self, model_name: str, model: LLMInterface) -> None:
        """注册LLM模型"""
        self.models[model_name] = model

    def send_request(self, model_name: str, prompt: str) -> str:
        """向指定模型发送请求"""
        model = self.models.get(model_name)
        if not model:
            logging.error(f"未找到模型: {model_name}")
            return ""
        try:
            response = model.generate(prompt, self.context)
            self.update_context(f"{model_name}: {response}")
            return response
        except Exception as e:
            logging.error(f"发送请求到模型 {model_name} 时出错: {e}")
            return ""

    def update_context(self, message: str) -> None:
        """更新对话上下文"""
        self.context.append(message)

    def get_context(self) -> List[str]:
        """获取当前对话上下文"""
        return self.context

    def register_tool(self, tool_name: str, tool: ToolInterface) -> None:
        """注册外部工具"""
        self.tools[tool_name] = tool

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行已注册的工具"""
        tool = self.tools.get(tool_name)
        if not tool:
            logging.error(f"未找到工具: {tool_name}")
            return ""
        try:
            return tool.execute(tool_name, parameters)
        except Exception as e:
            logging.error(f"执行工具 {tool_name} 时出错: {e}")
            return ""


# 影视对话生成系统
class FilmDialogueSystem:
    """影视对话生成系统"""
    def __init__(self, mcp_client: MCPInterface):
        self.mcp = mcp_client
        self.dialogue_history: List[Dict[str, str]] = []

    def generate_dialogue(self, scenario: Dict[str, str], num_rounds: int = 1) -> List[Dict[str, str]]:
        """根据剧情场景生成对话，支持多轮对话"""
        for _ in self.dialogue_history:
            self.mcp.update_context(_["line"])

        for _ in range(num_rounds):
            for character, instruction in scenario.items():
                # 构建角色专属提示词
                prompt = f"你是{character}，{instruction}"

                # 通过MCP发送请求
                response = self.mcp.send_request(character, prompt)

                # 简单内容审核过滤（这里简单检查是否包含不良词汇，可根据实际需求完善）
                if self._is_inappropriate(response):
                    response = f"{character}: 我不能说这样的话。"

                # 记录对话结果
                dialogue = {
                    "character": character,
                    "line": response,
                    "context_length": len(self.mcp.get_context())
                }
                self.dialogue_history.append(dialogue)
                self.mcp.update_context(response)

        return self.dialogue_history

    def _is_inappropriate(self, text: str) -> bool:
        # 简单的不良词汇检查，可扩展为更复杂的审核逻辑
        inappropriate_words = ["暴力", "辱骂"]
        for word in inappropriate_words:
            if word in text:
                return True
        return False


# 演示代码
if __name__ == "__main__":
    # 配置日志记录
    logging.basicConfig(level=logging.INFO)

    # 初始化MCP客户端
    mcp_client = LocalMCP()

    # 注册模型（实际应用中替换为真实的LLM实现）
    mcp_client.register_model("侦探", AnthropicLLM(api_key="your_api_key"))
    mcp_client.register_model("嫌疑人", OpenAILLM(api_key="your_api_key"))

    # 注册工具
    mcp_client.register_tool("weather", WeatherTool())

    # 初始化影视对话系统
    system = FilmDialogueSystem(mcp_client)

    # 定义剧情场景
    scenario = {
        "侦探": "质问嫌疑人昨晚的行踪",
        "嫌疑人": "试图隐瞒关键信息"
    }

    # 生成对话，设置为3轮对话
    dialogue_result = system.generate_dialogue(scenario, num_rounds=3)

    # 打印结果
    print("=== 生成的对话 ===")
    for dialogue in dialogue_result:
        print(f"{dialogue['character']}: {dialogue['line']}")

    # 演示工具调用
    weather_info = mcp_client.execute_tool("weather", {"location": "伦敦"})
    print("\n=== 工具调用示例 ===")
    print(f"工具调用结果: {weather_info}")

    # 保存对话记录
    with open("dialogue_output.json", "w", encoding="utf-8") as f:
        json.dump(dialogue_result, f, ensure_ascii=False, indent=2)