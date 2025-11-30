import os
import json
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from typing import List, Dict

class MemoryManager:
    def __init__(self, config_path="config/settings.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)["memory"]
            
        # 1. 初始化向量数据库 (Log存储)
        self.chroma_client = chromadb.PersistentClient(path=self.config["chroma_path"])
        # 使用默认embedding，生产环境建议换成本地模型如 m3e 或 openai-embedding
        self.collection = self.chroma_client.get_or_create_collection(
            name="personal_logs",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        
        # 2. 初始化结构化画像 (自进化存储)
        self.profile_path = self.config["profile_path"]
        if not os.path.exists(self.profile_path):
            with open(self.profile_path, "w") as f:
                json.dump({"preferences": [], "summary": "Initial Profile"}, f)

    def add_log(self, content: str, meta: Dict = None):
        """存储日志/图片描述"""
        meta = meta or {}
        meta["timestamp"] = datetime.now().isoformat()
        
        self.collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[f"log_{datetime.now().timestamp()}"]
        )

    def search_logs(self, query: str, n_results: int = 5) -> List[str]:
        """RAG 检索"""
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return results["documents"][0] if results["documents"] else []

    def get_profile(self) -> Dict:
        """获取当前用户画像"""
        with open(self.profile_path, "r") as f:
            return json.load(f)

    def update_profile(self, new_insight: str):
        """自进化：更新用户画像"""
        profile = self.get_profile()
        profile["preferences"].append(new_insight)
        profile["last_updated"] = datetime.now().isoformat()
        
        # 这里可以使用LLM合并整理preference，简单起见先Append
        with open(self.profile_path, "w") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)