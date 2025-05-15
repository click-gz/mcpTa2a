from mcp.server.fastmcp import FastMCP

# mcp server instance
mcp = FastMCP(
    name="chat"
)

# 新版本（>=1.0.0）
from openai import OpenAI


@mcp.tool()
def detective_chat(message: str):
    """
    这是一个侦探聊天工具，用于与侦探角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    # 新版本：创建客户端实例
    client = OpenAI(api_key="", base_url="https://qianfan.baidubce.com/v2")
    response = client.chat.completions.create(
        model="ernie-4.5-turbo-32k",  # 使用标准的OpenAI模型名称
        messages=[{"role": "user", "content": f"{message}"}]
    )
    # print(response.choices[0].message.content)
    return response.choices[0].message.content

@mcp.tool()
def suspect_chat(message: str):
    """
    这是一个嫌疑人聊天工具，用于与嫌疑人角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    client = OpenAI(api_key="", base_url="https://qianfan.baidubce.com/v2")
    response = client.chat.completions.create(
        model="ernie-4.5-turbo-32k",  # 使用标准的OpenAI模型名称
        messages=[{"role": "user", "content": f"{message}"}]
    )
    # print(response.choices[0].message.content)
    return response.choices[0].message.content

if __name__ == "__main__":
    mcp.run(transport="stdio")