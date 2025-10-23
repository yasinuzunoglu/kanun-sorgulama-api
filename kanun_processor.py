#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kanun Dosyalarını Vector Database'e Yükleyen Script
Bu script kanun dosyalarını okuyup vector database'e yükler.
"""

import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path
import hashlib

class KanunProcessor:
    def __init__(self, kanun_folder: str):
        self.kanun_folder = Path(kanun_folder)
        self.processed_kanunlar = []
    
    def parse_kanun_file(self, file_path: Path) -> Dict[str, Any]:
        """Tek bir kanun dosyasını parse eder"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Dosya adından kanun numarasını çıkar
            kanun_no = file_path.stem
            
            # İlk satırdan kanun başlığını al
            lines = content.split('\n')
            baslik = lines[0].strip() if lines else "Bilinmeyen Kanun"
            
            # Tarih bilgilerini çıkar
            tarih_pattern = r'Yayımlandığı Resmî Gazete Tarihi: (\d{2}\.\d{2}\.\d{4})'
            tarih_match = re.search(tarih_pattern, content)
            yayim_tarihi = tarih_match.group(1) if tarih_match else None
            
            # Madde numaralarını ve içeriklerini çıkar
            maddeler = self.extract_maddeler(content)
            
            # Geçici maddeleri çıkar
            gecici_maddeler = self.extract_gecici_maddeler(content)
            
            return {
                'kanun_no': kanun_no,
                'baslik': baslik,
                'yayim_tarihi': yayim_tarihi,
                'maddeler': maddeler,
                'gecici_maddeler': gecici_maddeler,
                'full_content': content,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            print(f"Hata: {file_path} dosyası işlenirken hata oluştu: {e}")
            return None
    
    def extract_maddeler(self, content: str) -> List[Dict[str, str]]:
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
    
    def extract_gecici_maddeler(self, content: str) -> List[Dict[str, str]]:
        """Geçici maddeleri çıkarır"""
        gecici_maddeler = []
        
        # Geçici madde pattern'i
        gecici_pattern = r'Geçici Madde\s+(\d+):\s*(.*?)(?=Geçici Madde\s+\d+:|Madde\s+\d+:|$)'
        matches = re.findall(gecici_pattern, content, re.DOTALL)
        
        for madde_no, madde_icerik in matches:
            madde_icerik = madde_icerik.strip()
            if madde_icerik:
                gecici_maddeler.append({
                    'madde_no': int(madde_no),
                    'icerik': madde_icerik
                })
        
        return gecici_maddeler
    
    def process_all_kanunlar(self) -> List[Dict[str, Any]]:
        """Tüm kanun dosyalarını işler"""
        txt_files = list(self.kanun_folder.glob("*.txt"))
        print(f"Toplam {len(txt_files)} kanun dosyası bulundu.")
        
        processed_count = 0
        for file_path in txt_files:
            print(f"İşleniyor: {file_path.name}")
            kanun_data = self.parse_kanun_file(file_path)
            
            if kanun_data:
                self.processed_kanunlar.append(kanun_data)
                processed_count += 1
            
            if processed_count % 100 == 0:
                print(f"İşlenen dosya sayısı: {processed_count}")
        
        print(f"Toplam {processed_count} kanun başarıyla işlendi.")
        return self.processed_kanunlar
    
    def save_to_json(self, output_file: str = "kanunlar_processed.json"):
        """İşlenen kanunları JSON dosyasına kaydeder"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_kanunlar, f, ensure_ascii=False, indent=2)
        print(f"Kanunlar {output_file} dosyasına kaydedildi.")
    
    def create_searchable_chunks(self) -> List[Dict[str, Any]]:
        """Arama için chunk'lar oluşturur"""
        chunks = []
        
        for kanun in self.processed_kanunlar:
            # Her madde için ayrı chunk
            for madde in kanun['maddeler']:
                chunk_text = f"Kanun: {kanun['baslik']}\nMadde {madde['madde_no']}: {madde['icerik']}"
                chunks.append({
                    'id': f"{kanun['kanun_no']}_madde_{madde['madde_no']}",
                    'text': chunk_text,
                    'kanun_no': kanun['kanun_no'],
                    'baslik': kanun['baslik'],
                    'madde_no': madde['madde_no'],
                    'yayim_tarihi': kanun['yayim_tarihi']
                })
            
            # Geçici maddeler için chunk
            for gecici_madde in kanun['gecici_maddeler']:
                chunk_text = f"Kanun: {kanun['baslik']}\nGeçici Madde {gecici_madde['madde_no']}: {gecici_madde['icerik']}"
                chunks.append({
                    'id': f"{kanun['kanun_no']}_gecici_{gecici_madde['madde_no']}",
                    'text': chunk_text,
                    'kanun_no': kanun['kanun_no'],
                    'baslik': kanun['baslik'],
                    'madde_no': f"Geçici {gecici_madde['madde_no']}",
                    'yayim_tarihi': kanun['yayim_tarihi']
                })
        
        return chunks

def main():
    # Kanun klasörünü işle
    processor = KanunProcessor(".")
    
    print("Kanun dosyaları işleniyor...")
    processor.process_all_kanunlar()
    
    # JSON'a kaydet
    processor.save_to_json()
    
    # Arama chunk'larını oluştur
    print("Arama chunk'ları oluşturuluyor...")
    chunks = processor.create_searchable_chunks()
    
    # Chunk'ları JSON'a kaydet
    with open("kanun_chunks.json", 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    print(f"Toplam {len(chunks)} arama chunk'ı oluşturuldu.")
    print("İşlem tamamlandı!")

if __name__ == "__main__":
    main()

