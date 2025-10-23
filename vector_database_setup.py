#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vector Database Kurulum ve Kanun Yükleme Scripti
Bu script kanunları vector database'e yükler ve arama için hazırlar.
"""

import json
import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone import Pinecone, ServerlessSpec

class KanunVectorDB:
    def __init__(self, pinecone_api_key: str = None, index_name: str = "kanunlar"):
        self.index_name = index_name
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.model = None
        self.pc = None
        self.index = None
        
        if pinecone_api_key:
            self.setup_pinecone(pinecone_api_key)
    
    def setup_pinecone(self, api_key: str):
        """Pinecone vector database'i kurar"""
        try:
            self.pc = Pinecone(api_key=api_key)
            
            # Index oluştur veya mevcut index'i al
            if self.index_name not in [index.name for index in self.pc.list_indexes()]:
                print(f"Yeni index oluşturuluyor: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # multilingual model boyutu
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            
            self.index = self.pc.Index(self.index_name)
            print(f"Pinecone index '{self.index_name}' hazır.")
            
        except Exception as e:
            print(f"Pinecone kurulum hatası: {e}")
            raise
    
    def load_embedding_model(self):
        """Türkçe embedding modelini yükler"""
        print("Embedding modeli yükleniyor...")
        self.model = SentenceTransformer(self.model_name)
        print("Model yüklendi.")
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Metinleri embedding'lere dönüştürür"""
        if not self.model:
            self.load_embedding_model()
        
        print(f"{len(texts)} metin embedding'e dönüştürülüyor...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def upload_kanunlar(self, chunks_file: str = "kanun_chunks.json"):
        """Kanun chunk'larını vector database'e yükler"""
        if not self.index:
            raise Exception("Pinecone index kurulmamış!")
        
        # Chunk'ları yükle
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"{len(chunks)} chunk yükleniyor...")
        
        # Batch'ler halinde yükle (Pinecone limiti: 100)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Embedding'leri oluştur
            texts = [chunk['text'] for chunk in batch]
            embeddings = self.create_embeddings(texts)
            
            # Pinecone formatına dönüştür
            vectors = []
            for j, chunk in enumerate(batch):
                vectors.append({
                    'id': chunk['id'],
                    'values': embeddings[j],
                    'metadata': {
                        'kanun_no': chunk['kanun_no'],
                        'baslik': chunk['baslik'],
                        'madde_no': chunk['madde_no'],
                        'yayim_tarihi': chunk['yayim_tarihi'],
                        'text': chunk['text'][:1000]  # Metadata için kısaltılmış
                    }
                })
            
            # Pinecone'a yükle
            self.index.upsert(vectors=vectors)
            print(f"Batch {i//batch_size + 1} yüklendi: {len(vectors)} vektör")
        
        print("Tüm kanunlar vector database'e yüklendi!")
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Benzer kanun maddelerini arar"""
        if not self.index:
            raise Exception("Pinecone index kurulmamış!")
        
        if not self.model:
            self.load_embedding_model()
        
        # Sorguyu embedding'e dönüştür
        query_embedding = self.model.encode([query])[0].tolist()
        
        # Pinecone'da ara
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Sonuçları formatla
        formatted_results = []
        for match in results['matches']:
            formatted_results.append({
                'id': match['id'],
                'score': match['score'],
                'kanun_no': match['metadata']['kanun_no'],
                'baslik': match['metadata']['baslik'],
                'madde_no': match['metadata']['madde_no'],
                'yayim_tarihi': match['metadata']['yayim_tarihi'],
                'text': match['metadata']['text']
            })
        
        return formatted_results

def main():
    # Pinecone API key'i al (environment variable'dan)
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    
    if not pinecone_api_key:
        print("PINECONE_API_KEY environment variable'ı ayarlanmamış!")
        print("Lütfen Pinecone'dan API key alın ve şu komutu çalıştırın:")
        print("set PINECONE_API_KEY=your_api_key_here")
        return
    
    # Vector DB'yi kur
    vector_db = KanunVectorDB(pinecone_api_key)
    
    # Kanunları yükle
    if os.path.exists("kanun_chunks.json"):
        vector_db.upload_kanunlar()
    else:
        print("kanun_chunks.json dosyası bulunamadı!")
        print("Önce kanun_processor.py'yi çalıştırın.")
        return
    
    # Test araması
    print("\nTest araması yapılıyor...")
    test_query = "vergi muafiyeti"
    results = vector_db.search_similar(test_query, top_k=3)
    
    print(f"\n'{test_query}' için sonuçlar:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['baslik']} - Madde {result['madde_no']}")
        print(f"   Skor: {result['score']:.3f}")
        print(f"   Metin: {result['text'][:200]}...")
        print()

if __name__ == "__main__":
    main()

