import asyncio
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import uuid

# MCP工具配置 ==============================================
CONFIG = """
workflow:
  name: article_generation
  parameters:
    initial_text: "人工智能发展趋势"
  
  tools:
    analyze_topic:
      class: mcp_tools.AnalyzeTool
      input: ["text"]
      output: ["keywords", "sentiment"]
      depends: []
      timeout: 5.0

    generate_outline:
      class: mcp_tools.OutlineTool
      input: ["keywords"]
      output: ["sections"]
      depends: ["analyze_topic"]
      timeout: 8.0

    research:
      class: mcp_tools.ResearchTool
      input: ["keywords", "max_results"]
      output: ["sources"]
      depends: ["analyze_topic"]
      timeout: 10.0

    generate_content:
      class: mcp_tools.ContentTool
      input: ["topic_data", "outline", "research_data"]
      output: ["content"]
      depends: ["analyze_topic", "generate_outline", "research"]
      timeout: 15.0
"""

# 数据结构 ==============================================
@dataclass
class MCPTool:
    name: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    depends: List[str]
    timeout: float

class ToolInvocation:
    def __init__(self, tool_name: str, params: Dict):
        self.task_id = str(uuid.uuid4())
        self.tool_name = tool_name
        self.params = params
        self.status = "pending"  # pending/ready/running/completed
        self.result = None

# 工作流引擎 ==============================================
class MCPWorkflowEngine:
    def __init__(self, config: Dict):
        self.config = config['workflow']
        self.tools = self._parse_tools()
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.dependents = defaultdict(set)
        self.ready_events = defaultdict(asyncio.Event)
        self.worker_count = 3

    def _parse_tools(self) -> Dict[str, MCPTool]:
        return {
            name: MCPTool(
                name=name,
                input_schema={k: v for k, v in tool['input']} if isinstance(tool['input'], list) else tool['input'],
                output_schema=tool['output'],
                depends=tool['depends'],
                timeout=tool['timeout']
            ) for name, tool in self.config['tools'].items()
        }

    async def start_workers(self):
        workers = [asyncio.create_task(self._tool_worker()) 
                  for _ in range(self.worker_count)]
        return workers

    async def _tool_worker(self):
        while True:
            invocation = await self.task_queue.get()
            await self._execute_tool(invocation)

    async def submit_task(self, tool_name: str, params: Dict):
        invocation = ToolInvocation(tool_name, params)
        
        # 注册依赖关系
        for dep in self.tools[tool_name].depends:
            self.dependents[dep].add(invocation.task_id)
            if dep not in self.results:
                self.ready_events[dep].wait()  # 等待依赖完成

        # 检查依赖就绪
        if await self._check_dependencies(invocation):
            await self._enqueue_task(invocation)
        else:
            # 注册回调通知
            asyncio.create_task(self._wait_for_dependencies(invocation))

    async def _check_dependencies(self, invocation: ToolInvocation) -> bool:
        return all(dep in self.results for dep in self.tools[invocation.tool_name].depends)

    async def _wait_for_dependencies(self, invocation: ToolInvocation):
        for dep in self.tools[invocation.tool_name].depends:
            await self.ready_events[dep].wait()
        await self._enqueue_task(invocation)

    async def _enqueue_task(self, invocation: ToolInvocation):
        invocation.status = "ready"
        await self.task_queue.put(invocation)

    async def _execute_tool(self, invocation: ToolInvocation):
        tool = self.tools[invocation.tool_name]
        invocation.status = "running"
        print(f"▶️ 开始执行 {tool.name}({invocation.params})")

        try:
            # 动态导入工具实现类
            module_path, class_name = tool.class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, class_name)
            
            # 执行工具并处理超时
            result = await asyncio.wait_for(
                tool_class.execute(**invocation.params),
                timeout=tool.timeout
            )
            
            # 保存结果并触发后续任务
            self.results[invocation.task_id] = result
            invocation.status = "completed"
            print(f"✅ {tool.name} 执行完成")
            
            # 通知依赖此任务的后继任务
            for child_id in self.dependents[invocation.task_id]:
                self.ready_events[invocation.task_id].set()

        except asyncio.TimeoutError:
            print(f"⏰ {tool.name} 执行超时")
            invocation.status = "timeout"
        except Exception as e:
            print(f"❌ {tool.name} 执行失败: {str(e)}")
            invocation.status = "failed"

# MCP工具实现 ==============================================
class AnalyzeTool:
    @classmethod
    async def execute(cls, text: str) -> Dict:
        await asyncio.sleep(1.5)
        return {
            "keywords": ["AI", "机器学习", "自然语言处理"],
            "sentiment": 0.85
        }

class OutlineTool:
    @classmethod
    async def execute(cls, keywords: List[str]) -> Dict:
        await asyncio.sleep(2)
        return {
            "sections": [
                "技术发展现状",
                "核心突破领域",
                "典型应用场景",
                "未来发展趋势"
            ]
        }

class ResearchTool:
    @classmethod
    async def execute(cls, keywords: List[str], max_results: int) -> Dict:
        await asyncio.sleep(3)
        return {
            "sources": [
                {"title": "2023年AI技术白皮书", "url": "..."},
                {"title": "行业应用报告", "url": "..."}
            ]
        }

class ContentTool:
    @classmethod
    async def execute(cls, topic_data: Dict, outline: Dict, research_data: Dict) -> Dict:
        await asyncio.sleep(4)
        return {
            "content": f"综合报告：基于{len(research_data['sources'])}个数据源，分析{topic_data['keywords'][0]}领域..."
        }

# LLM Agent模拟器 ==============================================
class LLMAgent:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.engine = MCPWorkflowEngine(self.config)
        self.workers = None

    async def execute_workflow(self):
        self.workers = await self.engine.start_workers()
        
        # 初始化任务
        initial_params = self.config['workflow']['parameters']
        analyze_id = await self.engine.submit_task(
            "analyze_topic",
            {"text": initial_params['initial_text']}
        )
        
        # 动态决策流程
        await self._process_next_step(analyze_id)

    async def _process_next_step(self, prev_task_id: str):
        """模拟LLM的链式决策"""
        current_results = self.engine.results.get(prev_task_id)
        
        if not current_results:
            return

        # 根据当前结果选择后续工具
        if prev_task_id.startswith("analyze_topic"):
            await self.engine.submit_task("generate_outline", {
                "keywords": current_results["keywords"]
            })
            await self.engine.submit_task("research", {
                "keywords": current_results["keywords"],
                "max_results": 5
            })
        
        elif prev_task_id.startswith("generate_outline"):
            await self.engine.submit_task("generate_content", {
                "topic_data": self.engine.results["analyze_topic"],
                "outline": current_results,
                "research_data": self.engine.results["research"]
            })
        
        # 持续监听完成事件
        asyncio.create_task(self._monitor_completion())

    async def _monitor_completion(self):
        while True:
            await asyncio.sleep(0.5)
            if "generate_content" in self.engine.results:
                print("\n🎉 工作流执行完成")
                return

# 执行示例 ==============================================
async def main():
    # 写入配置文件
    config_path = Path("mcp_workflow.yaml")
    config_path.write_text(CONFIG, encoding="utf-8")

    # 启动 LLM Agent 并执行工作流
    agent = LLMAgent(str(config_path))
    await agent.execute_workflow()

if __name__ == "__main__":
    asyncio.run(main())