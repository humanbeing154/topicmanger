from pkg.plugin.context import register, handler, BasePlugin, EventContext, APIHost
from pkg.plugin.events import GroupNormalMessageReceived
from typing import Dict, Any
import time
import asyncio

# 定义群组上下文存储结构
group_contexts: Dict[str, Dict[str, Any]] = {
    # group_id: {
    #     "topic": str,          # 当前话题
    #     "users": Dict[str, list], # 用户发言记录 {user_id: [messages]}
    #     "last_active": float   # 最后活跃时间戳
    # }
}

# 注册插件
@register(name="TopicManager", 
         description="群组话题上下文管理插件", 
         version="0.1", 
         author="YourName")
class TopicManagerPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host
        
    async def initialize(self):
        # 启动定时清理任务
        asyncio.create_task(self._cleanup_task())

    # 定时清理过期话题（每5分钟检查一次）
    async def _cleanup_task(self):
        while True:
            await asyncio.sleep(300)
            current_time = time.time()
            for group_id in list(group_contexts.keys()):
                ctx = group_contexts[group_id]
                if current_time - ctx["last_active"] > 600:  # 10分钟无活动
                    del group_contexts[group_id]
                    self.host.logger.info(f"群组 {group_id} 话题已自动关闭")

    # 处理群消息
    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        event = ctx.event
        group_id = event.group_id
        user_id = event.sender_id
        message = event.text_message.strip()

        # 处理话题指令
        if message.startswith("#开启话题"):
            if len(message.split()) < 2:
                await ctx.reply("请指定话题名称，格式：#开启话题 主题")
                return
                
            topic = message.split(" ", 1)[1]
            group_contexts[group_id] = {
                "topic": topic,
                "users": {},
                "last_active": time.time()
            }
            await ctx.reply(f"【新话题已开启】{topic}\n现在开始讨论吧！")
            ctx.prevent_default()
            return

        # 检查当前群组是否有活跃话题
        if group_id not in group_contexts:
            return

        # 更新活跃时间
        group_ctx = group_contexts[group_id]
        group_ctx["last_active"] = time.time()

        # 记录用户发言
        if user_id not in group_ctx["users"]:
            group_ctx["users"][user_id] = []
        group_ctx["users"][user_id].append(message)

        # 构建上下文Prompt
        history = []
        for uid, msgs in group_ctx["users"].items():
            history.append(f"用户{uid}历史发言：" + " | ".join(msgs[-3:]))  # 取最近3条
        
        prompt = f"""当前讨论话题：{group_ctx['topic']}
        上下文摘要：
        {chr(10).join(history)}
        最新提问：用户{user_id}说：{message}
        请根据话题和上下文给出专业回复："""

        # 调用语言模型（需替换为实际API调用）
        response = await self._call_llm_api(prompt)
        
        # 发送回复并阻止默认处理
        await ctx.reply(f"@{user_id} {response}")
        ctx.prevent_default()

    async def _call_llm_api(self, prompt: str) -> str:
        """模拟模型调用（实际需接入真实API）"""
        # 示例伪代码：
        # return await self.host.llm.generate(prompt)
        return "这是一个基于上下文的测试回复。实际应接入语言模型API。"