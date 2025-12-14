# BuildForAI
用户界面/API
    ↓
构建AI助手 (BuildAIAssistant)
    ├── 构建执行模块 (BuildExecutor)
    ├── 错误分析模块 (BuildErrorAnalyzer)
    ├── 知识管理模块 (KnowledgeManager)
    └── 工作流引擎 (HuaweiBuildAIWorkflow)
        ↓
    [本地向量知识库] ←→ [DeepSeek AI API]
        ↓
编译构建服务 API
    1. 启动构建任务
    2. 监控构建状态 (轮询30秒间隔)
    3. 成功 → 记录成功信息
    4. 失败 → 触发AI分析
       4.1 提取错误信息
       4.2 检索相关知识
       4.3 调用AI深度分析
       4.4 生成修复建议
    5. 提供用户交互选项
       5.1 自动重试修复
       5.2 显示详细步骤
       5.3 添加到知识库