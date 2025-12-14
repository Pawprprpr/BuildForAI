# core/prompts.py
import json
from typing import Dict, Any  # 添加导入

class PromptManager:
    """提示词管理器"""
    
    @staticmethod
    def get_analysis_prompt(error_log: str, context: str = "") -> str:
        """获取错误分析提示词"""
        
        base_prompt = """你是一个华为云编译构建专家。请分析以下构建错误日志，提供专业的解决方案。

错误日志：
{error_log}
相关上下文知识：
{context}

请按照以下JSON格式返回分析结果：
{{
    "error_summary": "一句话错误摘要",
    "error_type": "错误分类",
    "root_cause": "详细根本原因分析", 
    "confidence": 0.8,
    "fix_steps": [
        {{"step": 1, "action": "操作描述", "command": "具体命令"}}
    ],
    "verification": "如何验证修复成功",
    "prevention": "预防措施"
}}

要求：
1. 错误分类从以下选择：dependency, permission, resource, configuration, network, code, other
2. 修复步骤要具体可执行
3. 引用相关知识中的有效方法
4. 如果信息不足，请明确说明
"""
        
        context_text = context if context else "暂无相关知识"
        return base_prompt.format(error_log=error_log, context=context_text)
    
    @staticmethod
    def get_solution_to_kb_prompt(analysis_result: Dict) -> str:
        """获取解决方案总结提示词（用于存入知识库）"""
        return f"""请将以下解决方案总结为知识库文档格式：

原始错误：{analysis_result.get('error_summary', '')}
根本原因：{analysis_result.get('root_cause', '')}
解决方案步骤：{json.dumps(analysis_result.get('fix_steps', []), ensure_ascii=False)}

请生成标准化的解决方案文档，包含：
1. 问题描述
2. 解决方案（分步骤）
3. 验证方法
4. 注意事项

输出格式：
问题：[问题描述]
解决方案：
1. [步骤1]
2. [步骤2]
...
验证：[验证方法]
注意：[注意事项]"""