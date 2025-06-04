from python_a2a import A2AClient, Message, TextContent, MessageRole

# 创建一个客户端来与我们的智能体交流
client = A2AClient("http://localhost:7000/a2a")

# 发送消息
message = Message(
    content=TextContent(text="告诉我北京的天气"),
    role=MessageRole.USER
)
response = client.send_message(message)

# 打印响应
print(f"Agent says: {response.content.text}")