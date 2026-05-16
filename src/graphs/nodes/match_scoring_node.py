# -*- coding: utf-8 -*-
"""
节点③ 匹配评分节点
功能：评估候选人与岗位的匹配程度，给出评分
"""
import os
import json
import re
from typing import Any
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import MatchScoringInput, MatchScoringOutput


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


def match_scoring_node(
    state: MatchScoringInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> MatchScoringOutput:
    """
    title: 匹配评分
    desc: 根据岗位要求对候选人简历进行匹配度评分，判断是否通过筛选（70分为门槛）
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_path = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""), 
        "config/match_scoring_llm_cfg.json"
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
        parsed_info=json.dumps(state.parsed_info, ensure_ascii=False, indent=2)
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
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=llm_config.get("temperature", 0.3),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2048)
    )
    
    # 提取响应内容
    response_text = _get_text_content(response.content)
    
    # 解析JSON
    result = _extract_json_from_text(response_text)
    
    # 提取评分和是否通过
    match_score = float(result.get("match_score", 0.0))
    is_qualified = bool(result.get("is_qualified", match_score >= 70))
    
    return MatchScoringOutput(
        match_score=match_score,
        is_qualified=is_qualified
    )
