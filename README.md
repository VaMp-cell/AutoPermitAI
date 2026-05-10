# AutoPermit AI

Automated municipal building permit verification using a **Dual-AI Pipeline**:
- **YOLOv8** for structural element detection on architectural blueprints
- **GPT-4o** for building code compliance analysis

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Edit with your OpenAI API key
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`

## Architecture

```
PDF Upload → PyMuPDF (PDF→Image) → YOLOv8 (Detection) → PaddleOCR (Dimensions) → GPT-4o (Compliance) → Dashboard
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a PDF blueprint |
| POST | `/analyze` | Run full analysis pipeline |
| GET | `/report/{id}` | Get a compliance report |
| GET | `/reports` | List all reports |
| GET | `/image/{id}` | Serve blueprint images |
| GET | `/health` | System health check |

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, YOLOv8, PaddleOCR, OpenAI SDK
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Lucide React
- **ML:** Ultralytics YOLOv8, PaddleOCR, GPT-4o (JSON mode)
