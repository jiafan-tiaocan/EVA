from apscheduler.schedulers.background import BackgroundScheduler
from src.agent import app as agent_app  # 引入我们之前定义的 LangGraph App
from src.tools import send_wechat_notification
from langchain_core.messages import HumanMessage
import time

def daily_morning_brief():
    """每天早上 9 点触发：读取 arXiv，总结日程"""
    # 构造一个特殊的 Prompt 触发 Agent 的 Report 技能
    print("⏰ Triggering Morning Brief...")
    inputs = {"messages": [HumanMessage(content="SECRET_TRIGGER_MORNING_BRIEF: 请检查今天的日程和 arXiv 论文，给我发送早报。")]}
    
    # 运行图
    for event in agent_app.stream(inputs):
        pass # Agent 内部会自动调用 send_wechat_notification 工具

def start_scheduler():
    scheduler = BackgroundScheduler()
    # 每天早上 09:00 运行
    scheduler.add_job(daily_morning_brief, 'cron', hour=9, minute=0)
    scheduler.start()
    
    # 保持主线程运行 (如果是在单独脚本中)
    # try:
    #     while True: time.sleep(2)
    # except (KeyboardInterrupt, SystemExit):
    #     scheduler.shutdown()