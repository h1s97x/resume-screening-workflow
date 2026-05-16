# -*- coding: utf-8 -*-
"""
节点⑥ 婉拒建议节点
功能：生成婉拒邮件和学习建议，并发送邮件
"""
import os
import json
import re
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from typing import Any, List
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from coze_workload_identity import Client as WorkloadClient
from cozeloop.decorator import observe
from graphs.state import RejectionInput, RejectionOutput


def _get_text_content(content: Any) -> str:
    """安全提取文本内容"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        if content and isinstance(content[0], str):
            return " ".join(content)
        else:
            return " ".join(
                item.get("text", "") 
                for item in content 
                if isinstance(item, dict) and item.get("type") == "text"
            )
    return str(content)


def _extract_json_from_text(text: str) -> dict:
    """从文本中提取JSON对象"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    brace_pattern = r'\{[\s\S]*\}'
    brace_match = re.search(brace_pattern, text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass
    
    raise ValueError("无法从响应中提取有效的JSON")


def _get_email_config() -> dict:
    """获取邮件配置信息"""
    client = WorkloadClient()
    email_credential = client.get_integration_credential("integration-email-imap-smtp")
    return json.loads(email_credential)


@observe
def _send_email(
    subject: str,
    content: str,
    to_addrs: List[str]
) -> dict:
    """
    发送HTML格式邮件
    
    Args:
        subject: 邮件主题
        content: 邮件正文（HTML格式）
        to_addrs: 收件人列表
        
    Returns:
        发送结果字典
    """
    try:
        config = _get_email_config()
        
        msg = MIMEText(content, "html", "utf-8")
        msg["From"] = formataddr(("HR招聘系统", config["account"]))
        msg["To"] = ", ".join(to_addrs) if to_addrs else ""
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        if not to_addrs:
            return {"status": "error", "message": "收件人为空"}
        
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        attempts = 3
        last_err = None
        
        for i in range(attempts):
            try:
                with smtplib.SMTP_SSL(
                    config["smtp_server"], 
                    config["smtp_port"], 
                    context=ctx, 
                    timeout=30
                ) as server:
                    server.ehlo()
                    server.login(config["account"], config["auth_code"])
                    server.sendmail(config["account"], to_addrs, msg.as_string())
                    server.quit()
                return {
                    "status": "success", 
                    "message": f"邮件成功发送给 {len(to_addrs)} 位收件人"
                }
            except (
                smtplib.SMTPServerDisconnected, 
                smtplib.SMTPConnectError, 
                smtplib.SMTPDataError, 
                smtplib.SMTPHeloError, 
                ssl.SSLError, 
                OSError
            ) as e:
                last_err = e
                time.sleep(1 * (i + 1))
        
        return {
            "status": "error", 
            "message": "发送失败", 
            "detail": str(last_err)
        }
    except Exception as e:
        return {"status": "error", "message": f"发送失败: {str(e)}"}


def rejection_node(
    state: RejectionInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RejectionOutput:
    """
    title: 婉拒建议
    desc: 为未通过筛选的候选人撰写婉拒邮件并提供学习发展建议，并发送邮件通知
    integrations: 大语言模型, 邮件
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_path = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""), 
        "config/rejection_llm_cfg.json"
    )
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up = cfg.get("up", "")
    
    # 渲染用户提示词
    up_template = Template(up)
    user_prompt = up_template.render(
        job_requirements=state.job_requirements,
        parsed_info=json.dumps(state.parsed_info, ensure_ascii=False, indent=2),
        match_score=state.match_score
    )
    
    # 初始化 LLM 客户端
    client = LLMClient(ctx=ctx)
    
    # 构建消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    # 调用模型
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-pro-260215"),
        temperature=llm_config.get("temperature", 0.7),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4096)
    )
    
    # 提取响应内容
    response_text = _get_text_content(response.content)
    
    # 解析JSON
    result = _extract_json_from_text(response_text)
    
    rejection_content: str = result.get("rejection_content", "")
    learning_suggestions: List[str] = result.get("learning_suggestions", [])
    
    # 发送邮件
    email_sent = False
    parsed_info = state.parsed_info
    candidate_email = ""
    
    # 获取候选人邮箱
    if isinstance(parsed_info, dict):
        contact = parsed_info.get("contact", {})
        if isinstance(contact, dict):
            candidate_email = contact.get("email", "")
    
    if candidate_email and rejection_content:
        candidate_name = parsed_info.get("name", "候选人") if isinstance(parsed_info, dict) else "候选人"
        
        # 替换邮件中的占位符
        email_content = rejection_content.replace("[候选人姓名]", candidate_name)
        
        # 添加学习建议
        if learning_suggestions:
            suggestions_html = "<br>".join(
                f"• {s}" for s in learning_suggestions
            )
            email_content += f"<br><br><b>发展建议：</b><br>{suggestions_html}"
        
        send_result = _send_email(
            subject="感谢您的投递",
            content=f"<html><body><pre>{email_content}</pre></body></html>",
            to_addrs=[candidate_email]
        )
        email_sent = send_result.get("status") == "success"
    
    return RejectionOutput(
        rejection_content=rejection_content,
        learning_suggestions=learning_suggestions,
        email_sent=email_sent
    )
