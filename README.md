# Supply Chain Disruption Predictor

<div align="center">

![ChainGuard AI](./frontend/public/chain.svg)

### 🔮 AI-Powered Supply Chain Risk Intelligence Platform

**Predict disruptions before they happen. Protect your supply chain.**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

---

## 🌟 Features

- **🤖 AI-Powered Predictions** - LSTM & Prophet models analyze patterns to predict disruptions
- **📰 Real-Time News Analysis** - NLP sentiment analysis of supply chain news
- **🗺️ Global Risk Mapping** - Interactive visualization of regional risks
- **🚨 Smart Alerts** - Proactive notifications before disruptions occur
- **📊 Executive Dashboard** - Premium, dark-themed analytics dashboard
- **📈 Trend Analysis** - Historical and forecasted risk metrics

## 🏗️ Architecture

```
supply-chain-predictor/
├── backend/                    # FastAPI Python Backend
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── core/              # Configuration
│   │   ├── ml/                # Machine learning models
│   │   ├── nlp/               # NLP pipeline
│   │   ├── models/            # Data schemas
│   │   └── services/          # Business logic
│   ├── main.py                # Application entry
│   └── requirements.txt
├── frontend/                   # React Vite Frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API services
│   │   └── utils/             # Utilities
│   └── package.json
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run the server
python main.py
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/summary` | GET | Executive dashboard summary |
| `/api/dashboard/regions` | GET | Regional risk data |
| `/api/dashboard/alerts` | GET | Active alerts |
| `/api/dashboard/predictions` | GET | AI predictions |
| `/api/predictions/forecast` | GET | Risk forecast |
| `/api/predictions/analyze-text` | POST | NLP text analysis |
| `/api/predictions/risk-assessment` | GET | Comprehensive risk assessment |

## 🎨 UI Features

- **Dark Theme** - Premium dark color scheme with glassmorphism
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-Time Updates** - Auto-refresh every 30 seconds
- **Interactive Charts** - Recharts-powered visualizations
- **Animated Map** - SVG world map with risk indicators

## 🔑 Configuration

Create a `.env` file in the backend directory:

```env
# API Keys (optional - uses mock data if not provided)
NEWS_API_KEY=your_key_here
TWITTER_API_KEY=your_key_here

# Risk Thresholds
RISK_THRESHOLD_HIGH=0.7
RISK_THRESHOLD_MEDIUM=0.4
```

## 📊 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Recharts |
| Styling | Vanilla CSS with CSS Variables |
| Backend | FastAPI, Python 3.10+ |
| ML/AI | Scikit-learn, NLP Pipeline |
| API | RESTful with auto-generated docs |

## 🎯 Use Cases

1. **Manufacturing** - Predict production disruptions
2. **Logistics** - Anticipate shipping delays
3. **Procurement** - Assess supplier risks
4. **Finance** - Forecast cost impacts
5. **Operations** - Plan contingencies

## 📜 License

MIT License - See LICENSE file for details.

---

<div align="center">

**Built with ❤️ for Supply Chain Resilience**

</div>
