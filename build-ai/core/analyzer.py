# core/analyzer.py
import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
from datetime import datetime
import hashlib
from pathlib import Path
from .prompts import PromptManager
from config.settings import REPORT_CONFIG  # 导入配置

class BuildErrorAnalyzer:
    """构建错误分析器"""
    
    def __init__(self, deepseek_config: Dict, knowledge_base):
        
        # 直接从配置获取报告目录
        self.reports_dir = REPORT_CONFIG["output_dir"]
        
        print(f"📁 报告目录: {self.reports_dir}")
        print(f"🔍 检查目录是否存在: {self.reports_dir.exists()}")

        self.client = OpenAI(
            api_key=deepseek_config["api_key"],
            base_url=deepseek_config["base_url"]
        )
        self.model = deepseek_config["model"]
        self.temperature = deepseek_config["temperature"]
        self.max_tokens = deepseek_config["max_tokens"]
        
        self.knowledge_base = knowledge_base
        self.prompt_manager = PromptManager()
        
        # 错误模式识别
        self.error_patterns = self._init_error_patterns()
    
    def _init_error_patterns(self) -> Dict:
        """初始化错误模式"""
        return {
            "dependency": [
                r"npm ERR!", r"yarn error", r"pip install failed",
                r"Could not resolve dependency", r"Package.*not found",
                r"依赖.*失败", r"下载.*失败"
            ],
            "permission": [
                r"Permission denied", r"EACCES", r"权限不够",
                r"access denied", r"无权访问", r"Forbidden"
            ],
            "resource": [
                r"No space left", r"内存不足", r"disk full",
                r"OutOfMemoryError", r"内存溢出", r"资源不足"
            ],
            "configuration": [
                r"Configuration error", r"配置错误", 
                r"Invalid configuration", r"Missing.*property",
                r"参数错误", r"配置文件"
            ],
            "network": [
                r"Connection refused", r"Timeout", r"网络错误",
                r"Failed to connect", r"连接失败", r"请求超时"
            ],
            "code": [
                r"SyntaxError", r"编译错误", r"syntax error",
                r"undefined variable", r"类型错误", r"编译失败"
            ]
        }
    
    def analyze_error_log(self, log_content: str, log_source: str = "unknown") -> Dict:
        """分析错误日志"""
        print(f"🔍 开始分析错误日志: {log_source}")
        
        # 1. 提取关键错误信息
        error_snippets = self._extract_error_snippets(log_content)
        print(f"📝 提取到 {len(error_snippets)} 个错误片段")
        
        # 2. 检索相关知识,会拼接错误内容，然后一句话的方式去向量数据库匹配
        query_text = self._build_query_from_snippets(error_snippets)
        knowledge_results = self.knowledge_base.search(query_text, top_k=3)
        
        # 3. 构建上下文
        context = self._format_knowledge_context(knowledge_results)
        
        # 4. 调用AI分析
        analysis_result = self._call_ai_analysis(
            log_content[:2000],  # 限制长度
            context
        )

        # 5. 增强结果
        enhanced_result = self._enhance_analysis_result(
            analysis_result, 
            error_snippets,
            knowledge_results
        )
        
        # 6. 保存分析记录
        self._save_analysis_record(enhanced_result, log_source)
        
        return enhanced_result
    
    def _extract_error_snippets(self, log_content: str) -> List[str]:
        """提取关键错误片段"""
        snippets = []
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 提取上下文（前后2行）
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        snippet = '\n'.join(lines[start:end])
                        snippets.append({
                            "content": snippet,
                            "error_type": error_type,
                            "line_number": i + 1
                        })
                        break
        
        # 去重
        unique_snippets = []
        seen = set()
        for snippet in snippets:
            content_hash = hashlib.md5(snippet["content"].encode()).hexdigest()[:8]
            if content_hash not in seen:
                seen.add(content_hash)
                unique_snippets.append(snippet)
        
        return unique_snippets[:5]  # 最多返回5个
    
    def _build_query_from_snippets(self, snippets: List[Dict]) -> str:
        """从错误片段构建查询"""
        if not snippets:
            return "构建错误"
        
        # 使用错误类型和内容构建查询
        error_types = set(s["error_type"] for s in snippets)
        query_parts = []
        
        # 添加错误类型
        query_parts.append(" ".join(error_types))
        
        # 添加关键内容（每段取前50字符）
        for snippet in snippets[:2]:
            content_preview = snippet["content"][:50].replace('\n', ' ')
            query_parts.append(content_preview)
        
        return " ".join(query_parts)
    
    def _format_knowledge_context(self, knowledge_results: List[Dict]) -> str:
        """格式化知识上下文"""
        if not knowledge_results:
            return "暂无相关知识"
        
        context_parts = ["找到以下相关解决方案："]
        for i, result in enumerate(knowledge_results):
            context_parts.append(
                f"\n【解决方案 {i+1} - 相似度:{result['similarity']:.2f}】\n"
                f"{result['content']}"
            )
        
        return "\n".join(context_parts)
    
    def _call_ai_analysis(self, error_log: str, context: str) -> Dict:
        """调用AI进行分析"""
        try:
            prompt = self.prompt_manager.get_analysis_prompt(error_log, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是华为云编译构建专家"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
            
        except Exception as e:
            print(f"❌ AI分析失败: {str(e)}")
            return {
                "error_summary": "AI分析失败",
                "error_type": "other",
                "root_cause": f"分析过程中出错: {str(e)}",
                "confidence": 0.0,
                "fix_steps": [],
                "verification": "",
                "prevention": ""
            }
    
    def _enhance_analysis_result(self, analysis_result: Dict, 
                                error_snippets: List[Dict],
                                knowledge_results: List[Dict]) -> Dict:
        """增强分析结果"""
        enhanced = analysis_result.copy()
        
        # 添加原始数据
        enhanced["error_snippets"] = error_snippets
        enhanced["knowledge_references"] = [
            {
                "content": r["content"][:100] + "...",
                "similarity": r["similarity"]
            }
            for r in knowledge_results
        ]
        
        # 添加时间戳
        enhanced["analyzed_at"] = datetime.now().isoformat()
        
        # 计算置信度调整
        if knowledge_results:
            # 有相关知识，提高置信度
            max_similarity = max(r["similarity"] for r in knowledge_results)
            confidence_boost = min(0.2, max_similarity * 0.3)
            enhanced["confidence"] = min(1.0, enhanced.get("confidence", 0.5) + confidence_boost)
        
        return enhanced
    
    def _save_analysis_record(self, result: Dict, log_source: str):
        """保存分析记录"""
        record = {
            "log_source": log_source,
            "analyzed_at": result["analyzed_at"],
            "error_summary": result["error_summary"],
            "error_type": result["error_type"],
            "confidence": result["confidence"]
        }
        
        # 保存到文件
        record_file = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        record_path = self.reports_dir / record_file
        
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        print(f"📄 分析记录已保存: {record_path}")