import operator
from typing import Annotated, TypedDict, Union, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.llm import LLMFactory
from src.memory import MemoryManager
from src.tools import create_calendar_event, send_wechat_notification, generate_weekly_report

# 1. 定义状态
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_profile: str  # 注入的用户画像上下文
    image_data: str    # 暂存图片路径或base64 (简化处理)

# 2. 初始化组件
memory = MemoryManager()
llm = LLMFactory.get_llm()

# 绑定工具
tools = [create_calendar_event, send_wechat_notification, generate_weekly_report]
llm_with_tools = llm.bind_tools(tools)

# 3. 定义节点逻辑

def retrieve_context(state: AgentState):
    """检索增强节点：查找相关记忆并注入System Prompt"""
    last_msg = state["messages"][-1].content
    
    # RAG: 搜索相关历史
    related_logs = memory.search_logs(str(last_msg))
    profile = memory.get_profile()
    
    system_prompt = (
        f"You are a personal assistant for a senior algorithm engineer.\n"
        f"User Profile: {json.dumps(profile, ensure_ascii=False)}\n"
        f"Relevant Memories: {related_logs}\n"
        f"Current Time: {datetime.now()}\n"
        f"Be concise, professional, and proactive."
    )
    
    # 可以在这里处理图片：如果是 Gemini，将 ImageMessage 放入 messages 即可
    return {"user_profile": system_prompt}

def call_model(state: AgentState):
    """调用大模型"""
    messages = state["messages"]
    # 将 System Prompt 动态插入头部或作为 Context
    if state.get("user_profile"):
        messages = [SystemMessage(content=state["user_profile"])] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def reflect_and_learn(state: AgentState):
    """自进化节点：分析交互，更新画像"""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        # 简单的启发式：如果是一次建议性的回复，尝试提取用户的偏好
        # 在生产环境中，这里应该调用另一个专门的 'Evaluator' LLM chain
        pass 
        # memory.update_profile(...) 
    return {}

# 4. 构建图
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_context)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("reflect", reflect_and_learn)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "agent")

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "reflect"

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
workflow.add_edge("reflect", END)

app = workflow.compile()