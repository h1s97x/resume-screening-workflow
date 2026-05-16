# -*- coding: utf-8 -*-
"""
简历智能筛选工作流 - 主图编排
"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

# 导入状态定义
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    ScoreJudgeInput
)

# 导入节点函数
from graphs.nodes.resume_parse_node import resume_parse_node
from graphs.nodes.skill_extract_node import skill_extract_node
from graphs.nodes.match_scoring_node import match_scoring_node
from graphs.nodes.score_judge_node import score_judge
from graphs.nodes.interview_prep_node import interview_prep_node
from graphs.nodes.rejection_node import rejection_node
from graphs.nodes.result_packaging_node import result_packaging_node


# ==================== 创建状态图 ====================
builder = StateGraph(
    GlobalState, 
    input_schema=GraphInput, 
    output_schema=GraphOutput
)

# ==================== 添加节点 ====================

# 节点① 简历解析（Task节点）
builder.add_node("resume_parse", resume_parse_node)

# 节点② 技能提取（Agent节点）
builder.add_node(
    "skill_extract", 
    skill_extract_node,
    metadata={
        "type": "agent", 
        "llm_cfg": "config/skill_extract_llm_cfg.json"
    }
)

# 节点③ 匹配评分（Agent节点）
builder.add_node(
    "match_scoring", 
    match_scoring_node,
    metadata={
        "type": "agent", 
        "llm_cfg": "config/match_scoring_llm_cfg.json"
    }
)

# 节点⑤ 面试准备（Agent节点）
builder.add_node(
    "interview_prep", 
    interview_prep_node,
    metadata={
        "type": "agent", 
        "llm_cfg": "config/interview_llm_cfg.json"
    }
)

# 节点⑥ 婉拒建议（Agent节点）
builder.add_node(
    "rejection", 
    rejection_node,
    metadata={
        "type": "agent", 
        "llm_cfg": "config/rejection_llm_cfg.json"
    }
)

# 节点⑦ 结果打包（Task节点）
builder.add_node("result_packaging", result_packaging_node)


# ==================== 设置入口点 ====================
builder.set_entry_point("resume_parse")


# ==================== 添加边 ====================

# 简历解析 -> 技能提取
builder.add_edge("resume_parse", "skill_extract")

# 技能提取 -> 匹配评分
builder.add_edge("skill_extract", "match_scoring")

# 匹配评分 -> 条件判断
builder.add_conditional_edges(
    source="match_scoring",
    path=score_judge,
    path_map={
        "安排面试": "interview_prep",
        "发送婉拒": "rejection"
    }
)

# 面试准备 -> 结果打包
builder.add_edge("interview_prep", "result_packaging")

# 婉拒建议 -> 结果打包
builder.add_edge("rejection", "result_packaging")

# 结果打包 -> END
builder.add_edge("result_packaging", END)


# ==================== 编译图 ====================
main_graph = builder.compile()
