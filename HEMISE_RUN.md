# 🚀 BOT-U HƏMIŞƏ RUN ETMƏK

Bot-u server-də həmişə işlək saxlamaq üçün.

---

## 📋 ADDIM-ADDIM QURAŞDIRMA

### 1️⃣ GitHub-dan çək
```bash
ssh root@YOUR_SERVER_IP
cd /root/Indicome
git pull origin master
```

### 2️⃣ Service quraşdır
```bash
# Service faylını kopyala
sudo cp indicome-bot.service /etc/systemd/system/

# Systemd yenilə
sudo systemctl daemon-reload

# Enable et (server restart olsa avtomatik başlasın)
sudo systemctl enable indicome-bot

# Başlat
sudo systemctl start indicome-bot

# Status yoxla
sudo systemctl status indicome-bot
```

**Görməlisən:**
```
● indicome-bot.service - Indicome Telegram Bot - Always Running
   Active: active (running) ✅
```

✅ **Yaşıl "active (running)" = İşləyir!**

---

## 🎮 İDARƏ ƏMRLƏRI

### Status yoxla
```bash
sudo systemctl status indicome-bot
```

### Restart et
```bash
sudo systemctl restart indicome-bot
```

### Dayandır
```bash
sudo systemctl stop indicome-bot
```

### Başlat
```bash
sudo systemctl start indicome-bot
```

### Log-lara bax
```bash
# Real-time
journalctl -u indicome-bot -f

# Son 50 sətir
journalctl -u indicome-bot -n 50

# Son 1 saat
journalctl -u indicome-bot --since "1 hour ago"
```

---

## ✅ NƏ OLDU?

- ✅ **Bot həmişə işləyir**
- ✅ **Crash olsa avtomatik restart olur**
- ✅ **Server restart olsa avtomatik başlayır**
- ✅ **Log-lar systemd-də saxlanır**

---

## 🔄 YENİLƏMƏ (Yeni kod push edəndə)

```bash
cd /root/Indicome
git pull origin master
sudo systemctl restart indicome-bot
sudo systemctl status indicome-bot
```

---

## 🎯 BİR ƏMRLƏ QURAŞDIR

Bütün addımları bir əmrlə:

```bash
cd /root/Indicome && \
git pull origin master && \
sudo cp indicome-bot.service /etc/systemd/system/ && \
sudo systemctl daemon-reload && \
sudo systemctl enable indicome-bot && \
sudo systemctl restart indicome-bot && \
sudo systemctl status indicome-bot
```

---

## ⚠️ PROBLEM OLARSA

### Bot başlamır?
```bash
# Log-lara bax
journalctl -u indicome-bot -n 100 --no-pager

# Virtual env yoxla
ls -la /root/Indicome/venv/bin/python3

# Config yoxla
cat /root/Indicome/config.py | grep BOT_TOKEN
```

### Import error?
```bash
cd /root/Indicome
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🎊 UĞURLAR!

Bot indi həmişə işləyir! 

**Yoxla:**
```bash
sudo systemctl status indicome-bot
```

Telegram-da **/start** yaz və test et! 🚀

