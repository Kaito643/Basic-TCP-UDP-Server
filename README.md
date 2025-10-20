# Python Stdlib TCP HTTP + UDP Health Server

Basit bir eğitim projesi: Python standart kütüphane ile TCP tabanlı HTTP sunucusu ve UDP "health" servisi.

## Özellikler
- TCP HTTP: `GET` ve `HEAD`, basit routing (`/`, `/health`, `/static/...`), statik dosya servisi
- UDP Health: `PING` paketine `PONG <ISO_TIME>` yanıtı
- Ortak konfig: env değişkenleri ve CLI argümanları
- Logging: zaman damgalı, sade format
- Graceful shutdown: `SIGINT/SIGTERM`

## Proje Yapısı
```
HTTP Server/
  common/
    config.py
    logging_setup.py
    signals.py
  tcp_http/
    http_utils.py
    handlers.py
    server.py
  udp_health/
    server.py
  static/
    index.html
  main.py
  README.md
  .gitignore
```

## Gereksinimler
- Python 3.10+ (test: 3.13.7)

## Çalıştırma
- İkisini birden (varsayılan TCP 8080, UDP 9999):
```bash
python3 "./main.py" --both
```
- Sadece HTTP:
```bash
python3 "./main.py" --tcp
```
- Sadece UDP:
```bash
python3 "./main.py" --udp
```

## Konfigürasyon
- Ortam değişkenleri (opsiyonel):
  - `HOST` (varsayılan: `0.0.0.0`)
  - `TCP_PORT` (varsayılan: `8080`)
  - `UDP_PORT` (varsayılan: `9999`)
  - `READ_TIMEOUT` (varsayılan: `5` saniye)
  - `MAX_REQUEST_LINE_BYTES` (varsayılan: `4096`)
  - `MAX_HEADER_BYTES` (varsayılan: `16384`)
  - `STATIC_DIR` (varsayılan: `static`)
- CLI argümanları env’i geçersiz kılar:
```bash
python3 main.py --both --host 0.0.0.0 --tcp-port 8000 --udp-port 9000 --log-level DEBUG
```

## HTTP Uç Noktaları
- `/` → `static/index.html` döner
- `/health` → `200 OK` ve JSON: `{ "status": "ok", "time": "..." }`
- `/static/<dosya>` → `static/` altındaki dosyaları döner

`HEAD` aynı `GET` başlıklarını döner, gövde olmadan.

## UDP Protokolü
- İstek: `PING`
- Yanıt: `PONG 2025-10-20T12:34:56.789012Z` (UTC ISO-8601, `Z`)
- Sunucu, boş veya bilinmeyen datagramlara yanıt vermez (gürültüyü azaltmak için).

## Testler

### HTTP
```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/health
curl -I http://localhost:8080/
```
Beklenen: `200 OK` ve ana sayfa/JSON.

### UDP (macOS `nc` notu aşağıda)
```bash
(echo -n 'PING'; sleep 1) | nc -u -w2 -v 127.0.0.1 9999
```
Beklenen: tek satır `PONG ...Z`.

### Python ile UDP test (platformdan bağımsız önerilir)
```bash
python3 - <<'PY'
import socket
s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(2)
s.sendto(b'PING', ('127.0.0.1', 9999))
print(s.recvfrom(4096)[0].decode()); s.close()
PY
```

## Sorun Giderme
- `nc` (BSD/macOS) `-q` bayrağını desteklemez. Üstteki komutlarda `sleep` ile stdin’i kısa süre açık tutuyoruz.
- Yanıt alamazsanız:
  - Sunucu log’larını kontrol edin (başlatılmış mı?)
  - Firewall/Network ayarlarını kontrol edin
  - IPv4 adresini açık yazın: `127.0.0.1`

## Güvenlik Notu
Bu proje eğitim içindir. Üretim için ek güvenlik/sertleştirme, hata yönetimi, kaynak sınırları ve testler gereklidir.
