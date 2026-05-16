# -*- coding: utf-8 -*-
"""
节点⑦ 结果打包节点
功能：汇总所有数据，生成最终报告PDF
"""
from typing import List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import DocumentGenerationClient
from graphs.state import ResultPackagingInput, ResultPackagingOutput


def result_packaging_node(
    state: ResultPackagingInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ResultPackagingOutput:
    """
    title: 结果打包
    desc: 汇总筛选结果，生成简历筛选报告PDF供下载存档
    integrations: 文档生成
    """
    ctx = runtime.context
    
    # 提取候选人信息
    parsed_info = state.parsed_info
    candidate_name = "未知候选人"
    candidate_email = ""
    candidate_phone = ""
    
    if isinstance(parsed_info, dict):
        candidate_name = parsed_info.get("name", "未知候选人")
        contact = parsed_info.get("contact", {})
        if isinstance(contact, dict):
            candidate_email = contact.get("email", "")
            candidate_phone = contact.get("phone", "")
    
    # 构建Markdown报告内容
    status = "✅ 通过筛选" if state.is_qualified else "❌ 未通过筛选"
    
    report_content = f"""# 简历筛选报告

## 候选人信息

| 项目 | 内容 |
|------|------|
| 姓名 | {candidate_name} |
| 邮箱 | {candidate_email} |
| 电话 | {candidate_phone} |
| 筛选状态 | {status} |
| 匹配分数 | {state.match_score:.1f} / 100 |

---

## 筛选结果详情

### 评分说明
- 匹配分数达到 70 分及以上为通过筛选
- 本候选人得分：**{state.match_score:.1f}** 分
- 结果：**{"进入面试流程" if state.is_qualified else "未进入面试流程"}**

---

"""

    # 根据筛选结果添加不同内容
    if state.is_qualified:
        report_content += """## 面试安排

### 面试题目
"""
        if state.interview_questions:
            for i, question in enumerate(state.interview_questions, 1):
                report_content += f"\n**问题 {i}：**\n{question}\n"
        else:
            report_content += "\n暂无面试题目\n"
        
        if state.invitation_content:
            report_content += f"""
### 面试邀约邮件

```
{state.invitation_content}
```
"""
        
        report_content += f"""
### 邮件发送状态
{"✅ 邮件已发送" if state.email_sent else "❌ 邮件发送失败"}
"""
    else:
        report_content += """## 婉拒处理

### 婉拒信内容
"""
        if state.rejection_content:
            report_content += f"""
```
{state.rejection_content}
```
"""
        
        report_content += """
### 学习发展建议
"""
        if state.learning_suggestions:
            for i, suggestion in enumerate(state.learning_suggestions, 1):
                report_content += f"\n{i}. {suggestion}\n"
        else:
            report_content += "\n暂无学习建议\n"
        
        report_content += f"""

### 邮件发送状态
{"✅ 邮件已发送" if state.email_sent else "❌ 邮件发送失败"}
"""

    report_content += """
---

*本报告由简历智能筛选系统自动生成*
"""

    # 生成PDF报告
    client = DocumentGenerationClient()
    report_url = client.create_pdf_from_markdown(
        report_content, 
        "resume_screening_report"
    )
    
    # 构建最终结果
    final_result = {
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone,
        "match_score": state.match_score,
        "is_qualified": state.is_qualified,
        "status": "qualified" if state.is_qualified else "rejected",
        "interview_questions": state.interview_questions if state.is_qualified else [],
        "invitation_content": state.invitation_content if state.is_qualified else "",
        "rejection_content": state.rejection_content if not state.is_qualified else "",
        "learning_suggestions": state.learning_suggestions if not state.is_qualified else [],
        "email_sent": state.email_sent,
        "report_url": report_url
    }
    
    return ResultPackagingOutput(
        final_result=final_result,
        report_url=report_url
    )
