<div align="center">

# 🧠 OperationalBrain

### AI-Powered Industrial Knowledge Platform

Transform industrial documents into searchable operational intelligence using AI, semantic search, and vector databases.

![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-green)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-red)

</div>

---

## 📖 Overview

OperationalBrain is an AI-powered platform that helps organizations search and understand industrial documents such as SOPs, manuals, inspection reports, and maintenance guides.

Instead of keyword search, it uses semantic search and AI to retrieve relevant information and answer questions from uploaded documents.

---

## ✨ Features

- 📄 Multi-format document upload (PDF, DOCX, PPTX, XLSX, TXT)
- 🔍 Semantic document search
- 🤖 AI Copilot for document Q&A
- 📑 Automatic metadata extraction
- ✂️ Intelligent text chunking
- ⚡ Vector search using Qdrant
- 🕸 Knowledge Graph visualization
- 🏢 Workspace-based document management

---

## 🛠 Tech Stack

**Frontend**
- Next.js
- React
- TypeScript
- Tailwind CSS

**Backend**
- FastAPI
- MongoDB
- Qdrant
- PyMuPDF
- Tesseract OCR
- SentenceTransformers / OpenAI (optional)

---

## 🏗 Architecture

```
Documents
     │
     ▼
Extraction → Metadata → Chunking → Embeddings
     │
     ▼
 Qdrant Vector DB
     │
     ▼
Industrial Search & AI Copilot
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/OperationalBrain.git
cd OperationalBrain
```

### 2. Start the Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

Swagger UI:

```
http://localhost:8000/docs
```

---

### 3. Start the Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at:

```
http://localhost:3000
```


## 🚧 Important Features

- GraphRAG Integration
- P&ID Drawing Intelligence
- Computer Vision for Engineering Drawings
- Neo4j Knowledge Graph
- Industrial AI Agents

---

## 👩‍💻 Author

**Mahi Goel**

