from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
import json
from datetime import datetime

# 创建MCP服务器实例
mcp = FastMCP(name="werewolf")

# 消息类
@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    type: str
    timestamp: int

# 记忆类
class Memory:
    def __init__(self):
        self.game_history: List[Dict] = []
        self.player_actions: Dict[str, List[Dict]] = {}
        self.role_info: Dict[str, str] = {}
        self.strategy_history: List[Dict] = []

    def add_game_event(self, event: Dict):
        self.game_history.append(event)

    def add_player_action(self, player_id: str, action: Dict):
        if player_id not in self.player_actions:
            self.player_actions[player_id] = []
        self.player_actions[player_id].append(action)

# Agent类
class Agent:
    def __init__(self, player_id: str, role: str):
        self.id = player_id
        self.role = role
        self.memory = Memory()
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key='your-api-key'
        )
        
    def think(self, game_state: Dict, prompt: str) -> str:
        """Agent思考并做出决策"""
        context = f"""
        你是一个狼人杀游戏中的{self.role}。
        你的玩家ID是{self.id}。
        当前游戏状态：{json.dumps(game_state, ensure_ascii=False)}
        历史记忆：{json.dumps(self.memory.game_history, ensure_ascii=False)}
        
        请根据以上信息，对以下情况做出决策：
        {prompt}
        """
        
        response = self.client.chat.completions.create(
            model="ernie-4.5-turbo-32k",
            messages=[{"role": "user", "content": context}],
            temperature=0.8
        )
        
        decision = response.choices[0].message.content
        self.memory.add_game_event({
            "timestamp": datetime.now().timestamp(),
            "prompt": prompt,
            "decision": decision
        })
        return decision

# 游戏状态类
class GameState:
    def __init__(self):
        self.phase: str = "init"
        self.players: Dict[str, Dict] = {}
        self.alive_players: List[str] = []
        self.agents: Dict[str, Agent] = {}
        self.history: List[Dict] = []
        self.current_round: int = 0

# 全局游戏状态
game_state = GameState()

@mcp.tool()
def start_game(player_count: int = 8):
    """开始新游戏"""
    global game_state
    game_state = GameState()
    
    # 分配角色
    roles = ["狼人"] * 3 + ["预言家", "女巫", "平民", "平民", "平民"]
    player_ids = [f"player_{i+1}" for i in range(player_count)]
    
    random.shuffle(roles)
    werewolves = [player_ids[i] for i in range(player_count) if roles[i] == "狼人"]
    
    # 初始化玩家和Agent
    for i in range(player_count):
        player_id = f"player_{i+1}"
        role = roles[i]
        
        # 创建Agent
        agent = Agent(player_id=player_id, role=role)
        
        game_state.players[player_id] = {
            "id": player_id,
            "role": role,
            "is_alive": True
        }
        game_state.agents[player_id] = agent
        game_state.alive_players.append(player_id)
    
    game_state.phase = "night"
    return f"游戏开始！共有{player_count}名玩家，角色已分配完成，狼人：{', '.join(werewolves)}"

