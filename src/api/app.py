# src/api/app.py
import os
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from src.agents.runner import run_agent
from src.etl.pipeline import ETLPipeline
from src.utils.logging import logger
import uvicorn

app = FastAPI(title="Bharat Financial Intelligence Agent", version="1.0")

# ---------- Metrics ----------
query_counter = Counter("bfia_queries_total", "Total number of queries")
query_latency = Histogram("bfia_query_latency_seconds", "Query latency")
hallucination_gauge = Gauge("bfia_hallucination_score", "Hallucination score per query")
error_counter = Counter("bfia_errors_total", "Total errors")
ingestion_counter = Counter("bfia_ingestions_total", "Total documents ingested")
ingestion_latency = Histogram("bfia_ingestion_latency_seconds", "Ingestion latency")

# ---------- Endpoints ----------
class QueryRequest(BaseModel):
    query: str

class Citation(BaseModel):
    doc_id: str
    title: str
    page: int
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    hallucination_score: Optional[float] = None
    calculations: Optional[Dict] = None

@app.post("/query", response_model=QueryResponse)
async def handle_query(req: QueryRequest):
    # Increment counter
    query_counter.inc()
    # Measure latency
    start = time.time()
    try:
        result = run_agent(req.query)
        # Set hallucination gauge (latest value)
        hallucination_gauge.set(result.get("hallucination_score", 0.0))
        citations = [
            Citation(
                doc_id=c.get("id", ""),
                title=c.get("title", "Unknown"),
                page=c.get("page", 0),
                snippet=c.get("snippet", "")
            )
            for c in result.get("citations", [])
        ]
        response = QueryResponse(
            answer=result["answer"],
            citations=citations,
            hallucination_score=result.get("hallucination_score"),
            calculations=result.get("calculations")
        )
        # Observe latency
        query_latency.observe(time.time() - start)
        return response
    except Exception as e:
        error_counter.inc()
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(None),
    url: str = Form(None)
):
    ingestion_counter.inc()
    start = time.time()
    if file and url:
        raise HTTPException(400, "Provide either file or URL, not both.")
    if not file and not url:
        raise HTTPException(400, "Either file or URL required.")
    pipeline = ETLPipeline()
    try:
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            doc_id = pipeline.process_pdf(tmp_path, is_url=False)
            os.unlink(tmp_path)
        else:
            doc_id = pipeline.process_pdf(url, is_url=True)
        ingestion_latency.observe(time.time() - start)
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        error_counter.inc()
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(500, detail=str(e))

# ---------- Metrics endpoint for Prometheus ----------
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)