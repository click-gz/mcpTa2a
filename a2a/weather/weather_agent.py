from python_a2a import A2AServer, A2AClient, AgentCard, AgentSkill, TaskStatus, TaskState, run_server
from python_a2a import skill, agent # 从库中导入装饰器


# 通常 A2A 服务器会阻塞主线程
import asyncio
import threading
import socket
import time # 确保导入 time 模块
import requests
import json
from openai import OpenAI

def ask(prompt: str, system_prompt: str = None) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url='https://qianfan.baidubce.com/v2',
        api_key=''
    )
    message = [
        {"role": "system", "content": system_prompt} if system_prompt else {},
        {"role": "user", "content": prompt}
    ]
    yiyan_generator = client.chat.completions.create(
        model="ernie-4.5-turbo-vl-32k-preview", 
        messages=message, 
        temperature=0.8, 
        top_p=0.8,
        extra_body={ 
            "penalty_score":1
        }
    )
    # print(yiyan_generator.choices[0].message.content)
    return yiyan_generator.choices[0].message.content



# ask("你好，天气助手！", system_prompt="你是一个智能天气助手，能够提供天气查询和穿衣建议。")
# exit()
def find_available_port(start_port=8000, max_tries=100):
    """查找一个可用端口"""
    for port_num in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port_num))
            return port_num
        except OSError:
            continue
    raise IOError("No free ports found")

SERVER_PORT = find_available_port()
SERVER_URL = f"http://localhost:{SERVER_PORT}"
print(f"天气助手 Agent 将运行在: {SERVER_URL}")

@agent("weather_agent", 
        description="天气助手 Agent，同时提供穿衣建议和天气查询功能",
        version="1.0.0",
        url=SERVER_URL)
