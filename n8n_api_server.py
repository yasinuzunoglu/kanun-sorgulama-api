#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n.com için Kanun Sorgulama API Server
Bu server n8n.com'dan gelen soruları alır ve GitHub Gist'teki kanunlardan cevap verir.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import re
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Kanun Sorgulama API", version="1.0.0")

# Global değişkenler
kanun_data = []
model = None
gist_url = "https://gist.githubusercontent.com/yasinuzunoglu/e17910de5ef97cf1763def88d7f7bec2/raw/56bbfc87c01ef78af791521ac35470ee0526673f/tumlinkler"

class QuestionRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5

class QuestionResponse(BaseModel):
    question: str
    answers: List[Dict[str, Any]]
    total_found: int

def load_kanun_from_gist(gist_url: str) -> Dict[str, Any]:
    """Tek bir kanun dosyasını Gist'ten yükler"""
    try:
        response = requests.get(gist_url)
        response.raise_for_status()
        content = response.text
        
        # URL'den dosya adını çıkar
        filename = gist_url.split('/')[-1]
        kanun_no = filename.replace('.txt', '')
        
        # İlk satırdan kanun başlığını al
        lines = content.split('\n')
        baslik = lines[0].strip() if lines else "Bilinmeyen Kanun"
        
        # Tarih bilgilerini çıkar
        tarih_pattern = r'Yayımlandığı Resmî Gazete Tarihi: (\d{2}\.\d{2}\.\d{4})'
        tarih_match = re.search(tarih_pattern, content)
        yayim_tarihi = tarih_match.group(1) if tarih_match else None
        
        # Madde numaralarını ve içeriklerini çıkar
        maddeler = extract_maddeler(content)
        
        return {
            'kanun_no': kanun_no,
            'baslik': baslik,
            'yayim_tarihi': yayim_tarihi,
            'maddeler': maddeler,
            'full_content': content,
            'gist_url': gist_url
        }
        
    except Exception as e:
        print(f"Hata: {gist_url} dosyası yüklenirken hata oluştu: {e}")
        return None

def extract_maddeler(content: str) -> List[Dict[str, str]]:
    """Kanun metninden maddeleri çıkarır"""
    maddeler = []
    
    # Madde pattern'i: "Madde 0001:" veya "Madde 1:"
    madde_pattern = r'Madde\s+(\d+):\s*(.*?)(?=Madde\s+\d+:|Geçici Madde|$)'
    matches = re.findall(madde_pattern, content, re.DOTALL)
    
    for madde_no, madde_icerik in matches:
        # Madde içeriğini temizle
        madde_icerik = madde_icerik.strip()
        if madde_icerik:
            maddeler.append({
                'madde_no': int(madde_no),
                'icerik': madde_icerik
            })
    
    return maddeler

def load_all_gist_urls() -> List[str]:
    """Gist'ten tüm kanun URL'lerini çeker"""
    try:
        response = requests.get(gist_url)
        response.raise_for_status()
        
        # URL'leri çıkar
        urls = response.text.strip().split('\n')
        return [url.strip() for url in urls if url.strip()]
        
    except Exception as e:
        print(f"Gist URL'leri yüklenirken hata: {e}")
        return []

def search_kanunlar(question: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Soruyu kanunlarda arar ve en uygun sonuçları döndürür"""
    global kanun_data, model
    
    if not kanun_data:
        return []
    
    if not model:
        return []
    
    # Soruyu embedding'e dönüştür
    question_embedding = model.encode([question])
    
    # Tüm kanun maddelerini embedding'e dönüştür
    all_texts = []
    all_metadata = []
    
    for kanun in kanun_data:
        for madde in kanun['maddeler']:
            text = f"Kanun: {kanun['baslik']}\nMadde {madde['madde_no']}: {madde['icerik']}"
            all_texts.append(text)
            all_metadata.append({
                'kanun_no': kanun['kanun_no'],
                'baslik': kanun['baslik'],
                'madde_no': madde['madde_no'],
                'yayim_tarihi': kanun['yayim_tarihi'],
                'gist_url': kanun['gist_url'],
                'text': text
            })
    
    if not all_texts:
        return []
    
    # Embedding'leri oluştur
    text_embeddings = model.encode(all_texts)
    
    # Cosine similarity hesapla
    similarities = cosine_similarity(question_embedding, text_embeddings)[0]
    
    # En yüksek skorlu sonuçları al
    top_indices = np.argsort(similarities)[::-1][:max_results]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.1:  # Minimum similarity threshold
            metadata = all_metadata[idx]
            results.append({
                'kanun_no': metadata['kanun_no'],
                'baslik': metadata['baslik'],
                'madde_no': metadata['madde_no'],
                'yayim_tarihi': metadata['yayim_tarihi'],
                'gist_url': metadata['gist_url'],
                'text': metadata['text'],
                'similarity_score': float(similarities[idx])
            })
    
    return results

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatıldığında çalışır"""
    global kanun_data, model
    
    print("Kanun Sorgulama API başlatılıyor...")
    
    # Embedding modelini yükle
    print("Embedding modeli yükleniyor...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    print("Model yüklendi.")
    
    # Kanun URL'lerini yükle
    print("Kanun URL'leri yükleniyor...")
    gist_urls = load_all_gist_urls()
    
    if not gist_urls:
        print("Kanun URL'leri bulunamadı!")
        return
    
    print(f"Toplam {len(gist_urls)} kanun URL'si bulundu.")
    
    # İlk 50 kanunu yükle (test için - tümünü yüklemek için limit'i kaldırın)
    urls_to_load = gist_urls[:50]
    print(f"İlk {len(urls_to_load)} kanun yükleniyor...")
    
    for i, url in enumerate(urls_to_load):
        print(f"Yükleniyor ({i+1}/{len(urls_to_load)}): {url}")
        kanun = load_kanun_from_gist(url)
        if kanun:
            kanun_data.append(kanun)
    
    print(f"Toplam {len(kanun_data)} kanun yüklendi.")
    print("API hazır!")

@app.get("/")
async def root():
    """Ana sayfa"""
    return {
        "message": "Kanun Sorgulama API",
        "version": "1.0.0",
        "loaded_kanunlar": len(kanun_data),
        "status": "ready"
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Kanun sorusu sorar"""
    try:
        results = search_kanunlar(request.question, request.max_results)
        
        return QuestionResponse(
            question=request.question,
            answers=results,
            total_found=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Soru işlenirken hata: {str(e)}")

@app.get("/kanunlar")
async def get_kanunlar():
    """Yüklenen kanunların listesini döndürür"""
    return {
        "total": len(kanun_data),
        "kanunlar": [
            {
                "kanun_no": kanun['kanun_no'],
                "baslik": kanun['baslik'],
                "yayim_tarihi": kanun['yayim_tarihi'],
                "madde_sayisi": len(kanun['maddeler'])
            }
            for kanun in kanun_data
        ]
    }

@app.get("/health")
async def health_check():
    """Sistem durumu kontrolü"""
    return {
        "status": "healthy",
        "kanun_sayisi": len(kanun_data),
        "model_loaded": model is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
