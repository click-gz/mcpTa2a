Apply
# MCP 对话系统架构文档

## 1. 系统概述
MCP对话系统是一个基于LLM的多轮对话处理框架，支持工具调用和文件处理。系统通过异步方式运行，能够处理复杂的对话场景和工具调用。

## 2. 系统架构

### 2.1 核心组件
```plaintext
+-------------------+       +-------------------+       +-------------------+
|   用户输入处理     | ----> |   LLM 对话引擎    | ----> |   工具调用处理     |
+-------------------+       +-------------------+       +-------------------+
        ^                           |                           |
        |                           v                           v
        |                   +-------------------+       +-------------------+
        +-------------------|   对话历史管理     |<------|   文件处理模块     |
                            +-------------------+       +-------------------+
```
2.2 组件说明

用户输入处理

接收用户输入
处理文件附件
生成标准化的用户提示
LLM 对话引擎

调用LLM生成响应
处理多轮对话
管理对话上下文
工具调用处理

解析工具调用请求
执行工具
处理工具返回结果
对话历史管理

维护完整的对话历史
支持对话重置
提供上下文信息
文件处理模块

处理文件上传
支持文件字节和base64编码
保存生成的文件
3. 核心流程

```plaintext
Apply
1. 初始化系统
2. 接收用户输入
3. 处理文件附件
4. 生成用户提示
5. 调用LLM生成响应
6. 处理工具调用
7. 更新对话历史
8. 输出最终结果
4. 配置文件说明
```
系统使用JSON格式的配置文件，主要包含以下部分：


```json
Apply
{
    "mcpServers": {
        "ocr_general": {
            "url": "OCR服务地址"
        },
        "chat_general": {
            "command": "python",
            "args": ["chat_server.py"],
            "env": {
                "LLM_API_KEY": "API密钥",
                "LLM_BASE_URL": "API基础URL",
                "LLM_MODEL": "模型名称"
            }
        },
        "file_server": {
            "command": "python",
            "args": ["file_server.py"],
            "env": {
                "BASE_DATA_DIR": "文件存储目录"
            }
        }
    }
}
```
5. 主要功能
多轮对话管理

工具调用支持

文件处理

对话历史维护

异步执行

错误处理

6. 扩展性
系统设计具有良好的扩展性，可以通过以下方式扩展功能：

    + 添加新的工具服务器
    + 支持更多的文件类型
    + 集成更多的LLM模型
    + 添加对话策略管理
    + 支持多语言处理
  
### 1. 主LLM（剧本生成）
数据类型:
+ 剧本大纲
+ 场景描述

角色关系

数据来源:
+ IMSDb - 电影剧本数据库
+ SimplyScripts - 剧本资源网站
+ Dramatists Guild - 剧本资源

获取方式:
+ 从网站下载剧本
+ 使用爬虫工具收集
+ 手动整理和标注
### 2. 角色LLM（演员对话生成）
数据类型:
+ 角色档案
+ 对话样本
+ 性格特征
  
数据来源:
+ Cornell Movie Dialogs Corpus - 电影对话语料库
+ Character Mining - 角色特征数据库
+ TV Tropes - 角色特征分析
  
获取方式:
+ 下载公开数据集
+ 手动整理角色对话
+ 使用API获取角色信息
### 3. 工具调用模型
数据类型:
+ 工具使用记录
+ 调用参数
+ 返回结果

数据来源:
+ ProgrammableWeb - API目录
+ RapidAPI - API市场
+ GitHub - 开源工具

获取方式:
+ 收集工具使用日志
+ 整理API文档
+ 手动创建调用示例
### 4. 场景理解模型
数据类型:
+ 场景描述
+ 场景要素
+ 场景分类

数据来源:
+ MovieScenes - 电影场景数据库
+ + SceneStruct - 场景结构分析
FilmSceneAnalysis - 场景分析资源

获取方式:
+ 下载场景描述数据集
+ 手动标注场景要素
+ 使用爬虫工具收集
### 5. 剧本结构模型
数据类型:
+ 标准剧本格式
+ 剧本要素
+ 结构标注

数据来源:
+ Final Draft - 剧本格式标准
+ Celtx - 剧本格式资源
+ Screenplay Format - 剧本格式指南

获取方式:
+ 下载标准剧本样本
+ 手动标注剧本要素
+ 使用工具生成剧本结构

数据准备工具
+ 爬虫工具: Scrapy, BeautifulSoup
+ 标注工具: Label Studio, Prodigy
+ 数据处理工具: Pandas, NumPy
+ 数据存储: MongoDB, PostgreSQL