class WeatherAgent(A2AServer):
    def __init__(self, mcp_url: str = "http://localhost:7001"):
        self.mcp_url = mcp_url
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=''
        )
        print(f"🛠️ MyToolAgent 初始化完成，将连接到 MCP 服务: {self.mcp_url}")
        agent_card = AgentCard(
            name="weather_agent",
            description="提供天气查询和穿衣建议的智能助手",
            version="1.0.0",
            url=SERVER_URL,
            skills=[
                AgentSkill(
                    name="get_weather",
                    description="查询指定城市的天气情况",
                    examples=["查询北京的天气", "上海今天的天气如何？"],
                ),
                AgentSkill(
                    name="get_clothing_advice",
                    description="根据天气情况提供穿衣建议",
                    examples=["今天天气晴朗，25度，我该怎么穿？", "零下5度，有雪，给点穿衣建议。"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
        self.prompt = "你是一个智能天气助手，能够提供天气查询和穿衣建议。"
        self.system_prompt = (
            "你是一个任务分析助手。你的任务是分析用户的输入，判断其意图并提取相关参数。"
            "请根据用户的文本，判断意图是 'query_weather' (查询天气), 'get_dressing_advice' (获取穿衣建议), 或者 'unknown' (未知意图)。"
            "如果意图是 'query_weather'，请提取 'location' 参数。"
            "如果意图是 'get_dressing_advice'，请提取 'weather_description' 参数。如果没有直接的天气描述，可以将 'weather_description' 设为 null。"
            "请以JSON格式返回结果，例如：{\"intent\": \"query_weather\", \"parameters\": {\"location\": \"北京\"}} 或者 "
            "{\"intent\": \"get_dressing_advice\", \"parameters\": {\"weather_description\": \"晴朗，25度\"}} 或者 "
            "{\"intent\": \"unknown\", \"parameters\": {}}"
            "如果用户只是打招呼或者聊天，也视为 'unknown'。确保返回的是合法的JSON，不要在JSON前后添加任何其他字符或markdown标记。"
        )
    def _get_ernie_response(self, user_query, system_prompt="你是一个乐于助人的AI助手。"):
        """调用 Ernie 大模型获取回复"""
        try:
            print(f"🧠 正在向 Ernie 发送请求: '{user_query}'")
            message = [
                {"role": "system", "content": self.system_prompt} ,
                {"role": "user", "content": user_query}
            ]
            yiyan_generator = self.client.chat.completions.create(
                model="ernie-4.5-turbo-vl-32k-preview", 
                messages=message, 
                temperature=0.8, 
                top_p=0.8,
                extra_body={ 
                    "penalty_score":1
                }
            )
            response_content = yiyan_generator.choices[0].message.content
            print(f"💡 Ernie 回复: '{response_content}'")
            return response_content
        except Exception as e:
            error_msg = f"调用 Ernie API 失败: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    def _call_mcp_tool(self, tool_name, params):
        """一个辅助方法，用于调用 MCP 工具"""
        if not self.mcp_url:
            return "错误：MCP 服务地址未配置。"
        
        tool_endpoint = f"{self.mcp_url}/tools/{tool_name}"
        try:
            print(f"📞 正在调用 MCP 工具: {tool_endpoint}，参数: {params}")
            response = requests.post(tool_endpoint, json=params, timeout=10)
            response.raise_for_status() # 如果 HTTP 状态码是 4xx 或 5xx，则抛出异常
            
            tool_response_json = response.json()
            print(f"工具响应JSON: {tool_response_json}")

            # 从 MCP 响应中提取文本内容
            # MCP 响应通常在 content -> parts -> text
            if tool_response_json.get("content"):
                parts = tool_response_json["content"]
                if isinstance(parts, list) and len(parts) > 0 and "text" in parts[0]:
                    return parts[0]["text"]
            return "工具成功执行，但未找到标准文本输出。"

        except requests.exceptions.RequestException as e:
            error_msg = f"调用 MCP 工具 {tool_name} 失败: {e}"
            print(f"❌ {error_msg}")
            return error_msg
        except Exception as e_json: # requests.post 成功，但响应不是期望的json或json结构不对
            error_msg = f"解析 MCP 工具 {tool_name} 响应失败: {e_json}"
            print(f"❌ {error_msg}")
            return error_msg

    @skill("get_weather",
           description="查询指定城市的天气情况, 输入参数为城市名称 'location' ",
    )
    def get_weather(self, location: str) -> str:
        if not location or not isinstance(location, str):
            return "请输入有效的地点名称。"
        prompt = f"请告诉我{location}今天的天气怎么样？"
        weather_info = ask(prompt, system_prompt=self.prompt)
        return weather_info
    
    @skill(
        name="GetDressingAdvice",
        description="根据天气描述提供穿衣建议。输入参数 'weather_description' (字符串)。"
    )
    def get_dressing_advice(self, weather_description: str):
        if not weather_description or not isinstance(weather_description, str):
            return "请输入有效的天气描述。"
        prompt = f"今天的天气是'{weather_description}'，请给我一些穿衣建议。"
        advice = ask(prompt, system_prompt=self.prompt)
        return advice

    def handle_task(self, task):

        message_data = task.message or {}
        content = message_data.get("content", {})
        # 对于SKILL:调用，我们保留原始大小写，对于自然语言则转小写
        text = content.get("text", "") if isinstance(content, dict) else ""

        response_text = "抱歉，我不太理解你的意思。你可以问我某个地方的‘天气’，或者根据天气情况获取‘穿衣’建议。"
        print(f"处理任务: {task.id}, 内容: {text}")
        task_completed = False # Flag to indicate if the task was successfully processed by a skill
        # task.artifacts = [{"parts": [{"type": "text", "text": "请输入你的问题。"}]}]
        # task.status = TaskStatus(state=TaskState.INPUT_REQUIRED, message={"role": "agent", "content": {"type": "text", "text": "请输入你的问题。"}})
        # return task
        try:
            if not text.strip():
                task.artifacts = [{"parts": [{"type": "text", "text": "请输入你的问题。"}]}]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED, message={"role": "agent", "content": {"type": "text", "text": "请输入你的问题。"}})
                return task

            res = self._get_ernie_response(text)
            print(f"Ernie 回复: {res}")
            res = res.replace("```json", "").replace("```", "").strip() # 去除可能的markdown代码块标记
            intent = json.loads(res).get("intent", "unknown")
            params = json.loads(res).get("parameters", "{}")
            # exit()
            task_completed = False

            if intent == "query_weather":
                location = params.get("location")
                if location and isinstance(location, str): # 增加类型检查
                    response_text = self._call_mcp_tool("get_weather", params)
                    task_completed = True
                else:
                    response_text = "你想查询哪个城市的天气呢？（我没能从您的话中找到城市名称）"
            elif intent == "get_dressing_advice":
                weather_desc = params.get("weather_description")
                if weather_desc and isinstance(weather_desc, str): # 增加类型检查
                    response_text = self.get_dressing_advice(weather_description=weather_desc)
                    task_completed = True
                else: # 未能提取到天气描述
                    response_text = "请先告诉我今天的天气怎么样（比如'晴天25度'），或者先问我天气，我才能给你穿衣建议。"
            elif intent == "unknown":
                original_user_text = params.get("original_text", text)
                response_text = ask(original_user_text, system_prompt="你是一个通用的AI助手，请尽力回答用户的问题或进行聊天。")
                task_completed = True
            else: 
                response_text = f"我暂时还不支持处理 '{intent}' 这种类型的请求。"
                task_completed = True # 认为已经响应了，即使是说不支持

            if task_completed:
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else: # 如果 task_completed 为 False，通常意味着需要更多输入
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED, message={"role": "agent", "content": {"type": "text", "text": response_text}})
        
        except Exception as e:
            print(f"处理任务时发生严重错误: {e}")
            import traceback
            traceback.print_exc() # 打印详细的错误堆栈
            error_message = "抱歉，我在处理你的请求时遇到了一个内部错误。"
            task.artifacts = [{"parts": [{"type": "text", "text": error_message}]}]
            task.status = TaskStatus(state=TaskState.FAILED)
            
        return task

# # 创建 Agent 实例
# weather_agent_instance = WeatherAgent()

# # ---- 在后台线程中运行 A2A 服务器 ----
# def run_a2a_server_in_background(agent_instance, host="0.0.0.0", port_to_run=SERVER_PORT):
#     print(f"后台线程：尝试在 {host}:{port_to_run} 启动服务器...")
#     try:
#         run_server(agent_instance, host=host, port=port_to_run)
#         print(f"后台线程：服务器已在 {host}:{port_to_run} 停止。")
#     except Exception as e:
#         print(f"后台线程：启动服务器失败或服务器停止时出错: {e}")

# server_thread = threading.Thread(
#     target=run_a2a_server_in_background, 
#     args=(weather_agent_instance, "localhost", SERVER_PORT), 
#     daemon=True
# )
# server_thread.start()

# print("等待服务器启动...")
# time.sleep(3) 

# print("服务器应该已经在后台启动了。")


# import re # 确保导入 re 模块，handle_task 中可能会用到
# import json

# from python_a2a import Task, Message, TextContent, MessageRole, TaskState # TaskState 用于检查响应状态
# import uuid # 用于生成唯一的 Task ID

# # 确保之前的服务器启动代码已经运行完毕，并且服务器正在后台运行
# if not server_thread.is_alive():
#     print("错误：服务器线程未运行。请确保上一个单元格已成功执行且服务器已启动。")
# else:
#     print(f"服务器应该在 {SERVER_URL} 运行。现在创建客户端进行测试...")
    
#     # 创建 A2AClient
#     a2a_client = A2AClient(SERVER_URL)
    
#     print("\n--- 测试通过 ask() 精确调用 Skill (期望字符串回复) ---")
#     try:
#         # 准备调用 GetCurrentWeather Skill
#         location_to_query = "广州"
#         # 构建符合约定的文本: SKILL:SkillName PARAMS:{"key": "value"}
#         skill_request_text_weather = f"SKILL:get_weather PARAMS:{json.dumps({'location': location_to_query})}"
        
#         print(f"\n[用户] (发送精确调用请求) {skill_request_text_weather}")
#         weather_response_text = a2a_client.ask(skill_request_text_weather) # ask() 返回字符串
#         print(f"[Agent] {weather_response_text}")

#     except Exception as e:
#         print(f"通过 ask() 方法与 Agent 通信失败: {e}")
#         print("请检查服务器是否仍在运行，以及 SERVER_URL 是否正确。")


if __name__ == "__main__":

    my_agent = WeatherAgent()
    # A2A 代理的配置
    AGENT_PORT = 7000 # A2A 代理监听的端口
    MCP_SERVER_URL = "http://localhost:7001" # 我们之前启动的 MCP 工具服务的地址
    print(f"🚀 My A2A Agent 即将启动于 http://localhost:{AGENT_PORT}")
    print(f"🔗 它将连接到 MCP 服务于 {MCP_SERVER_URL}")
    
    # run_server 会启动一个 Flask (默认) 或 FastAPI 服务器来托管 A2A 代理
    # 这部分代码也会阻塞
    run_server(my_agent, host="0.0.0.0", port=AGENT_PORT)