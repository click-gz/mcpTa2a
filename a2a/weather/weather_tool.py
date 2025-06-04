from python_a2a.mcp import FastMCP, create_fastapi_app
import uvicorn
from datetime import datetime
import json, time
import requests

mcp = FastMCP(
    name = "WeatherAgent",
    description = "weather tool",
    version = "0.1",
)

@mcp.tool(
    name="get_weather",
    description="获取指定地点的当前天气信息。"
)
def get_weather(location: str) -> str:
    """
    获取指定地点的当前天气信息。
    """
    # 模拟获取天气信息

    key = "794ed5ee2784d94d6dfaffe0a2c6372a"
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={key}&units=metric&lang=zh_cn"
        response = requests.get(url)
        data = response.json()
        print(data)
        if data.get("cod") == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"当前{location}的天气是{weather}，温度{temp}°C。"
        else:   
            return f"获取{location}天气，天气是晴朗"
    except Exception as e:
        return f"获取{location}天气时发生错误：{e}"


if __name__ == "__main__":
    port = 7001 # 指定服务端口
    print(f"🚀 My Utility MCP 服务即将启动于 http://localhost:{port}")
    
    # create_fastapi_app 会将 FastMCP 实例转换为一个 FastAPI 应用
    app = create_fastapi_app(mcp)
    
    # 使用 uvicorn 运行 FastAPI 应用
    # 这部分代码会阻塞，直到服务停止 (例如按 Ctrl+C)
    uvicorn.run(app, host="0.0.0.0", port=port)
    