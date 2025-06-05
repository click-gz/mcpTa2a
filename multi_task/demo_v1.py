import asyncio
from typing import Dict, Any, Callable, Set, List
from collections import defaultdict

class TaskManager:
    """任务状态与依赖管理器"""
    def __init__(self):
        self.tasks = {}          # 任务注册表 {task_id: {depends, callback}}
        self.status = {}         # 任务状态 {task_id: 'pending'|'success'|'failed'}
        self.dependents = defaultdict(set)  # 依赖关系 {parent_id: {child_ids}}
    
    def register_task(self, 
                     task_id: Any,
                     depends: List[Any] = [],
                     callback: Callable = None):
        """注册新任务"""
        self.tasks[task_id] = {
            'depends': set(depends),
            'callback': callback,
            'result': None
        }
        self.status[task_id] = 'pending'
        
        # 建立依赖关系
        for parent in depends:
            self.dependents[parent].add(task_id)
    
    def mark_completed(self, task_id: Any, result: Any):
        """标记任务完成"""
        if task_id not in self.tasks:
            return
        
        self.tasks[task_id]['result'] = result
        self.status[task_id] = 'success'
        
    def get_ready_tasks(self) -> Set[Any]:
        """获取就绪任务（依赖已满足）"""
        ready = set()
        for task_id, info in self.tasks.items():
            if self.status[task_id] != 'pending':
                continue
                
            # 检查所有前置任务是否完成
            if all(self.status.get(dep, 'success') == 'success' 
                   for dep in info['depends']):
                ready.add(task_id)
        
        return ready

class AsyncLLMOrchestrator:
    def __init__(self, max_workers=3):
        self.task_queue = asyncio.Queue()
        self.task_manager = TaskManager()
        self.workers = []
        self.max_workers = max_workers
        self.results = {}
        
    async def start(self):
        """启动工作协程"""
        self.workers = [
            asyncio.create_task(self._worker())
            for _ in range(self.max_workers)
        ]
    
    async def shutdown(self):
        """关闭服务"""
        for w in self.workers:
            w.cancel()
    
    async def submit_task(self, 
                         tool_name: str,
                         params: dict,
                         depends: List[str] = [],
                         callback: Callable = None) -> str:
        """提交新任务"""
        task_id = f"{tool_name}-{id(params)}"
        self.task_manager.register_task(task_id, depends, callback)
        
        # 立即检查是否就绪
        if task_id in self.task_manager.get_ready_tasks():
            await self.task_queue.put({
                'tool': tool_name,
                'params': params,
                'task_id': task_id
            })
        
        return task_id
    
    async def _worker(self):
        """工作协程实现"""
        while True:
            task = await self.task_queue.get()
            try:
                result = await self.execute_tool(task['tool'], task['params'])
                self._handle_task_completion(task['task_id'], result)
            except Exception as e:
                print(f"任务 {task['task_id']} 失败: {str(e)}")
                self.task_manager.status[task['task_id']] = 'failed'
    
    async def execute_tool(self, tool_name: str, params: dict) -> Any:
        """执行工具（模拟实现）"""
        print(f"[执行] 开始 {tool_name}，参数: {params}")
        await asyncio.sleep(2)  # 模拟耗时操作
        result = f"{tool_name}-result"
        print(f"[完成] {tool_name} => {result}")
        return result
    
    def _handle_task_completion(self, task_id: str, result: Any):
        """处理任务完成"""
        # 保存结果
        self.results[task_id] = result
        self.task_manager.mark_completed(task_id, result)
        
        # 执行回调
        if callback := self.task_manager.tasks[task_id]['callback']:
            callback(task_id, result)
        
        # 触发后续任务
        for child_id in self.task_manager.dependents[task_id]:
            if child_id in self.task_manager.get_ready_tasks():
                asyncio.create_task(self._enqueue_child(child_id))
    
    async def _enqueue_child(self, child_id: str):
        """将就绪的子任务入队"""
        task_info = self.task_manager.tasks[child_id]
        await self.task_queue.put({
            'tool': child_id.split('-')[0],  # 从ID解析工具名
            'params': {},  # 实际应携带参数
            'task_id': child_id
        })

# 使用示例
async def sample_callback(task_id: str, result: str):
    print(f"[回调] {task_id} 完成，结果: {result}")
    # 可在此保存状态到数据库

async def main():
    orchestrator = AsyncLLMOrchestrator(max_workers=2)
    await orchestrator.start()
    
    # 提交任务链：A → C，B → C
    task_a = await orchestrator.submit_task(
        "analyzer", {"text": "Hello"}, callback=sample_callback
    )
    task_b = await orchestrator.submit_task(
        "searcher", {"query": "World"}, callback=sample_callback
    )
    task_c = await orchestrator.submit_task(
        "generator", {}, depends=[task_a, task_b], callback=sample_callback
    )
    
    # 等待所有任务完成
    while len(orchestrator.results) < 3:
        await asyncio.sleep(1)
    
    await orchestrator.shutdown()

asyncio.run(main())

"""
1. 提交任务A(analyzer)和B(searcher)，它们没有前置依赖
   → 立即进入队列执行
   
2. 提交任务C(generator)，依赖A和B
   → 状态保持pending，直到A和B完成

3. 工作协程执行A和B:
   A完成 → 触发回调 → 检查C的依赖是否满足（此时B未完成）
   B完成 → 触发回调 → 检查C的依赖（A和B均完成）

4. C进入就绪状态 → 被加入队列执行

5. 所有任务完成 → 流程结束

"""
