# 项目概述

- **名称**: 简历智能筛选与面试官
- **功能**: 自动解析简历、评估匹配度、生成面试题/婉拒信、发送邮件、输出筛选报告

## 节点清单

| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| resume_parse | `nodes/resume_parse_node.py` | task | 解析PDF/DOCX简历，提取原始文本 | - | - |
| skill_extract | `nodes/skill_extract_node.py` | agent | 使用LLM提取结构化简历信息 | - | `config/skill_extract_llm_cfg.json` |
| match_scoring | `nodes/match_scoring_node.py` | agent | 评估简历与岗位匹配度，给出评分 | - | `config/match_scoring_llm_cfg.json` |
| score_judge | `nodes/score_judge_node.py` | condition | 根据分数判断后续流程 | ≥70分→interview_prep, <70分→rejection | - |
| interview_prep | `nodes/interview_prep_node.py` | agent | 生成面试题和邀约邮件，发送邮件 | - | `config/interview_llm_cfg.json` |
| rejection | `nodes/rejection_node.py` | agent | 生成婉拒信和学习建议，发送邮件 | - | `config/rejection_llm_cfg.json` |
| result_packaging | `nodes/result_packaging_node.py` | task | 汇总结果，生成PDF报告 | - | - |

**类型说明**: task(普通任务节点) / agent(大模型节点) / condition(条件分支节点)

## 工作流结构

```
resume_parse → skill_extract → match_scoring → score_judge
                                                    │
                                    ┌───────────────┴───────────────┐
                                    │                               │
                                    ▼                               ▼
                            interview_prep                    rejection
                                    │                               │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                           result_packaging → END
```

## 技能使用

| 节点 | 技能 | 用途 |
|-----|------|------|
| resume_parse | Fetch URL | 解析简历文档，提取文本内容 |
| skill_extract | 大语言模型 | 结构化提取简历信息 |
| match_scoring | 大语言模型 | 匹配度评分 |
| interview_prep | 大语言模型 + 邮件 | 生成面试题/邀约邮件并发送 |
| rejection | 大语言模型 + 邮件 | 生成婉拒信/建议并发送 |
| result_packaging | 文档生成 | 生成PDF筛选报告 |

## 配置文件说明

| 文件 | 模型 | 温度 | 用途 |
|-----|------|------|------|
| `skill_extract_llm_cfg.json` | doubao-seed-2-0-lite-260215 | 0.3 | 简历信息提取 |
| `match_scoring_llm_cfg.json` | doubao-seed-2-0-lite-260215 | 0.3 | 匹配度评分 |
| `interview_llm_cfg.json` | doubao-seed-2-0-pro-260215 | 0.7 | 面试题目生成 |
| `rejection_llm_cfg.json` | doubao-seed-2-0-pro-260215 | 0.7 | 婉拒信生成 |

## 输入输出

### 输入
- `resume_file`: 简历文件 (PDF/DOCX)
- `job_requirements`: 岗位要求描述文本

### 输出
- `final_result`: 筛选结果汇总 (dict)
  - `candidate_name`: 候选人姓名
  - `match_score`: 匹配分数
  - `is_qualified`: 是否通过筛选
  - `interview_questions`: 面试题目列表
  - `rejection_content`: 婉拒信内容
  - `learning_suggestions`: 学习建议
  - `email_sent`: 邮件发送状态
  - `report_url`: PDF报告下载链接
