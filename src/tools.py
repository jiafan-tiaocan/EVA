from langchain_core.tools import tool
from datetime import datetime, timedelta
from ics import Calendar, Event
import requests
import yaml

# 读取配置用于回调
with open("config/settings.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

@tool
def generate_weekly_report(logs_context: str) -> str:
    """
    根据提供的日志上下文生成周报草稿。
    Input: logs_context (本周所有的日志聚合文本)
    """
    # 实际逻辑由Agent的LLM完成，Tool只作为占位或格式化
    return f"REPORT_GENERATED_SIGNAL: 请LLM根据以下内容整理Markdown周报:\n{logs_context}"

@tool
def create_calendar_event(title: str, start_time: str, duration_hours: float = 1.0) -> str:
    """
    在iOS日历中创建日程。
    Input:
        title: 事件标题
        start_time: ISO格式时间字符串 (e.g., 2025-11-30T10:00:00)
        duration_hours: 持续时间
    """
    try:
        c = Calendar()
        e = Event()
        e.name = title
        e.begin = start_time
        e.duration = timedelta(hours=duration_hours)
        c.events.add(e)
        
        filename = f"invite_{datetime.now().timestamp()}.ics"
        with open(filename, 'w') as f:
            f.write(str(c))
            
        # 实际场景：这里可以调用 send_wechat 发送这个 .ics 文件给手机
        # 或者调用 iOS Shortcuts Webhook
        return f"Event created: {filename}. Please send this file to user's phone."
    except Exception as e:
        return f"Failed to create event: {str(e)}"

@tool
def send_wechat_notification(message: str):
    """主动触达用户微信"""
    url = CONFIG["channels"]["wecom_webhook"]
    if not url:
        return "No WeCom webhook configured."
    
    payload = {
        "msgtype": "text",
        "text": {"content": f"[Agent]: {message}"}
    }
    requests.post(url, json=payload)
    return "Notification sent."

# 此处可预留 MCP Server 的 client 接入
# def call_mcp_tool(...)