# n8n.com Kanun Sorgulama Sistemi Kurulum Rehberi

## 🎯 Proje Özeti
GitHub Gist'teki 2396 kanunu kullanarak n8n.com ile entegre edilmiş soru-cevap sistemi.

## 📋 Gereksinimler
- Python 3.8+
- n8n.com hesabı (ücretsiz)
- GitHub Gist erişimi

## 🚀 Kurulum Adımları

### 1. Python Paketlerini Yükleyin
```bash
pip install -r requirements_n8n.txt
```

### 2. API Server'ı Başlatın
```bash
python n8n_api_server.py
```
Server http://localhost:8000 adresinde çalışacak.

### 3. n8n.com Workflow Kurulumu

#### Adım 3.1: n8n.com'a Giriş Yapın
- https://n8n.com adresine gidin
- Ücretsiz hesap oluşturun

#### Adım 3.2: Yeni Workflow Oluşturun
1. "Create workflow" butonuna tıklayın
2. Workflow adını "Kanun Sorgulama" olarak ayarlayın

#### Adım 3.3: Webhook Node Ekleyin
1. "+" butonuna tıklayın
2. "Webhook" node'unu seçin
3. Ayarlar:
   - HTTP Method: POST
   - Path: `/kanun-sorgula`
   - Response Mode: "On Received"

#### Adım 3.4: HTTP Request Node Ekleyin
1. Webhook'tan sonra "+" butonuna tıklayın
2. "HTTP Request" node'unu seçin
3. Ayarlar:
   - Method: POST
   - URL: `http://localhost:8000/ask`
   - Headers: `Content-Type: application/json`
   - Body: 
   ```json
   {
     "question": "{{ $json.question }}",
     "max_results": 5
   }
   ```

#### Adım 3.5: Code Node Ekleyin (Opsiyonel)
1. HTTP Request'ten sonra "+" butonuna tıklayın
2. "Code" node'unu seçin
3. JavaScript kodu:
```javascript
// Yanıtları formatla
const answers = $input.first().json.answers;

let response = `Soru: ${$input.first().json.question}\n\n`;
response += `Bulunan ${answers.length} sonuç:\n\n`;

answers.forEach((answer, index) => {
  response += `${index + 1}. ${answer.baslik}\n`;
  response += `   Madde ${answer.madde_no}\n`;
  response += `   Benzerlik: ${(answer.similarity_score * 100).toFixed(1)}%\n`;
  response += `   Metin: ${answer.text.substring(0, 200)}...\n\n`;
});

return { response };
```

#### Adım 3.6: Response Node Ekleyin
1. Son node'tan sonra "+" butonuna tıklayın
2. "Respond to Webhook" node'unu seçin
3. Ayarlar:
   - Response Body: `{{ $json.response }}`

### 4. Workflow'u Test Edin
1. "Test workflow" butonuna tıklayın
2. Webhook URL'sini kopyalayın
3. Postman veya curl ile test edin:

```bash
curl -X POST "WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"question": "vergi muafiyeti nedir?"}'
```

## 🔧 Gelişmiş Ayarlar

### Tüm Kanunları Yüklemek İçin
`n8n_api_server.py` dosyasında:
```python
# Satır 95'teki limit'i kaldırın:
urls_to_load = gist_urls  # [:50] kısmını silin
```

### Vector Database Entegrasyonu (Opsiyonel)
Daha hızlı arama için Pinecone entegrasyonu:
```bash
pip install pinecone-client
```

## 📱 Kullanım Örnekleri

### Webhook URL'si ile Soru Sorma
```bash
curl -X POST "https://your-n8n-instance.com/webhook/kanun-sorgula" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "işçi hakları nelerdir?"
  }'
```

### Slack Entegrasyonu
1. Slack node ekleyin
2. Webhook'tan Slack'e mesaj gönderin
3. Kullanıcılar Slack'ten kanun soruları sorabilir

### WhatsApp Entegrasyonu
1. WhatsApp Business API node ekleyin
2. Mesajları otomatik olarak kanun sistemine yönlendirin

## 🛠️ Sorun Giderme

### API Server Çalışmıyor
- Port 8000'in boş olduğundan emin olun
- Python paketlerinin yüklü olduğunu kontrol edin

### n8n Webhook Çalışmıyor
- Webhook URL'sinin doğru olduğunu kontrol edin
- API server'ın çalıştığını kontrol edin

### Yavaş Yanıt
- Daha az kanun yükleyin (test için)
- Vector database kullanın

## 📊 Performans Optimizasyonu

1. **Caching**: Redis ekleyin
2. **Load Balancing**: Nginx kullanın
3. **Database**: PostgreSQL + pgvector
4. **CDN**: CloudFlare ekleyin

## 🔒 Güvenlik

- API key authentication ekleyin
- Rate limiting uygulayın
- HTTPS kullanın
- Input validation yapın
