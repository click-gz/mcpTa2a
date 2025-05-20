from openai import OpenAI

class AgentTool:
    def __init__(self, content: str):
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=''
        )
        self.history = [{
            "role": "assistant",
            "content": content
        }]
    
    def updata_history(self, messages):
        self.history.append({
            "role": "assistant",
            "content": messages
        })
    def chat(self, messages):
        self.history.append({
            "role": "user",
            "content": messages
        })
        response = self.client.chat.completions.create(
            model="ernie-4.5-turbo-32k", 
            messages=self.history, 
            temperature=0.8, 
            top_p=0.8,
            extra_body={ 
                "penalty_score":1, 
                "web_search":{
                    "enable": False,
                    "enable_trace": False
                }
            }
        )
        self.history.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })
        return response.choices[0].message.content