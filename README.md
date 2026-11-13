# TruthLens – Real-Time AI News Verification System

TruthLens is a full-stack, AI-powered news verification application designed to analyze factual claims using live web evidence, Natural Language Processing (NLP), semantic similarity, and Large Language Models (LLMs).

The system retrieves relevant information from online sources, extracts and filters evidence, and uses Google's Gemini AI to generate a structured verification report. Users can submit claims, view verification results, and access their verification history through an interactive React dashboard.

## Features

- **Real-Time Evidence Retrieval:** Retrieves relevant online information using the Tavily Search API.
- **Natural Language Processing:** Uses spaCy to process and extract meaningful sentences from retrieved content.
- **Semantic Similarity:** Uses Sentence Transformers to identify evidence relevant to the submitted claim.
- **AI-Powered Verification:** Uses Google's Gemini API to analyze claims against retrieved evidence.
- **Verification Verdicts:** Generates verdicts such as SUPPORTED, REFUTED, and UNVERIFIED.
- **Evidence and Source Tracking:** Displays supporting evidence and source metadata.
- **Verification History:** Stores and retrieves previous verification records.
- **Interactive Dashboard:** Provides a React-based interface for submitting claims and viewing results.
- **System Health Monitoring:** Checks backend, database, and Gemini service status.

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Google Gemini API
- Tavily Search API
- spaCy
- Sentence Transformers
- PyTorch
- BeautifulSoup
- Requests

### Frontend
- React
- Vite
- Tailwind CSS
- Axios
- React Router DOM
- Lucide React
- Recharts

### Testing and Development
- Pytest
- HTTPX
- Git and GitHub
- VS Code

## System Architecture

TruthLens follows a full-stack client-server architecture.

### Verification Workflow

1. The user submits a factual claim through the React frontend.
2. The frontend sends the claim to the FastAPI backend.
3. The backend retrieves relevant information using the Tavily Search API.
4. Retrieved content is processed and relevant sentences are extracted.
5. Sentence Transformers calculates semantic similarity to identify relevant evidence.
6. The filtered evidence is passed to Google's Gemini API.
7. Gemini analyzes the claim and generates a structured verification report.
8. The result, including verdict, confidence score, explanation, and source information, is returned to the frontend.
9. The verification result is stored in the SQLite database using SQLAlchemy.

### Architecture Overview

```text
                 USER
                   |
                   v
          REACT FRONTEND
          (Vite + Tailwind)
                   |
                   v
              AXIOS API
                   |
                   v
          FASTAPI BACKEND
                   |
          +--------+---------+
          |                  |
          v                  v
     TAVILY SEARCH       SQLITE DATABASE
          |               (SQLAlchemy)
          v
      WEB EVIDENCE
          |
          v
      NLP PROCESSING
          (spaCy)
          |
          v
   SEMANTIC SIMILARITY
   (Sentence Transformers)
          |
          v
        GEMINI AI
          |
          v
   VERIFICATION REPORT
          |
          v
     REACT DASHBOARD
```

## Project Structure

```text
realtime-news-verifier/
│
├── app/
│   ├── __init__.py
│   ├── crud.py
│   ├── database.py
│   ├── init_db.py
│   ├── main.py
│   ├── models.py
│   ├── nlp_processor.py
│   ├── rag_engine.py
│   ├── scraper.py
│   └── search.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_nlp.py
│   ├── test_rag_engine.py
│   └── test_search.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── package-lock.json
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.11
- Node.js and npm
- Git
- Google Gemini API key
- Tavily Search API key

### 1. Clone the Repository

```bash
git clone https://github.com/RitheeshReddy078/realtime-news-verifier.git
cd realtime-news-verifier
```

### 2. Set Up the Python Backend

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Backend Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./news_verifier.db
LLM_API_KEY=your_gemini_api_key
SEARCH_API_KEY=your_tavily_api_key
```

Replace the placeholder values with your actual API keys.

**Important:** Never commit your `.env` file or expose API keys on GitHub.

### 4. Run the Backend

From the project root:

```bash
uvicorn app.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### 5. Set Up the React Frontend

Open another terminal:

```powershell
cd frontend
npm install
```

Create a `.env` file inside the `frontend` directory:

```env
VITE_API_URL=http://127.0.0.1:8000
```

### 6. Run the Frontend

```bash
npm run dev
```

Frontend URL:

http://localhost:5173

Keep both backend and frontend development servers running while using the application.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend welcome and API information |
| GET | `/health` | Checks backend, database, and Gemini status |
| POST | `/verify` | Verifies a submitted factual claim |
| GET | `/history` | Retrieves stored verification history |

### Example Verification Request

Endpoint:

```http
POST /verify
```

Request Body:

```json
{
  "claim": "Chandrayaan-3 successfully landed on the Moon."
}
```

The response includes verification information such as the claim ID, verdict, confidence score, explanation, evidence, and sources.

## Testing

Run backend tests:

```bash
pytest -q
```

Check Python dependency compatibility:

```bash
python -m pip check
```

The current backend test suite contains **36 passing tests**.

## Frontend Production Build

Generate a production build:

```powershell
cd frontend
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Configures the SQLAlchemy database connection |
| `LLM_API_KEY` | Google Gemini API authentication |
| `SEARCH_API_KEY` | Tavily Search API authentication |
| `VITE_API_URL` | Frontend backend API base URL |

## Future Improvements

- Improve evidence ranking and source credibility assessment.
- Add more reliable cross-source evidence comparison.
- Optimize frontend bundle size through code splitting.
- Improve verification accuracy and explainability.
- Add additional source credibility and misinformation detection features.
- Expand automated testing and deployment.

## Author

**TruthLens – Real-Time AI News Verification System**

An AI-powered full-stack project combining NLP, semantic search, LLM-based reasoning, and modern web technologies.

GitHub Repository:

https://github.com/RitheeshReddy078/realtime-news-verifier
