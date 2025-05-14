"""
@Desc    :   simple demo for mcp
"""
# -*-coding:utf-8 -*-

import asyncio
from client import ChatSession
import argparse
import pathlib
from mcp.types import CallToolResult
import base64
import uuid

def print_red(text):
    """print text in red color"""
    print(f"\033[91m{text}\033[0m")

def print_green(text):
    """print text in green color"""
    print(f"\033[92m{text}\033[0m")

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="servers_config.json", help="config file path")
    parser.add_argument("--servers", nargs="*", help="servers to connect")
    parser.add_argument("-f", "--file", type=str, help="file path")
    return parser.parse_args()

async def main():
    args = get_args()
    print(f"config: {args.config}")
    if not pathlib.Path(args.config).exists():
        print(f"config file {args.config} not found")
        return
    chat_session = ChatSession.create(args.config, args.servers)
    await chat_session.start_session()
    while True:
        await chat_session.reset_session()
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        file_bytes = None
        if args.file:
            file_path = pathlib.Path(args.file)
            file_bytes = file_path.read_bytes()
            user_prompt = f"""{user_input}

文件名为: {file_path.name}, 文件类型为: {file_path.suffix}

**注意：在调用工具时如果需要使用图片或音频,请使用"<<file_bytes>>"来填充需要文件的原始内容的参数，用<<file_base64>>来填充需要文件的base64编码内容的参数**"""
        else:
            user_prompt = user_input

        chat_session.messages.append({"role": "user", "content": user_prompt})
        response = chat_session.llm_client.get_response(chat_session.messages)
        chat_session.messages.append({"role": "assistant", "content": response})

        result = await chat_session.process_llm_response(response, file_bytes=file_bytes)
        print("result: ", response,result)
        # 使用循环处理多轮工具调用
        while isinstance(result, CallToolResult):
            print("call tool")
            # 处理工具调用结果
            tool_results = []
            for item in result.content:
                if item.type == "image":
                    file_name = f"image_{uuid.uuid4()}.jpg"
                    with open(file_name, "wb") as f:
                        f.write(base64.b64decode(item.data))
                    print_green(f"assistant: image is saved to {file_name}")
                    tool_results.append(f"图片已保存到 {file_name}")
                elif item.type == "text":
                    tool_results.append(item.text)
            
            # 将工具调用结果添加到对话历史
            chat_session.messages.append({
                "role": "user",
                "content": "tool执行结果:\n" + "\n".join(tool_results)
            })
            print("user: " + "工具执行结果:\n" + "\n".join(tool_results))
            
            # 获取新的响应
            response = chat_session.llm_client.get_response(chat_session.messages)
            chat_session.messages.append({"role": "assistant", "content": response})
            
            # 处理新的响应
            result = await chat_session.process_llm_response(response, file_bytes=file_bytes)
            print("result: ", result)
        # 输出最终答案
        print_green(f"assistant: {response}")
    await chat_session.close_session()

if __name__ == "__main__":
    asyncio.run(main())
