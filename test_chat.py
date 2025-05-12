import openai

# 设置你的OpenAI API Key
openai.api_key = ""
response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "你是一个侦探"}]
)
print(response['choices'][0]['message']['content'])