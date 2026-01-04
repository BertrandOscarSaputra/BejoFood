---
description: How to start the BejoFood development servers
---

# Starting BejoFood

Run these commands in separate terminals from the project root (`c:\Users\Lenovo\Desktop\BejoFood`):

## 0. Prerequisites
Ensure your `.env` file has the following (especially for security):
```env
DEBUG=True
TELEGRAM_SECRET_TOKEN=your-generated-secret-token
```

## 1. Start Django Backend (Terminal 1)
Using `runserver` for development (supports static files & debug):
```powershell
cd backend
..\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

## 2. Start Frontend Dashboard (Terminal 2)
```powershell
cd frontend
npm run dev
```

## 3. Start Ngrok Tunnel (Terminal 3)
```powershell
& "C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" http 8000
```

## 4. Set Telegram Webhook (on ngrok URL change)
Get the ngrok URL from http://127.0.0.1:4040 then run:
```powershell
cd backend
..\venv\Scripts\python.exe manage.py setup_webhook https://YOUR-NGROK-URL.ngrok-free.dev/webhook/telegram/
```

## Access Points
- **Dashboard**: http://localhost:5173
- **Django Admin**: http://localhost:8000/admin/ (Login: admin/admin123)
- **Ngrok Inspector**: http://127.0.0.1:4040

## Quick Test
1. Send `/start` to your Telegram bot
2. Send `/menu` to see the **Indonesian menu**
3. Create an order and watch it appear on the dashboard!
