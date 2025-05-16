from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import random

# 创建MCP服务器实例
mcp = FastMCP(
    name="werewolf"
)

# 游戏状态
game_state = {
    "players": {},  # 玩家信息
    "roles": {},    # 角色分配
    "phase": "init", # 游戏阶段
    "alive_players": [], # 存活玩家
    "history": [],   # 游戏历史
    "action_count": 0 # 行动次数, 用于引导游戏白天/黑夜场景变换
}

@mcp.tool()
def start_game(player_count: int = 8):
    """
    开始新游戏，分配角色
    Args:
        player_count (int): 玩家数量，默认8人
    """
    global game_state
    
    # 重置游戏状态
    game_state = {
        "players": {},
        "roles": {},
        "phase": "init",
        "alive_players": [],
        "history": [],
        "action_count": 0
    }
    
    # 分配角色
    roles = ["狼人"] * 3 + ["预言家", "女巫", "猎人", "平民"] * 2
    random.shuffle(roles)
    
    for i in range(player_count):
        player_id = f"player_{i+1}"
        game_state["players"][player_id] = {"id": player_id, "role": roles[i]}
        game_state["alive_players"].append(player_id)
        game_state["roles"][player_id] = roles[i]
    
    game_state["phase"] = "night"
    return f"游戏开始！共有{player_count}名玩家，角色已分配完成。"

@mcp.tool()
def get_role(player_id: str):
    """
    获取玩家角色
    Args:
        player_id (str): 玩家ID
    """
    if player_id not in game_state["roles"]:
        return "玩家不存在"
    return f"你的角色是：{game_state['roles'][player_id]}"

@mcp.tool()
def night_action(player_id: str, action: str, target: str = None):
    """
    执行夜晚行动
    Args:
        player_id (str): 玩家ID
        action (str): 行动类型（查看/毒药/救人/击杀）
        target (str): 目标玩家ID
    """
    if game_state["phase"] != "night":
        return "现在不是夜晚阶段"
    
    if player_id not in game_state["alive_players"]:
        return "你已经死亡"
    
    role = game_state["roles"][player_id]
    
    if role == "狼人" and action == "击杀":
        if target in game_state["alive_players"]:
            game_state["alive_players"].remove(target)
            return f"狼人击杀了 {target}"
    
    elif role == "预言家" and action == "查看":
        if target in game_state["alive_players"]:
            target_role = game_state["roles"][target]
            return f"你查看了 {target} 的身份，他是 {target_role}"
    
    elif role == "女巫":
        if action == "毒药" and target in game_state["alive_players"]:
            game_state["alive_players"].remove(target)
            return f"女巫毒死了 {target}"
        elif action == "救人" and target in game_state["alive_players"]:
            return f"女巫救活了 {target}"
    
    return "无效的行动"

@mcp.tool()
def change_scene():
    """
    场景变换，在夜晚能够行动的玩家都行动后或者白天发言结束后触发
    """
    global game_state
    if game_state["phase"] == "night":
        game_state["phase"] = "day"
        return "现在是白天阶段"
    elif game_state["phase"] == "day":
        game_state["phase"] = "night"
        return "现在是夜晚阶段"
    else:
        return "游戏尚未开始, 请先start"

@mcp.tool()
def day_action(player_id: str, action: str, target: str = None):
    """
    执行白天行动，包括发言和投票，先完成所有可发言玩家的发言，然后进行所有可投票玩家的投票
    Args:
        player_id (str): 玩家ID
        action (str): 行动类型（发言/投票）
        target (str): 目标玩家ID（投票时使用）
    """
    if game_state["phase"] != "day":
        return "现在不是白天阶段"
    
    if player_id not in game_state["alive_players"]:
        return "你已经死亡"
    
    if action == "发言":
        if player_id == "player_2":
            return "2号玩家发言需要由用户自己输入内容"
    
    elif action == "投票" and target:
        if target in game_state["alive_players"]:
            game_state["alive_players"].remove(target)
            return f"{player_id} 投票放逐了 {target}"
    
    return "无效的行动"

@mcp.tool()
def check_game_status():
    """
    检查游戏状态
    """
    alive_roles = [game_state["roles"][p] for p in game_state["alive_players"]]
    
    # 检查狼人是否全部死亡
    if not any(r == "狼人" for r in alive_roles):
        return "好人阵营胜利！"
    
    # 检查好人是否全部死亡
    if not any(r in ["预言家", "女巫", "猎人", "平民"] for r in alive_roles):
        return "狼人阵营胜利！"
    
    return f"游戏继续中，当前存活玩家：{', '.join(game_state['alive_players'])}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 