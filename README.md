# 简历智能筛选工作流

基于 LangGraph 的智能简历筛选系统，自动解析简历、评估匹配度、生成面试题/婉拒信、发送邮件、输出筛选报告。

## 功能特性

- 📄 **简历解析** - 支持 PDF/DOCX 格式，自动提取文本内容
- 🤖 **智能提取** - 使用 LLM 结构化提取简历信息（姓名、联系方式、教育背景、工作经历、技能等）
- 📊 **匹配评分** - 根据岗位要求自动评分，70分为筛选门槛
- ✉️ **邮件通知** - 自动发送面试邀约或婉拒邮件
- 📝 **报告生成** - 生成 PDF 格式的筛选报告，可下载存档

## 工作流架构

```
简历文件(PDF/DOCX) + 岗位要求
         │
         ▼
┌────────────────────┐
│ ① 简历解析        │ → Fetch URL 技能解析文档
└────────┬───────────┘
         ▼
┌────────────────────┐
│ ② 技能提取        │ → LLM提取结构化信息
└────────┬───────────┘
         ▼
┌────────────────────┐
│ ③ 匹配评分        │ → LLM评分(0-100)
└────────┬───────────┘
         ▼
┌────────────────────┐
│ ④ 条件判断        │ → 70分门槛
└────┬───────────┬───┘
     │(高分≥70)  │(低分<70)
     ▼           ▼
┌─────────┐  ┌─────────┐
│⑤面试准备│  │⑥婉拒建议│
│+邮件发送│  │+邮件发送│
└────┬────┘  └────┬────┘
     └──────┬─────┘
            ▼
┌────────────────────┐
│ ⑦ 结果打包        │ → PDF报告
└────────────────────┘
```

## 节点说明

| 节点 | 类型 | 功能 |
|-----|------|------|
| resume_parse | Task | 解析 PDF/DOCX 简历文件 |
| skill_extract | Agent | LLM 提取结构化简历信息 |
| match_scoring | Agent | LLM 评估匹配度并评分 |
| score_judge | Condition | 根据分数判断后续流程 |
| interview_prep | Agent | 生成面试题和邀约邮件 |
| rejection | Agent | 生成婉拒信和学习建议 |
| result_packaging | Task | 汇总结果生成 PDF 报告 |

## 本地运行

### 运行完整流程
```bash
bash scripts/local_run.sh -m flow
```

### 运行单个节点
```bash
bash scripts/local_run.sh -m node -n resume_parse
```

### 启动 HTTP 服务
```bash
bash scripts/http_run.sh -m http -p 5000
```

## 输入输出

### 输入参数
```json
{
  "resume_file": {
    "url": "简历文件URL",
    "file_type": "document"
  },
  "job_requirements": "岗位要求描述文本"
}
```

### 输出示例

**高分候选人（≥70分）**
```json
{
  "candidate_name": "张三",
  "match_score": 85.0,
  "is_qualified": true,
  "status": "qualified",
  "interview_questions": ["问题1...", "问题2..."],
  "invitation_content": "面试邀约邮件内容...",
  "email_sent": true,
  "report_url": "https://xxx/report.pdf"
}
```

**低分候选人（<70分）**
```json
{
  "candidate_name": "李四",
  "match_score": 45.0,
  "is_qualified": false,
  "status": "rejected",
  "rejection_content": "婉拒信内容...",
  "learning_suggestions": ["建议1...", "建议2..."],
  "email_sent": true,
  "report_url": "https://xxx/report.pdf"
}
```

## 技术栈

- **框架**: LangGraph
- **语言**: Python
- **LLM**: 豆包 Seed 系列模型
- **技能**: Fetch URL, Email (IMAP/SMTP), 文档生成

## 目录结构

```
├── config/                    # LLM 配置文件
│   ├── skill_extract_llm_cfg.json
│   ├── match_scoring_llm_cfg.json
│   ├── interview_llm_cfg.json
│   └── rejection_llm_cfg.json
├── src/
│   ├── graphs/
│   │   ├── state.py          # 状态定义
│   │   ├── graph.py          # 主图编排
│   │   └── nodes/            # 节点实现
│   └── utils/
├── scripts/                   # 运行脚本
└── assets/                    # 资源文件
```

## License

MIT
