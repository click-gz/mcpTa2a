# 狼人杀游戏设计文档 (A2A版本)

## 1. 系统架构

### 1.1 核心组件
- **Agent系统**：每个玩家都是一个独立的AI代理
- **游戏引擎**：管理游戏状态和流程
- **通信系统**：处理代理之间的信息传递
- **记忆系统**：存储每个代理的游戏记忆

### 1.2 数据流
[Agent A] <-> [通信系统] <-> [游戏引擎] <-> [通信系统] <-> [Agent B]
^ ^
| |
[记忆系统 A] ------------------------------------------------- [记忆系统 B]


## 2. Agent设计

### 2.1 Agent属性
```python
class Agent:
    def __init__(self):
        self.id: str          # 代理ID
        self.role: str        # 游戏角色
        self.memory: List     # 游戏记忆
        self.personality: Dict # 性格特征
        self.strategy: Dict   # 策略偏好
```

### 2.2 Agent能力
- **观察能力**：接收游戏状态和其他代理的行为
- **推理能力**：分析局势并做出决策
- **记忆能力**：存储和调用历史信息
- **学习能力**：根据游戏进程调整策略

## 3. 游戏流程

### 3.1 初始化阶段
1. 创建多个Agent实例
2. 随机分配角色
3. 初始化游戏状态
4. 建立Agent之间的通信通道

### 3.2 夜晚阶段
1. 狼人Agent之间进行秘密交流
2. 每个特殊角色Agent独立行动
3. 记录所有Agent的决策
4. 更新游戏状态

### 3.3 白天阶段
1. 所有Agent进行公开讨论
2. 每个Agent根据记忆和推理发表看法
3. 进行投票决策
4. 公布结果并更新状态

## 4. 通信机制

### 4.1 公开通信
- 白天阶段的发言
- 投票结果
- 游戏状态更新

### 4.2 私密通信
- 狼人之间的夜间交流
- 特殊角色（预言家、女巫）的查验/救人信息

### 4.3 通信格式
```python
class Message:
    def __init__(self):
        self.sender: str      # 发送者ID
        self.receiver: str    # 接收者ID
        self.content: str     # 消息内容
        self.type: str        # 消息类型
        self.timestamp: int   # 时间戳
```

## 5. 记忆系统

### 5.1 记忆类型
- **短期记忆**：当前回合的信息
- **长期记忆**：历史游戏信息
- **角色记忆**：角色相关的特殊信息

### 5.2 记忆结构
```python
class Memory:
    def __init__(self):
        self.game_history: List    # 游戏历史
        self.player_actions: Dict  # 玩家行为记录
        self.role_info: Dict      # 角色信息
        self.strategy_history: List # 策略历史
```

## 6. 决策系统

### 6.1 决策因素
- 当前游戏状态
- 历史记忆
- 角色特性
- 其他Agent的行为
- 策略偏好

### 6.2 决策流程
1. 收集相关信息
2. 分析当前局势
3. 评估可能行动
4. 选择最优决策
5. 执行并记录

## 7. 游戏状态

### 7.1 状态结构
```python
class GameState:
    def __init__(self):
        self.phase: str           # 游戏阶段
        self.players: Dict        # 玩家信息
        self.alive_players: List  # 存活玩家
        self.history: List        # 游戏历史
        self.current_round: int   # 当前回合
```

### 7.2 状态更新
- 角色行动后更新
- 投票结果后更新
- 阶段转换时更新