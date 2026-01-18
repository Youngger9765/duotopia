"""
Translation Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent
from models import (
    ProgramLevel,
    TeacherOrganization,
    TeacherSchool,
    Organization,
    School,
)
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate
from services.translation import translation_service

router = APIRouter()


@router.post("/translate")
async def translate_text(
    request: TranslateRequest, current_teacher: Teacher = Depends(get_current_teacher)
):
    """翻譯單一文本"""
    try:
        translation = await translation_service.translate_text(
            request.text, request.target_lang
        )
        return {"original": request.text, "translation": translation}
    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")


@router.post("/translate-with-pos")
async def translate_with_pos(
    request: TranslateRequest, current_teacher: Teacher = Depends(get_current_teacher)
):
    """翻譯單字並辨識詞性"""
    try:
        result = await translation_service.translate_with_pos(
            request.text, request.target_lang
        )
        return {
            "original": request.text,
            "translation": result["translation"],
            "parts_of_speech": result["parts_of_speech"],
        }
    except Exception as e:
        print(f"Translate with POS error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")


@router.post("/translate-with-pos/batch")
async def batch_translate_with_pos(
    request: BatchTranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """批次翻譯多個單字並辨識詞性"""
    try:
        results = await translation_service.batch_translate_with_pos(
            request.texts, request.target_lang
        )
        return {"originals": request.texts, "results": results}
    except Exception as e:
        print(f"Batch translate with POS error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")


@router.post("/translate/batch")
async def batch_translate(
    request: BatchTranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """批次翻譯多個文本"""
    try:
        translations = await translation_service.batch_translate(
            request.texts, request.target_lang
        )
        return {"originals": request.texts, "translations": translations}
    except Exception as e:
        print(f"Batch translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")


@router.post("/generate-sentences")
async def generate_sentences(
    request: GenerateSentencesRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """AI 生成例句"""
    try:
        sentences = await translation_service.generate_sentences(
            words=request.words,
            level=request.level,
            prompt=request.prompt,
            translate_to=request.translate_to,
            parts_of_speech=request.parts_of_speech,
        )
        return {"sentences": sentences}
    except Exception as e:
        print(f"Generate sentences error: {e}")
        raise HTTPException(status_code=500, detail="Generate sentences failed")