@mcp.tool()
def night_phase():
    """夜晚阶段"""
    if game_state.phase != "night":
        return "现在不是夜晚阶段"
    
    night_actions = []
    
    # 狼人行动
    werewolves = [p for p in game_state.alive_players 
                 if game_state.players[p]["role"] == "狼人"]
    
    # 狼人之间进行秘密交流
    werewolf_chat = []
    for werewolf in werewolves:
        agent = game_state.agents[werewolf]
        decision = agent.think(
            game_state.__dict__,
            "作为狼人，请与其他狼人交流并选择要击杀的目标。"
        )
        werewolf_chat.append(f"狼人{werewolf}：{decision}")
    
    # 狼人统一行动
    target = game_state.agents[werewolves[0]].think(
        game_state.__dict__,
        f"基于狼人之间的交流：{json.dumps(werewolf_chat, ensure_ascii=False)}，请选择最终要击杀的目标。"
    )
    night_actions.append(f"狼人选择击杀：{target}")
    
    # 预言家行动
    seers = [p for p in game_state.alive_players 
            if game_state.players[p]["role"] == "预言家"]
    for seer in seers:
        agent = game_state.agents[seer]
        decision = agent.think(
            game_state.__dict__,
            "作为预言家，请选择要查验的目标。"
        )
        night_actions.append(f"预言家{seer}查验：{decision}")
    
    # 女巫行动
    witches = [p for p in game_state.alive_players 
              if game_state.players[p]["role"] == "女巫"]
    for witch in witches:
        agent = game_state.agents[witch]
        decision = agent.think(
            game_state.__dict__,
            "作为女巫，请决定是否使用解药或毒药。"
        )
        night_actions.append(f"女巫{witch}行动：{decision}")
    
    return "\n".join(night_actions)

@mcp.tool()
def day_phase():
    """白天阶段"""
    if game_state.phase != "day":
        return "现在不是白天阶段"
    
    day_actions = []
    
    # 所有存活玩家发言
    for player_id in game_state.alive_players:
        agent = game_state.agents[player_id]
        decision = agent.think(
            game_state.__dict__,
            "请发表你的看法，分析场上局势。"
        )
        day_actions.append(f"玩家{player_id}发言：{decision}")
    
    # 投票阶段
    votes = {}
    for player_id in game_state.alive_players:
        agent = game_state.agents[player_id]
        decision = agent.think(
            game_state.__dict__,
            f"基于所有玩家的发言：{json.dumps(day_actions, ensure_ascii=False)}，请投票选出要放逐的玩家。"
        )
        votes[player_id] = decision
        day_actions.append(f"玩家{player_id}投票：{decision}")
    
    # 统计投票结果
    vote_count = {}
    for vote in votes.values():
        if vote in vote_count:
            vote_count[vote] += 1
        else:
            vote_count[vote] = 1
    
    # 找出得票最多的玩家
    max_votes = max(vote_count.values())
    eliminated = [p for p, v in vote_count.items() if v == max_votes]
    
    if len(eliminated) == 1:
        game_state.players[eliminated[0]]["is_alive"] = False
        game_state.alive_players.remove(eliminated[0])
        day_actions.append(f"玩家{eliminated[0]}被投票出局")
    else:
        day_actions.append("平票，无人出局")
    
    return "\n".join(day_actions)

@mcp.tool()
def change_phase():
    """切换游戏阶段"""
    if game_state.phase == "night":
        game_state.phase = "day"
        return "现在是白天阶段"
    else:
        game_state.phase = "night"
        game_state.current_round += 1
        return "现在是夜晚阶段"

@mcp.tool()
def check_status():
    """检查游戏状态"""
    alive_roles = [game_state.players[p]["role"] for p in game_state.alive_players]
    
    if not any(r == "狼人" for r in alive_roles):
        return "好人阵营胜利！"
    if not any(r in ["预言家", "女巫", "平民"] for r in alive_roles):
        return "狼人阵营胜利！"
    
    return f"游戏继续中，当前存活玩家：{', '.join(game_state.alive_players)}"

# 1. 开始游戏
result = start_game(8)  # 创建8个玩家
print(result)  # 显示游戏开始信息和角色分配

# 2. 夜晚阶段
result = night_phase()
print(result)  # 显示夜晚行动结果

# 3. 切换到白天
result = change_phase()
print(result)

# 4. 白天阶段
result = day_phase()
print(result)  # 显示白天发言和投票结果

# 5. 检查游戏状态
result = check_status()
print(result)

# 6. 继续游戏循环
while True:
    # 夜晚
    night_phase()
    change_phase()
    
    # 白天
    day_phase()
    change_phase()
    
    # 检查是否结束
    status = check_status()
    if "胜利" in status:
        print(status)
        break