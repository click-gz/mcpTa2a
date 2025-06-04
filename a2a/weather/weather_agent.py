from python_a2a import A2AServer, A2AClient, AgentCard, AgentSkill, TaskStatus, TaskState, run_server
from python_a2a import skill, agent # 从库中导入装饰器


# 通常 A2A 服务器会阻塞主线程
import asyncio
import threading
import socket
import time # 确保导入 time 模块

def ask(prompt: str, system_prompt: str = None) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url='https://qianfan.baidubce.com/v2',
        api_key='bce-v3/ALTAK-MNO7ueFojOinVGULYIgBA/978d318585fad146fc72de6bfe44cac87dd82ff0'
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
            # 1. 检查是否为约定的 SKILL 调用格式
            if text.startswith("SKILL:"):
                try:
                    # 解析格式: SKILL:SkillName PARAMS:{"key": "value"}
                    parts = text.split(" PARAMS:", 1)
                    skill_name_part = parts[0][len("SKILL:"):]
                    params_json_str = parts[1] if len(parts) > 1 else "{}"
                    params = json.loads(params_json_str)

                    if skill_name_part == "get_weather":
                        location = params.get("location")
                        if location and isinstance(location, str):
                            response_text = self._call_mcp_tool("get_weather", {"location": "北京"}) # 测试 MCP 工具调用
                            task_completed = True
                        else:
                            response_text = "错误：调用 get_weather 时缺少 'location' 参数或参数类型不正确。"
                            task_completed = False # Indicate failure
                    elif skill_name_part == "get_clothing_advice":
                        weather_desc = params.get("weather_description")
                        if weather_desc and isinstance(weather_desc, str):
                            response_text = self.get_dressing_advice(weather_description=weather_desc)
                            task_completed = True
                        else:
                            response_text = "错误：调用 weather_description 时缺少 'weather_description' 参数或参数类型不正确。"
                            task_completed = False # Indicate failure
                    else:
                        response_text = f"错误：未知的技能名称 '{skill_name_part}'。"
                        task_completed = False # Indicate failure
                    
                    if task_completed:
                        task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                        task.status = TaskStatus(state=TaskState.COMPLETED)
                    else: # Skill call failed (e.g. wrong params, unknown skill)
                        task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                        task.status = TaskStatus(state=TaskState.FAILED, message={"role": "agent", "content": {"type": "text", "text": response_text}})
                    return task 
                except json.JSONDecodeError:
                    response_text = "错误：解析 SKILL 调用中的 PARAMS 参数失败，非法的JSON格式。"
                    task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                    task.status = TaskStatus(state=TaskState.FAILED)
                    return task
                except Exception as e: # Other errors during SKILL processing
                    response_text = f"错误：处理 SKILL 调用时出错 - {str(e)}"
                    task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                    task.status = TaskStatus(state=TaskState.FAILED)
                    return task

            # 2. 如果不是 SKILL 调用，则进行原来的自然语言关键词匹配
            text_lower = text.lower() # 转小写进行关键词匹配
            if "天气" in text_lower:
                location = None
                # 尝试从 task.message.parameters 获取 (如果 client 能以某种方式设置它)
                if task.message and hasattr(task.message, 'parameters') and task.message.parameters:
                    location = task.message.parameters.get("location")
                
                if not location: # 如果 parameters 中没有，尝试简单文本提取
                    if "北京" in text_lower: location = "北京"
                    elif "上海" in text_lower: location = "上海"
                    # 可以添加更多城市，或依赖后续的智能意图识别

                if location:
                    response_text = self.get_current_weather(location=location)
                    task_completed = True
                else:
                    response_text = "请告诉我你具体想查询哪个城市的天气？例如：‘北京天气怎么样？’"
            
            elif "穿衣" in text_lower or "怎么穿" in text_lower or "建议" in text_lower:
                weather_description = None
                if task.message and hasattr(task.message, 'parameters') and task.message.parameters:
                    weather_description = task.message.parameters.get("weather_description")
                
                if not weather_description and text_lower: # 尝试从文本中提取天气描述
                    # 这是一个非常粗略的提取，实际应用需要更复杂的NLP逻辑
                    # 例如，用户可能说："今天天气晴朗，25度，我应该怎么穿？"
                    # 我们需要提取 "晴朗，25度" 作为 weather_description
                    # 这里仅作概念演示，实际提取可能需要更复杂的正则或NLP
                    if "天气是" in text_lower:
                         match = re.search(r"天气是([^，。？！]+)", text_lower)
                         if match: weather_description = match.group(1).strip()
                    elif "今天" in text_lower and ("度" in text_lower or "晴" in text_lower or "雨" in text_lower): # 简单启发式
                        # 假设天气描述在“今天”之后，在“怎么穿”等词之前
                        potential_desc_match = re.search(r"今天([^，。？！]+)(?:，)?(?:我该怎么穿|有啥建议)", text_lower)
                        if potential_desc_match:
                             weather_description = potential_desc_match.group(1).strip()


                if weather_description:
                    response_text = self.get_dressing_advice(weather_description=weather_description)
                    task_completed = True
                else:
                    response_text = "请先告诉我今天的天气怎么样（例如：'晴朗，25度'），我才能给你穿衣建议。"
            
            # 根据处理结果设置 task 状态
            if task_completed:
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else: # 没有匹配到任何意图，或者意图匹配但缺少信息
                # 如果用户有输入文本但未被处理，可以考虑让 Ernie 通用回答
                if text: 
                     current_response_text = ask_ernie(text, system_prompt="你是一个通用的AI助手。")
                     task.artifacts = [{"parts": [{"type": "text", "text": current_response_text}]}]
                     task.status = TaskStatus(state=TaskState.COMPLETED) # 算是处理了
                else: # 没有文本输入
                    task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}] # 使用默认的抱歉消息
                    task.status = TaskStatus(state=TaskState.INPUT_REQUIRED, message={"role": "agent", "content": {"type": "text", "text": response_text}})
        
        except Exception as e:
            print(f"处理任务时发生未捕获的错误: {e}")
            import traceback
            traceback.print_exc()
            error_message = f"抱歉，处理你的请求时遇到了一个意外的内部错误: {str(e)}"
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