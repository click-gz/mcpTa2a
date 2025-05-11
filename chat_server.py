

from mcp.server.fastmcp import FastMCP

# mcp server instance
mcp = FastMCP(
    name="chat"
)

from g4f.client import Client

@mcp.tool()
def detective_chat(message: str):
    """
    这是一个侦探聊天工具，用于与侦探角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"{message}"}],
        web_search=False
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
    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"{message}"}],
        web_search=False
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

if __name__ == "__main__":
    mcp.run(transport="stdio")