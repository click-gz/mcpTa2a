from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from typing import List, Dict
import random
import json

mcp = FastMCP(name="werewolf")

class Agent:
    def __init__(self, player_id: str, role: str):
        self.id = player_id
        self.role = role
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key='your-api-key'
        )
        self.memory = []
        
    def think(self, game_state: Dict, prompt: str) -> str:
        """Agent思考并做出决策"""
        context = f"""
        你是一个狼人杀游戏中的{self.role}。
        你的玩家ID是{self.id}。
        当前游戏状态：{json.dumps(game_state, ensure_ascii=False)}
        历史记忆：{json.dumps(self.memory, ensure_ascii=False)}
        
        请根据以上信息，对以下情况做出决策：
        {prompt}
        """
        
        response = self.client.chat.completions.create(
            model="ernie-4.5-turbo-32k",
            messages=[{"role": "user", "content": context}],
            temperature=0.8
        )
        
        decision = response.choices[0].message.content
        self.memory.append({"prompt": prompt, "decision": decision})
        return decision

@mcp.tool()
def start_a2a_game(player_count: int = 8):
    """开始A2A狼人杀游戏"""
    # 初始化游戏状态
    game_state = {
        "phase": "night",
        "players": {},
        "alive_players": [],
        "agents": {},
        "current_round": 0
    }
    
    # 分配角色
    roles = ["狼人"] * 3 + ["预言家", "女巫", "平民", "平民", "平民"]
    player_ids = [f"player_{i+1}" for i in range(player_count)]
    
    random.shuffle(roles)
    werewolves = [player_ids[i] for i in range(player_count) if roles[i] == "狼人"]
    
    # 创建所有Agent
    for i in range(player_count):
        player_id = f"player_{i+1}"
        role = roles[i]
        agent = Agent(player_id=player_id, role=role)
        
        game_state["players"][player_id] = {
            "id": player_id,
            "role": role,
            "is_alive": True
        }
        game_state["agents"][player_id] = agent
        game_state["alive_players"].append(player_id)
    
    # 让所有Agent开始游戏
    game_prompt = f"""
    游戏开始！共有{player_count}名玩家。
    你的角色是{role}。
    其他玩家ID：{', '.join(player_ids)}。
    狼人玩家：{', '.join(werewolves)}。
    
    请开始游戏，根据你的角色做出相应的行动。
    如果是狼人，请与其他狼人交流并选择击杀目标。
    如果是预言家，请选择查验目标。
    如果是女巫，请决定是否使用解药或毒药。
    如果是平民，请观察局势并准备发言。
    """
    
    # 让所有Agent同时开始行动
    actions = []
    for player_id in game_state["alive_players"]:
        agent = game_state["agents"][player_id]
        action = agent.think(game_state, game_prompt)
        actions.append(f"玩家{player_id}（{game_state['players'][player_id]['role']}）行动：{action}")
    
    return "\n".join(actions)

@mcp.tool()
def continue_a2a_game(game_state: Dict):
    """继续A2A游戏"""
    # 让所有Agent继续游戏
    game_prompt = f"""
    当前游戏阶段：{game_state['phase']}
    存活玩家：{', '.join(game_state['alive_players'])}
    当前回合：{game_state['current_round']}
    
    请根据当前局势继续游戏。
    如果是夜晚，请执行你的夜晚行动。
    如果是白天，请发表你的看法并参与投票。
    """
    
    # 让所有Agent同时行动
    actions = []
    for player_id in game_state["alive_players"]:
        agent = game_state["agents"][player_id]
        action = agent.think(game_state, game_prompt)
        actions.append(f"玩家{player_id}（{game_state['players'][player_id]['role']}）行动：{action}")
    
    return "\n".join(actions)

# 开始游戏
result = start_a2a_game(8)
print(result)

# 继续游戏
result = continue_a2a_game(game_state)
print(result)