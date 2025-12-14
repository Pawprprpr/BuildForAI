# core/knowledge_base.py
import json
import hashlib
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings
from pathlib import Path

class KnowledgeBase:
    """向量知识库管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.kb_path = Path(config["path"])
        self.embedder = None
        self.client = None
        self.collection = None
        
        self._init_knowledge_base()
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        # 1. 初始化嵌入模型
        print("🔧 加载嵌入模型...")
        self.embedder = SentenceTransformer(self.config["embedder_model"])
        
        # 2. 初始化ChromaDB客户端
        print("📚 初始化向量数据库...")
        self.client = chromadb.PersistentClient(
            path=str(self.kb_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 3. 获取或创建集合
        try:
            self.collection = self.client.get_collection(
                name=self.config["collection_name"]
            )
            print(f"✅ 加载已有知识库，文档数: {self.collection.count()}")
        except:
            self.collection = self.client.create_collection(
                name=self.config["collection_name"],
                metadata={"description": "华为云构建错误解决方案知识库"}
            )
            print("✅ 创建新的知识库")
        
        # 4. 加载初始知识
        self._load_initial_knowledge()
    
    def _load_initial_knowledge(self):
        """加载初始知识文档"""
        initial_knowledge = [
            {
                "content": """华为云编译构建常见错误：依赖下载失败
解决方案：
1. 检查网络连接：ping repo.huaweicloud.com
2. 配置镜像源：npm config set registry https://repo.huaweicloud.com/repository/npm/
3. 清理缓存：npm cache clean --force
4. 重试构建""",
                "metadata": {
                    "source": "manual",
                    "error_type": "dependency",
                    "keywords": "npm依赖 下载失败"
                }
            },
            {
                "content": """Docker构建错误：权限不足
解决方案：
1. 检查Docker服务状态：systemctl status docker
2. 添加用户到docker组：sudo usermod -aG docker $USER
3. 重新登录生效
4. 检查镜像仓库权限""",
                "metadata": {
                    "source": "manual", 
                    "error_type": "permission",
                    "keywords": "docker, 权限, permission denied"
                }
            },
            {
                "content": """Maven构建错误：内存不足
解决方案：
1. 调整Maven内存设置：export MAVEN_OPTS="-Xmx2048m -Xms1024m"
2. 跳过测试：mvn clean install -DskipTests
3. 使用增量编译
4. 检查JVM配置""",
                "metadata": {
                    "source": "manual",
                    "error_type": "resource",
                    "keywords": "maven 内存 out of memory"
                }
            }
        ]
        
        # 如果知识库为空，添加初始知识
        if self.collection.count() == 0:
            print("📖 添加初始知识文档...")
            for i, doc in enumerate(initial_knowledge):
                self.add_document(
                    content=doc["content"],
                    metadata=doc["metadata"]
                )
    
    def add_document(self, content: str, metadata: Dict) -> str:
        """添加文档到知识库"""
        # 生成文档ID 
        doc_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        doc_id = f"doc_{doc_hash}"
        
        # 生成嵌入向量
        embedding = self.embedder.encode(content).tolist()
        
        # 添加元数据
        full_metadata = metadata.copy()
        full_metadata["content_hash"] = doc_hash
        
        # 存储到向量数据库
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[full_metadata],
            ids=[doc_id]
        )
        
        print(f"✅ 文档已添加: {doc_id}")
        return doc_id
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索相关知识"""
        # 生成查询向量
        query_embedding = self.embedder.encode(query).tolist()
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        formatted_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # 转换为相似度分数
                    "rank": i + 1
                })
        
        return formatted_results
    
    def count_documents(self) -> int:
        """获取文档数量"""
        return self.collection.count()