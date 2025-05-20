1. 总体结构
使用FastMCP框架，所有操作通过@mcp.tool()装饰器暴露为工具接口。
游戏状态通过全局变量game_state维护，包括玩家、角色、阶段、存活玩家、历史、行动次数等。
2. 主要数据结构
Apply to design.py
3. 主要功能接口（工具）
3.1. start_game(player_count=8)
初始化游戏状态，随机分配角色（3狼人+1预言家+1女巫+3平民）。
设置初始阶段为“night”（夜晚）。
3.2. get_role(player_id)
查询指定玩家的角色。
3.3. night_action_werewolf(prompt)
狼人夜晚行动，通知狼人交流选择杀人对象。
3.4. night_action_seer(prompt)
预言家夜晚行动，通知预言家选择查看对象。
3.5. night_action_witch(prompt)
女巫夜晚行动，通知女巫选择救人/毒人对象。
3.6. change_scene()
切换游戏阶段（夜晚<->白天）。
3.7. day_action(prompt, action)
执行白天行动，包括发言和投票。
3.8. set_player_dead(player_id)
设置游戏中玩家状态变成死亡。
3.9. check_game_status()
检查当前游戏状态，判断是否有阵营获胜。
4. 游戏流程
初始化：调用start_game分配角色，进入夜晚。
夜晚行动：狼人击杀、预言家查验、女巫用药。
切换白天：调用change_scene，进入白天。
白天发言/投票：玩家依次发言，投票放逐嫌疑人。
切换夜晚：调用change_scene，进入夜晚。
胜负判定：每轮结束后调用check_game_status，判断是否有阵营获胜。
循环往复：直到一方胜利。
请根据以上内容更新design.md文件。
