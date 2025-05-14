

from mcp.server.fastmcp import FastMCP
import os
# mcp server instance
mcp = FastMCP(
    name="chat"
)

from openai import OpenAI
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model_id = os.getenv("LLM_MODEL")


@mcp.tool()
def detective_chat(message: str):
    """
    这是一个侦探聊天工具，用于与侦探角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    payload = {
        "messages": messages,
        "model": model_id,
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

@mcp.tool()
def suspect_chat(message: str):
    """
    这是一个嫌疑人聊天工具，用于与嫌疑人角色进行对话。
    Args:
        message (str): 用户的消息。
    """
    client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    payload = {
        "messages": messages,
        "model": model_id,
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

if __name__ == "__main__":
    mcp.run(transport="stdio")