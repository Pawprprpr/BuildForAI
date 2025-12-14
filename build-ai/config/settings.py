# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目路径
BASE_DIR = Path(__file__).resolve().parent.parent

# DeepSeek配置
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "temperature": 0.1,
    "max_tokens": 2000
}

# 知识库配置
KNOWLEDGE_BASE_CONFIG = {
    "path": BASE_DIR / "data" / "knowledge",
    "embedder_model": "paraphrase-multilingual-MiniLM-L12-v2",
    "collection_name": "huawei_build_solutions",
    "chunk_size": 500
}

# 日志文件配置
LOG_FILES_CONFIG = {
    "input_dir": BASE_DIR / "data" / "logs",
    "supported_formats": [".log", ".txt"]
}

# 分析报告配置
REPORT_CONFIG = {
    "output_dir": BASE_DIR / "data" / "reports",
    "template": "default"
}

# 创建必要目录
for dir_path in [
    KNOWLEDGE_BASE_CONFIG["path"],
    LOG_FILES_CONFIG["input_dir"],
    REPORT_CONFIG["output_dir"]
]:
    dir_path.mkdir(parents=True, exist_ok=True)