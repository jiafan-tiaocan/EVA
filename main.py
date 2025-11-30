from src.agent import app
from src.memory import MemoryManager
from langchain_core.messages import HumanMessage
import sys

def main():
    print("🤖 Engineer's Personal Agent (Gemini Powered) - Initialized")
    memory = MemoryManager()
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            # 模拟：如果是 "upload image"，实际应传入图片数据
            # 这里简化为文本交互，多模态在LangChain中需构造含 image_url 的 Message
            
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # Streaming output
            for event in app.stream(inputs):
                for key, value in event.items():
                    if key == "agent":
                        msg = value["messages"][0]
                        print(f"\nAgent: {msg.content}")
                    elif key == "tools":
                        print(f"\n[System]: Tool Executed.")
            
            # 交互结束后，自动将输入存入 Log (用于周报)
            memory.add_log(user_input, meta={"type": "conversation"})
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()