# 📈 Stocks Researcher – AI Equity Research Assistant

**Stocks Researcher transforms raw regulatory filings, financial data, and market news into concise, structured equity research reports using vector search and LLM-powered reasoning.**

---

## 🎥 Demo

<p align="center">
  <img src="docs/demo.gif" width="600">
</p>

⚠️ **Note:** Report generation involves document retrieval, metric aggregation, and LLM summarization.  
Actual runtime may take a couple of minutes depending on data size and API response times.

📄 Example generated report available in the `docs` folder:  
`MSFT_report (1).pdf`

---

## ❗ Problem Statement

Performing fundamental equity research is time-consuming.

Investors and analysts often need to visit multiple platforms to gather financial metrics, read regulatory filings, and track recent news before forming an opinion about a company. This manual process can take hours.

There is a need for a system that can consolidate trusted sources, retrieve the most relevant information, and present it in a concise, structured format.

---

## 💡 Solution Overview

Stocks Researcher automates the equity research workflow by combining authoritative data sources with Retrieval-Augmented Generation (RAG).

The system fetches regulatory filings through the SEC API, processes and chunks the documents, and stores their embeddings inside a FAISS vector database for efficient semantic retrieval.

When a user requests a company report, the application retrieves the most relevant filing excerpts from FAISS and provides them as context to an LLM, enabling grounded and accurate summarization.

To complement qualitative insights, the system integrates financial indicators such as revenue CAGR, operating margin, and leverage metrics via the Financial Modeling Prep (FMP) API. Recent company developments are added through a market news API.

The result is a unified, structured equity research report generated in minutes instead of hours.

---

## ✨ Key Features

- 📄 **Automated filing ingestion** from the SEC API
- 🧠 **Retrieval-Augmented Generation (RAG)** for grounded outputs
- 🔎 **Semantic search with FAISS** for high-relevance context selection
- 📊 **Financial KPI integration** (revenue growth, margins, leverage, etc.) via FMP
- 📰 **Recent news aggregation** for up-to-date developments
- 🧩 **Structured, analyst-style reports** instead of raw text dumps
- ⚡ **On-demand generation** through API-driven architecture
- 🧱 **Modular pipeline** enabling easy extension with new data sources
- 📑 **Export-ready outputs** suitable for investor review

---

## ⚙️ How It Works

1. **Fetch Data**  
   The system pulls company filings from the SEC API, financial metrics from the FMP API, and recent developments from a news provider.

2. **Process & Index**  
   Filings are cleaned, chunked, converted into embeddings, and stored in a FAISS vector database.

3. **User Request**  
   A ticker symbol is submitted through the UI.

4. **Retrieve Context**  
   The most relevant document segments are selected using semantic similarity search.

5. **Generate Report**  
   Retrieved context, metrics, and news are passed to the LLM to create a structured equity research summary.

6. **Deliver Output**  
   The final report is displayed in the UI and can be exported for further analysis.

---

## 🛠 Tech Stack

### Backend
- Python
- FastAPI
- FAISS
- Uvicorn

### AI / ML
- OpenAI LLMs
- Embeddings for semantic retrieval
- Retrieval-Augmented Generation (RAG)

### Data Sources
- SEC Filings API
- Financial Modeling Prep (FMP) API
- Market News API

### Frontend
- Lovable (AI-generated UI)
- React / TypeScript (exported project)

---

## 📂 Repository Structure

```
backend/        FastAPI application, RAG pipeline, data ingestion, report generation  
frontend/       Lovable-generated UI exported as a React/TypeScript project  
docs/           Demo media and example generated reports  
requirements.txt
README.md
```

---

## 🚀 Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/Indrajit30/Stocks-Researcher.git
cd Stocks-Researcher
```

---

### 2. Backend setup
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```
Before starting the backend, create a .env file in the root directory of the project.

Add the following inside the .env file:

```
FMP_API_KEY=your_fmp_api_key
SEC_USER_AGENT=StockIntel (XYZ@gmail.com)
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_news_api_key
```

---

### 3. Start the backend server
```bash
python -m uvicorn backend.main:app --port 8000
```

Backend will be available at:
```
http://127.0.0.1:8000
```

---

### 4. Expose the backend (required for the frontend)
```bash
ngrok http 8000
```

💡 The frontend expects a publicly accessible API endpoint.  
Ngrok creates a secure tunnel to your local machine and provides a temporary public URL.

---

### 5. Frontend setup
```bash
cd frontend
npm install
npm run dev
```

---

Open the URL shown in the terminal to access the UI.

---

## 🔮 Future Scope

- 📰 **Improve news accuracy**  
  The current system uses the free tier of a news API, which relies on keyword matching and may not always return perfectly company-specific results. This can be improved by integrating premium providers or building dedicated scraping pipelines.

- 📊 **Expand financial depth**  
  The metrics in the report are based on what I considered useful for quick analysis. With input from finance professionals, the framework could be extended to include more rigorous and industry-standard evaluation measures.

---

## 👤 Author

**Indrajit Dalvi**  
MS Data Science – Rutgers University
