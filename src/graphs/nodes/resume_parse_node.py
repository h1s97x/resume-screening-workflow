# -*- coding: utf-8 -*-
"""
节点① 简历解析节点
功能：解析 PDF/DOCX 简历文件，提取原始文本内容
"""
import os
import json
from typing import Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.fetch import FetchClient
from graphs.state import ResumeParseInput, ResumeParseOutput


def resume_parse_node(
    state: ResumeParseInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ResumeParseOutput:
    """
    title: 简历解析
    desc: 解析上传的简历文件(PDF/DOCX)，提取原始文本内容供后续处理
    integrations: Fetch URL
    """
    ctx = runtime.context
    
    # 获取简历文件URL
    resume_file: Any = state.resume_file
    file_url: str = ""
    
    # 处理 File 类型
    if hasattr(resume_file, 'url'):
        file_url = resume_file.url
    elif isinstance(resume_file, dict):
        file_url = resume_file.get("url", "")
    elif isinstance(resume_file, str):
        file_url = resume_file
    
    if not file_url:
        raise ValueError("简历文件URL为空，无法解析")
    
    # 使用 FetchClient 解析文档
    client = FetchClient(ctx=ctx)
    
    try:
        response = client.fetch(url=file_url)
        
        if response.status_code != 0:
            raise Exception(f"文档解析失败: {response.status_message}")
        
        # 提取文本内容
        text_parts: list[str] = []
        for item in response.content:
            if hasattr(item, 'type') and item.type == "text":
                text_content = getattr(item, 'text', '')
                if text_content:
                    text_parts.append(text_content)
        
        raw_text = "\n".join(text_parts)
        
        if not raw_text.strip():
            raise Exception("简历解析结果为空，请检查文件格式")
        
        return ResumeParseOutput(raw_text=raw_text)
        
    except Exception as e:
        raise Exception(f"简历解析异常: {str(e)}")
