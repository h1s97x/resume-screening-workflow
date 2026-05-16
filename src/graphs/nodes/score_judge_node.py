# -*- coding: utf-8 -*-
"""
节点④ 评分判断节点（条件分支）
功能：根据匹配分数决定后续流程：安排面试 or 发送婉拒
"""
from graphs.state import ScoreJudgeInput


def score_judge(state: ScoreJudgeInput) -> str:
    """
    title: 评分判断
    desc: 根据匹配分数决定后续流程（70分为门槛，高分安排面试，低分发送婉拒）
    """
    if state.match_score >= 70:
        return "安排面试"
    else:
        return "发送婉拒"
