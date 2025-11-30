from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from src.agent import app as agent_app
from src.tools import send_wechat_notification
from langchain_core.messages import HumanMessage

# 引入 wechatpy 库
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.crypto import WeChatCrypto
from wechatpy import parse_message, create_reply
import yaml

app = FastAPI()

# 1. 加载配置
with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)["server"]

TOKEN = config["wecom_token"]
EncodingAESKey = config["wecom_aes_key"]
CORP_ID = config["wecom_corp_id"]

# 初始化加解密器
crypto = WeChatCrypto(TOKEN, EncodingAESKey, CORP_ID)

def run_agent_task(user_msg: str, user_id: str):
    """后台运行 Agent"""
    print(f"🤖 Agent received from {user_id}: {user_msg}")
    
    # 构造输入
    inputs = {"messages": [HumanMessage(content=user_msg)]}
    
    final_response = "I'm thinking..."
    try:
        # 运行 LangGraph
        for event in agent_app.stream(inputs):
            if "agent" in event:
                msg = event["agent"]["messages"][0]
                final_response = msg.content
                
        # 主动推送结果给用户
        # 注意：这里需要你修改 tools.py 里的 send_wechat_notification
        # 让它支持传入 user_id (touser)，否则默认是发给全员或特定人
        send_wechat_notification(final_response) 
        
    except Exception as e:
        print(f"Error executing agent: {e}")

@app.get("/wechat")
async def verify_url(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """
    企微后台配置回调 URL 时的验证接口 (GET)
    """
    try:
        echostr_decrypted = crypto.check_signature(
            msg_signature,
            timestamp,
            nonce,
            echostr
        )
        return PlainTextResponse(echostr_decrypted)
    except InvalidSignatureException:
        raise HTTPException(status_code=403, detail="Invalid signature")

@app.post("/wechat")
async def receive_msg(request: Request, background_tasks: BackgroundTasks):
    """
    接收用户发来的消息 (POST)
    """
    params = request.query_params
    msg_signature = params.get('msg_signature')
    timestamp = params.get('timestamp')
    nonce = params.get('nonce')
    
    # 1. 获取原始 XML 数据
    body = await request.body()
    
    try:
        # 2. 解密 XML
        decrypted_xml = crypto.decrypt_message(
            body,
            msg_signature,
            timestamp,
            nonce
        )
        
        # 3. 解析消息对象
        msg = parse_message(decrypted_xml)
        
        # 4. 只处理文本消息 (你也可以加 image)
        if msg.type == 'text':
            content = msg.content
            user_id = msg.source # 发送者的 UserID
            
            # 5. 放入后台任务 (快速返回，防止超时)
            background_tasks.add_task(run_agent_task, content, user_id)
            
        # 企微要求 5秒内响应，否则会重试。
        # 我们可以返回一个空串，或者简单的 "Received"
        # 或者直接用 create_reply 返回一个 XML (但这只能是被动回复)
        return PlainTextResponse("success")
        
    except (InvalidSignatureException, Exception) as e:
        print(f"Error handling message: {e}")
        raise HTTPException(status_code=403, detail="Invalid request")