\# 🫀 PulseAgent — Voice-Native Clinical Triage Agent



> \*\*HackBLR 2026 | Vision\_Architect | PS-3: Voice AI for Accessibility \& Societal Impact\*\*



Medical professionals waste 40% of their time on data entry. In emergencies, that time costs lives.  

\*\*PulseAgent eliminates it with voice.\*\*



\## 🎥 Demo Video

\[!\[Demo](https://img.shields.io/badge/Demo-Watch%20Now-red)](YOUR\_DEMO\_LINK)



\## 🏗️ Architecture

User speaks

↓

Vapi STT + Function Calling

↓

FastAPI Webhook (Python)

↓

Qdrant Vector Search ←→ Clinical Protocols + Patient History

↓

GPT-4o-mini Response

↓

Streamlit Dashboard (real-time polling)



\## ✅ How We Used Vapi

\- \*\*STT/TTS\*\* — Deepgram Nova-2 transcription, ElevenLabs voice

\- \*\*Function Calling\*\* — 4 custom tools that fire real backend actions

\- \*\*Webhook Integration\*\* — Every tool call hits our FastAPI endpoint

\- Tools: `log\_patient\_info`, `log\_vitals`, `query\_protocols`, `recall\_patient\_history`



\## ✅ How We Used Qdrant

\- \*\*Collection 1: `clinical\_protocols`\*\* — 8 medical emergency protocols embedded with multilingual sentence-transformers. Semantic RAG retrieval on symptom queries.

\- \*\*Collection 2: `patient\_history`\*\* — Episodic patient memory. Semantic recall across sessions.

\- \*\*Collection 3: `user\_memory`\*\* — Future: persistent user profiles

\- Model: `paraphrase-multilingual-MiniLM-L12-v2` (384-dim cosine similarity)



\## 🚨 What It Does

1\. Health worker \*\*speaks\*\* patient info → agent calls `log\_patient\_info` → dashboard populates

2\. Health worker \*\*speaks\*\* vitals → agent calls `log\_vitals` → critical alerts fire automatically

3\. Health worker says \*\*"check protocols"\*\* → Qdrant semantic search → matched protocol displayed

4\. Health worker says \*\*"recall history"\*\* → Qdrant memory → past patient data retrieved



\## 🛠️ Tech Stack

| Component | Technology |

|-----------|-----------|

| Voice AI | Vapi (Deepgram STT + ElevenLabs TTS) |

| Vector DB | Qdrant Cloud |

| LLM | GPT-4o-mini via OpenAI |

| Backend | FastAPI + Python |

| Embeddings | sentence-transformers |

| Dashboard | Streamlit |



\## 🚀 Quick Start

```bash

git clone https://github.com/Varvyju/pulseagent

cd pulseagent

pip install -r requirements.txt



\# Add your keys to .env

cp .env.example .env



\# Seed Qdrant

python seed\_qdrant.py



\# Start backend

uvicorn main:app --reload --port 8000



\# Start dashboard

streamlit run dashboard.py

```



\## 📁 Repo Structure

pulseagent/

├── main.py              # FastAPI backend + all tool handlers

├── dashboard.py         # Streamlit real-time dashboard

├── seed\_qdrant.py       # Seeds clinical protocols + patient history

├── requirements.txt

└── .env.example



\## 👤 Team

\*\*Vision\_Architect\*\* | Varun S Namavali |Vyshak T M| HackBLR 2026

