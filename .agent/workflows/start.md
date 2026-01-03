---
description: How to start the BejoFood development servers
---

# Starting BejoFood

Run these commands in separate terminals from the project root (`c:\Users\Lenovo\Desktop\BejoFood`):

## 1. Start Django Backend (Terminal 1)
```powershell
cd backend
..\venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 backend.asgi:application
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

## 4. Set Telegram Webhook (one-time after ngrok starts)
Get the ngrok URL from http://127.0.0.1:4040 then run:
```powershell
cd backend
..\venv\Scripts\python.exe manage.py setup_webhook https://YOUR-NGROK-URL.ngrok-free.dev/webhook/telegram/
```

## Access Points
- **Dashboard**: http://localhost:5173
- **Django Admin**: http://localhost:8000/admin/
- **Ngrok Inspector**: http://127.0.0.1:4040
- **Telegram Bot**: Open Telegram and message your bot

## Quick Test
1. Send `/start` to your Telegram bot
2. Send `/menu` to see the food menu
3. Add items and checkout
4. Watch orders appear in the dashboard!
