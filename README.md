# BejoFood - Telegram Food Ordering System

A full-stack food ordering system that allows customers to order food via Telegram Bot with QRIS payment integration and real-time admin dashboard.

![Dashboard Screenshot](https://bejo-food.vercel.app)

## Features

### Customer Features (Telegram Bot)
- Browse menu by categories
- Add items to cart
- Checkout with delivery address
- QRIS payment via Midtrans
- Order status notifications
- Order tracking with `/status` command

### Admin Features (Web Dashboard)
- Real-time order notifications (WebSocket)
- Order management with status workflow
- Payment status tracking
- Customer information
- Revenue statistics
- Menu management via Django Admin

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2, Django REST Framework |
| **Frontend** | React 18, Vite, Tailwind CSS v4 |
| **Database** | PostgreSQL (Neon) |
| **Real-time** | Django Channels, WebSocket |
| **Payment** | Midtrans QRIS API |
| **Bot** | Telegram Bot API |
| **Deployment** | Koyeb (Backend), Vercel (Frontend) |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram Bot   │────▶│  Django Backend  │◀────│  React Dashboard│
│  (Customer UI)  │     │  (Koyeb)         │     │  (Vercel)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐      ┌──────▼──────┐
              │ PostgreSQL│      │  Midtrans   │
              │  (Neon)   │      │  (Payment)  │
              └───────────┘      └─────────────┘
```

## Project Structure

```
BejoFood/
├── backend/                 # Django Backend
│   ├── backend/            # Django settings
│   ├── bot/                # Telegram bot handlers
│   │   ├── handlers/       # Command, callback, conversation handlers
│   │   └── views.py        # Webhook endpoint
│   ├── core/               # Core utilities
│   │   └── services/       # Telegram service
│   ├── dashboard/          # REST API for frontend
│   ├── menu/               # Menu models & admin
│   ├── orders/             # Order models & logic
│   ├── payments/           # Midtrans integration
│   └── realtime/           # WebSocket consumers
├── frontend/               # React Dashboard
│   ├── src/
│   │   ├── App.jsx        # Main dashboard component
│   │   └── index.css      # Tailwind styles
│   └── .env               # Environment variables
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Telegram Bot Token
- Midtrans Account (for payments)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/BejoFood.git
cd BejoFood
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. Environment Variables
Create `backend/.env`:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host/db

TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_SECRET_TOKEN=your-webhook-secret

MIDTRANS_SERVER_KEY=your-server-key
MIDTRANS_CLIENT_KEY=your-client-key
MIDTRANS_IS_PRODUCTION=False
```

### 4. Database Setup
```bash
python manage.py migrate
python manage.py seed_menu  # Seed sample menu
python manage.py createsuperuser
```

### 5. Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_ADMIN_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 6. Run Development Servers
```bash
# Terminal 1: Backend
cd backend
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Ngrok (for Telegram webhook)
ngrok http 8000
```

### 7. Setup Telegram Webhook
```bash
python manage.py setup_webhook https://your-ngrok-url.ngrok-free.dev/webhook/telegram/
```

## API Endpoints

### Dashboard API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/orders/` | List all orders |
| GET | `/api/v1/orders/{id}/` | Order details |
| PATCH | `/api/v1/orders/{id}/update_status/` | Update order status |
| GET | `/api/v1/stats/` | Dashboard statistics |
| GET | `/api/v1/menu/` | Menu items |

### Webhooks
| Endpoint | Description |
|----------|-------------|
| `/webhook/telegram/` | Telegram bot updates |
| `/webhook/payment/midtrans/` | Midtrans payment notifications |

## Order Workflow

```
1. Customer sends /menu to bot
2. Customer browses categories and adds items
3. Customer sends /checkout
4. Bot collects: address → phone → notes
5. Order created with PENDING status
6. QRIS payment generated via Midtrans
7. Customer scans QR and pays
8. Midtrans sends webhook → Order CONFIRMED
9. Admin processes: CONFIRMED → PREPARING → READY → COMPLETED
```

## Deployment

### Backend (Koyeb)
1. Push code to GitHub
2. Create Koyeb service from GitHub
3. Set environment variables
4. Deploy

### Frontend (Vercel)
1. Import GitHub repository
2. Set root directory to `frontend`
3. Add environment variables
4. Deploy

### Webhooks
Update webhook URLs after deployment:
- Telegram: `https://your-app.koyeb.app/webhook/telegram/`
- Midtrans: `https://your-app.koyeb.app/webhook/payment/midtrans/`

## Live Demo

- **Dashboard**: https://bejo-food.vercel.app
- **Telegram Bot**: [@BejoFoodBot](https://t.me/BejoFoodBot)
- **Admin**: https://chronic-lily-bejo-3b2213a3.koyeb.app/admin/

## License

MIT License

---

Built with ❤️ by Bejo
