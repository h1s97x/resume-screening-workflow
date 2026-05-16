# -*- coding: utf-8 -*-
"""
简历智能筛选工作流 - 状态定义
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from utils.file.file import File


# ==================== 全局状态 ====================
class GlobalState(BaseModel):
    """工作流全局状态"""
    resume_file: File = Field(..., description="简历文件（PDF/DOCX）")
    job_requirements: str = Field(..., description="岗位要求描述")
    raw_text: str = Field(default="", description="简历解析后的原始文本")
    parsed_info: dict = Field(default={}, description="结构化的简历信息")
    match_score: float = Field(default=0.0, description="简历与岗位匹配分数(0-100)")
    is_qualified: bool = Field(default=False, description="是否通过筛选")
    interview_questions: List[str] = Field(default=[], description="生成的面试题目")
    invitation_content: str = Field(default="", description="面试邀约邮件内容")
    rejection_content: str = Field(default="", description="婉拒信内容")
    learning_suggestions: List[str] = Field(default=[], description="学习建议")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")
    final_result: dict = Field(default={}, description="最终结果汇总")
    report_url: str = Field(default="", description="筛选报告PDF下载链接")


# ==================== 图输入输出 ====================
class GraphInput(BaseModel):
    """工作流输入"""
    resume_file: File = Field(..., description="上传的简历文件")
    job_requirements: str = Field(..., description="岗位要求描述")


class GraphOutput(BaseModel):
    """工作流输出"""
    final_result: dict = Field(..., description="筛选结果汇总")


# ==================== 节点① 简历解析 ====================
class ResumeParseInput(BaseModel):
    """简历解析节点输入"""
    resume_file: File = Field(..., description="简历文件")
    job_requirements: str = Field(..., description="岗位要求")


class ResumeParseOutput(BaseModel):
    """简历解析节点输出"""
    raw_text: str = Field(..., description="解析后的简历文本内容")


# ==================== 节点② 技能提取 ====================
class SkillExtractInput(BaseModel):
    """技能提取节点输入"""
    raw_text: str = Field(..., description="简历原始文本")
    job_requirements: str = Field(..., description="岗位要求")


class SkillExtractOutput(BaseModel):
    """技能提取节点输出"""
    parsed_info: dict = Field(..., description="结构化的简历信息")


# ==================== 节点③ 匹配评分 ====================
class MatchScoringInput(BaseModel):
    """匹配评分节点输入"""
    parsed_info: dict = Field(..., description="结构化简历信息")
    job_requirements: str = Field(..., description="岗位要求")


class MatchScoringOutput(BaseModel):
    """匹配评分节点输出"""
    match_score: float = Field(..., description="匹配分数(0-100)")
    is_qualified: bool = Field(..., description="是否通过筛选")


# ==================== 节点④ 评分判断(条件) ====================
class ScoreJudgeInput(BaseModel):
    """评分判断节点输入"""
    match_score: float = Field(..., description="匹配分数")


# ==================== 节点⑤ 面试准备 ====================
class InterviewPrepInput(BaseModel):
    """面试准备节点输入"""
    parsed_info: dict = Field(..., description="结构化简历信息")
    match_score: float = Field(..., description="匹配分数")
    job_requirements: str = Field(..., description="岗位要求")


class InterviewPrepOutput(BaseModel):
    """面试准备节点输出"""
    interview_questions: List[str] = Field(..., description="生成的面试题目列表")
    invitation_content: str = Field(..., description="面试邀约邮件内容")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")


# ==================== 节点⑥ 婉拒建议 ====================
class RejectionInput(BaseModel):
    """婉拒建议节点输入"""
    parsed_info: dict = Field(..., description="结构化简历信息")
    match_score: float = Field(..., description="匹配分数")
    job_requirements: str = Field(..., description="岗位要求")


class RejectionOutput(BaseModel):
    """婉拒建议节点输出"""
    rejection_content: str = Field(..., description="婉拒信内容")
    learning_suggestions: List[str] = Field(..., description="学习建议列表")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")


# ==================== 节点⑦ 结果打包 ====================
class ResultPackagingInput(BaseModel):
    """结果打包节点输入"""
    parsed_info: dict = Field(default={}, description="结构化简历信息")
    match_score: float = Field(default=0.0, description="匹配分数")
    is_qualified: bool = Field(default=False, description="是否通过筛选")
    interview_questions: List[str] = Field(default=[], description="面试题目")
    invitation_content: str = Field(default="", description="邀约邮件内容")
    rejection_content: str = Field(default="", description="婉拒信内容")
    learning_suggestions: List[str] = Field(default=[], description="学习建议")
    email_sent: bool = Field(default=False, description="邮件发送状态")


class ResultPackagingOutput(BaseModel):
    """结果打包节点输出"""
    final_result: dict = Field(..., description="最终结果汇总")
    report_url: str = Field(..., description="筛选报告PDF下载链接")
