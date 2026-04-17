# -*- coding: utf-8 -*-
"""
冲突检测路由

GET /api/conflicts/{version_id}          完整冲突详情
GET /api/conflicts/{version_id}/summary  仅 summary（轻量）
"""
from fastapi import APIRouter, HTTPException
from app.services.conflict_analyzer import analyze_conflicts

router = APIRouter()


@router.get("/{version_id}/summary")
async def get_conflict_summary(version_id: int):
    result = analyze_conflicts(version_id)
    return {"version_id": version_id, "summary": result["summary"]}


@router.get("/{version_id}")
async def get_conflicts(version_id: int):
    return analyze_conflicts(version_id)
