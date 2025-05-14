

from mcp.server.fastmcp import FastMCP

# mcp server instance
mcp = FastMCP(
    name="chat"
)

from g4f.client import Client
import openai

# 设置你的OpenAI API Key
openai.api_key = ""
@mcp.tool()
def detective_chat(message: str):
    """
    这是一个侦探聊天工具，用于与侦探角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"{message}"}]
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

@mcp.tool()
def suspect_chat(message: str):
    """
    这是一个嫌疑人聊天工具，用于与嫌疑人角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"{message}"}]
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

if __name__ == "__main__":
    mcp.run(transport="stdio")