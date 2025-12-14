# main.py
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from config.settings import DEEPSEEK_CONFIG, KNOWLEDGE_BASE_CONFIG
from core.knowledge_base import KnowledgeBase
from core.analyzer import BuildErrorAnalyzer

def main():
    """主程序"""
    print("=" * 50)
    print("🚀 华为云构建AI助手 - 极简版")
    print("=" * 50)
    
    # 检查API密钥
    if not DEEPSEEK_CONFIG["api_key"]:
        print("❌ 错误：请先在 .env 文件中设置 DEEPSEEK_API_KEY")
        print("   1. 访问 https://platform.deepseek.com/")
        print("   2. 获取API密钥")
        print("   3. 编辑 .env 文件，添加: DEEPSEEK_API_KEY=你的密钥")
        return
    
    # 1. 初始化知识库
    print("\n1. 初始化系统...")
    kb = KnowledgeBase(KNOWLEDGE_BASE_CONFIG)
    
    # 2. 添加一些示例知识
    if kb.count_documents() == 0:
        print("2. 添加示例知识...")
        examples = [
            "npm install失败时，可以尝试：1.清除缓存 npm cache clean 2.使用国内镜像源",
            "Docker权限错误：将用户加入docker组：sudo usermod -aG docker $USER",
            "内存不足时，增加Maven内存：export MAVEN_OPTS='-Xmx2048m -Xms1024m'"
        ]
        for example in examples:
            kb.add_document(example, {"type": "example"})
    
    # 3. 初始化分析器
    analyzer = BuildErrorAnalyzer(DEEPSEEK_CONFIG, kb)
    
    # 4. 测试分析
    print("\n3. 测试分析功能...")
    
    # 测试日志
    test_log = """npm ERR! code ETIMEDOUT
npm ERR! errno ETIMEDOUT
npm ERR! network request to https://registry.npmjs.org/vue failed
npm ERR! network This is a problem related to network connectivity.
npm ERR! network In most cases you are behind a proxy or have bad network settings."""
    
    print(f"测试日志: {test_log[:100]}...")
    
    # 分析
    result = analyzer.analyze_error_log(test_log)
    
    # 5. 显示结果
    print("\n" + "=" * 50)
    print("📊 分析结果")
    print("=" * 50)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n✅ 系统运行成功！")
    print("\n下一步可以:")
    print("1. 修改测试日志内容")
    print("2. 添加更多知识到知识库")
    print("3. 连接真实构建日志文件")

if __name__ == "__main__":
    main()
