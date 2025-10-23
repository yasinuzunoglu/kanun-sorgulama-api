#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Gist'ten Kanun Dosyalarını Çeken Script
Bu script GitHub Gist'teki kanun dosyalarını çeker ve işler.
"""

import requests
import json
import re
from typing import List, Dict, Any
import time
from urllib.parse import urlparse

class GistKanunLoader:
    def __init__(self, gist_url: str):
        self.gist_url = gist_url
        self.kanun_urls = []
        self.processed_kanunlar = []
    
    def load_gist_urls(self) -> List[str]:
        """Gist'ten tüm kanun URL'lerini çeker"""
        try:
            response = requests.get(self.gist_url)
            response.raise_for_status()
            
            # URL'leri çıkar
            urls = response.text.strip().split('\n')
            self.kanun_urls = [url.strip() for url in urls if url.strip()]
            
            print(f"Toplam {len(self.kanun_urls)} kanun URL'si bulundu.")
            return self.kanun_urls
            
        except Exception as e:
            print(f"Gist URL'leri yüklenirken hata: {e}")
            return []
    
    def parse_kanun_from_url(self, url: str) -> Dict[str, Any]:
        """Tek bir kanun URL'sinden kanun verisini çıkarır"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            
            # URL'den dosya adını çıkar
            parsed_url = urlparse(url)
            filename = parsed_url.path.split('/')[-1]
            kanun_no = filename.replace('.txt', '')
            
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
                'gist_url': url
            }
            
        except Exception as e:
            print(f"Hata: {url} dosyası işlenirken hata oluştu: {e}")
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
    
    def load_all_kanunlar(self, max_kanunlar: int = None) -> List[Dict[str, Any]]:
        """Tüm kanunları Gist'ten yükler"""
        if not self.kanun_urls:
            self.load_gist_urls()
        
        if not self.kanun_urls:
            print("Kanun URL'leri bulunamadı!")
            return []
        
        # Maksimum kanun sayısını ayarla (test için)
        urls_to_process = self.kanun_urls
        if max_kanunlar:
            urls_to_process = self.kanun_urls[:max_kanunlar]
        
        print(f"{len(urls_to_process)} kanun yükleniyor...")
        
        processed_count = 0
        for i, url in enumerate(urls_to_process):
            print(f"İşleniyor ({i+1}/{len(urls_to_process)}): {url}")
            
            kanun_data = self.parse_kanun_from_url(url)
            
            if kanun_data:
                self.processed_kanunlar.append(kanun_data)
                processed_count += 1
            
            # Rate limiting için kısa bekleme
            time.sleep(0.1)
            
            if processed_count % 50 == 0:
                print(f"İşlenen kanun sayısı: {processed_count}")
        
        print(f"Toplam {processed_count} kanun başarıyla yüklendi.")
        return self.processed_kanunlar
    
    def save_to_json(self, output_file: str = "kanunlar_gist.json"):
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
                    'yayim_tarihi': kanun['yayim_tarihi'],
                    'gist_url': kanun['gist_url']
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
                    'yayim_tarihi': kanun['yayim_tarihi'],
                    'gist_url': kanun['gist_url']
                })
        
        return chunks

def main():
    # Gist URL'si
    gist_url = "https://gist.githubusercontent.com/yasinuzunoglu/e17910de5ef97cf1763def88d7f7bec2/raw/56bbfc87c01ef78af791521ac35470ee0526673f/tumlinkler"
    
    # Kanun loader'ı oluştur
    loader = GistKanunLoader(gist_url)
    
    print("GitHub Gist'ten kanunlar yükleniyor...")
    # Test için ilk 10 kanunu yükle (tümünü yüklemek için max_kanunlar=None yapın)
    kanunlar = loader.load_all_kanunlar(max_kanunlar=10)
    
    if kanunlar:
        # JSON'a kaydet
        loader.save_to_json("kanunlar_gist_sample.json")
        
        # Arama chunk'larını oluştur
        print("Arama chunk'ları oluşturuluyor...")
        chunks = loader.create_searchable_chunks()
        
        # Chunk'ları JSON'a kaydet
        with open("kanun_chunks_gist.json", 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"Toplam {len(chunks)} arama chunk'ı oluşturuldu.")
        
        # Örnek kanun bilgisi göster
        print(f"\nÖrnek kanun: {kanunlar[0]['baslik']}")
        print(f"Madde sayısı: {len(kanunlar[0]['maddeler'])}")
        print(f"Geçici madde sayısı: {len(kanunlar[0]['gecici_maddeler'])}")
    
    print("İşlem tamamlandı!")

if __name__ == "__main__":
    main()
