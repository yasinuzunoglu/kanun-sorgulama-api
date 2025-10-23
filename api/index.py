from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import re
from typing import List, Dict, Any, Optional
import os
import uvicorn

app = FastAPI(title="Kanun Sorgulama API", version="1.0.0")

# Basit test için
class QuestionRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5

class QuestionResponse(BaseModel):
    question: str
    answers: List[Dict[str, Any]]
    total_found: int
    status: str

@app.get("/")
async def root():
    """Ana sayfa"""
    return {
        "message": "Kanun Sorgulama API - Railway",
        "version": "1.0.0",
        "status": "ready",
        "endpoints": {
            "ask": "/ask",
            "health": "/health"
        }
    }

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Kanun sorusu sorar - Basit test versiyonu"""
    try:
        # Basit test cevabı
        test_answers = [
            {
                "kanun_no": "test_001",
                "baslik": "Test Kanunu",
                "madde_no": 1,
                "yayim_tarihi": "2024-01-01",
                "gist_url": "https://example.com",
                "text": f"Test cevabı: {request.question}",
                "similarity_score": 0.95
            }
        ]
        
        return QuestionResponse(
            question=request.question,
            answers=test_answers,
            total_found=len(test_answers),
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Soru işlenirken hata: {str(e)}")

@app.get("/health")
async def health_check():
    """Sistem durumu kontrolü"""
    return {
        "status": "healthy",
        "message": "API çalışıyor"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)