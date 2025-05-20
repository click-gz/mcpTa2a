from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import random
from agent_tool import AgentTool
import json


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
        "action_count": 0,
        "werewolves": []
    }
    
    # 分配角色
    roles = ["狼人"] * 3 + ["预言家", "女巫", "平民", "平民", "平民"]
    player_ids = [f"player_{i+1}" for i in range(player_count)]
    
    random.shuffle(roles)
    werewolves = [player_ids[i] for i in range(player_count) if roles[i] == "狼人"]
    game_state['werewolves'] = werewolves
    
    for i in range(player_count):
        player_id = f"player_{i+1}"
        game_state["players"][player_id] = {"id": player_id, "role": roles[i], "agent":AgentTool(f"现在在玩狼人杀游戏，现在所有的用户id是{player_ids}，你的玩家id是{player_id}，你被分配的角色是{roles[i]}")}
        if roles[i] == "狼人":
            game_state["players"][player_id]["agent"].updata_history(
                f"狼人们的用户id是：{werewolves}"
            )
        game_state["alive_players"].append(player_id)
        game_state["roles"][player_id] = roles[i]
    
    game_state["phase"] = "night"
    return f"游戏开始！共有{player_count}名玩家，角色已分配完成，狼人：{', '.join(game_state['werewolves'])}"

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
def night_action_werewolf(prompt: str):
    """
    狼人夜晚行动, 通知狼人交流选择杀人对象，
    Args:
        prompt (str): 狼人交流的提示，需要上一轮狼人交流的记录
    """
    if game_state["phase"] != "night":
        return "现在不是夜晚阶段"
    res = []
    for player_id in game_state["alive_players"]:
        if game_state["roles"][player_id] == "狼人":
            target = game_state["players"][player_id]["agent"].chat(f"提示信息：{prompt}，请选择杀人对象的用户id")
            res.append(f"狼人{player_id}选择杀人对象: {target}")
    return f"狼人第一轮交流完毕: {json.dumps(res, ensure_ascii=False)}, 请继续你的推进，如果没有达成一致请继续推进狼人交流，你需要把上一轮狼人交流的记录告诉他们。"
    
@mcp.tool()
def night_action_seer(prompt: str):
    """
    预言家夜晚行动, 通知预言家选择查看对象
    Args:
        prompt (str): 提示信息
    """
    if game_state["phase"] != "night":
        return "现在不是夜晚阶段"
    res = []
    for player_id in game_state["alive_players"]:
        if game_state["roles"][player_id] == "预言家":
            target = game_state["players"][player_id]["agent"].chat(f"提示信息：{prompt}，请直接输出选择查看对象的用户id，不要输出任何其他信息：")
            if target in game_state["alive_players"]:
                role = game_state["players"][target]['role']
            else:
                role = "用户已死亡, 请提醒预言家重新选择"
            res.append(f"预言家{player_id}选择查看对象: {target}，他的角色是 {role}")
            game_state["players"][target]['agent'].updata_history(
                f"查看对象 {target}，他的角色是 {role}"
            )
    return f"预言家查看结束: {json.dumps(res, ensure_ascii=False)}, 请继续你的推进。"

@mcp.tool()
def night_action_witch(prompt: str):
    """
    女巫夜晚行动, 通知女巫选择救人/毒人对象
    Args:
        prompt (str): 提示信息
    """
    if game_state["phase"] != "night":
        return "现在不是夜晚阶段"
    res = []
    for player_id in game_state["alive_players"]:
        if game_state["roles"][player_id] == "女巫":
            # 获取女巫的选择
            action = game_state["players"][player_id]["agent"].chat(
                f"提示信息：{prompt}，请选择你要使用的技能（救人/毒人），以及目标玩家的用户id，严格按照输出示例：'救人，用户id' 或者 '毒人，用户id'，不要输出其他信息。"
            )
            # 解析女巫的选择
            res.append(f"女巫{player_id}的选择, {action}，")
                
    return f"女巫行动结束: {json.dumps(res, ensure_ascii=False)}, 请继续你的推进。如果存在用户id已死亡，请及时更新游戏状态。"
            

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
def day_action(prompt: str, action: str):
    """
    执行白天行动，包括发言和投票，先完成所有可发言玩家的发言，然后进行所有可投票玩家的投票
    Args:
        prompt (str): 提示信息，如果是发言，则提示信息为为昨夜发生的事并且要求发言；如果是投票，则提示信息为上一轮发言记录并且要求投票。
        action (str): 行动类型，发言或者投票
    """
    if game_state["phase"] != "day":
        return "现在不是白天阶段"
    
    
    if action == "发言":
        res = []
        for player_id in game_state["alive_players"]:
            response = game_state["players"][player_id]["agent"].chat(f"提示信息：{prompt}，现在是白天时间，请发言。")
            res.append(f"{player_id} 发言: {response}")
        return f"白天发言结束: {json.dumps(res, ensure_ascii=False)}, 请继续你的推进。下一步是投票，请把发言记录告诉所有玩家。"
    
    elif action == "投票":
        res = []
        for player_id in game_state["alive_players"]:
            response = game_state["players"][player_id]["agent"].chat(f"提示信息：{prompt}， 请投票给目标玩家。")
            res.append(f"{player_id} 投票: {response}")
        return f"白天投票结束: {json.dumps(res, ensure_ascii=False)}, 请继续你的推进。"
    
    return "无效的行动"

@mcp.tool()
def set_player_dead(player_id: str):
    """
    设置游戏中玩家状态变成死亡，可以是狼人杀人、女巫毒人、投票出局导致死亡。
    Args:
        player_id (str): 玩家ID
    """
    game_state["alive_players"].remove(player_id)
    return f"玩家{player_id}已设置成死亡。请继续推进游戏。"

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
    
    return f"游戏继续中，当前存活玩家：{', '.join(game_state['alive_players'])}，狼人：{', '.join(game_state['werewolves'])}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 