#!/usr/bin/env python
"""檢查 AI 評估結果是否有儲存到資料庫"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).parent.parent / ".env.local")

from models import StudentContentProgress  # noqa: E402

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()

print("檢查最近的 AI 評估結果...")

# 查詢有 ai_scores 的記錄
results = (
    session.query(StudentContentProgress)
    .filter(StudentContentProgress.ai_scores.isnot(None))
    .order_by(StudentContentProgress.completed_at.desc())
    .limit(5)
)

for progress in results:
    print(f"\nProgress ID: {progress.id}")
    print(f"Status: {progress.status}")
    print(f"Completed at: {progress.completed_at}")
    print(f"AI Scores: {progress.ai_scores}")
    if progress.response_data:
        print(f"Response data: {progress.response_data}")

session.close()
