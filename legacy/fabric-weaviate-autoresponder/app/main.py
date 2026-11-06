"""FastAPI application — Loopio RFI Auto-Responder."""

from __future__ import annotations

import io
import os
import time
from datetime import datetime, timezone

import openpyxl
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config import INDEX_NAME
from .ingest import export_from_loopio, ingest_csv
from .models import AnswerResponse, HealthResponse, IngestResponse, QuestionRequest, SourceEntry
from .pipeline import answer_question

app = FastAPI(
    title="Loopio RFI Auto-Responder",
    description="RAG-powered RFI/RFP answer generation using PulsePoint's Loopio library.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check — verifies Pinecone connectivity."""
    try:
        from pinecone import Pinecone
        from .config import PINECONE_API_KEY

        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        return HealthResponse(
            status="ok",
            index=INDEX_NAME,
            vector_count=stats.total_vector_count,
        )
    except Exception as e:
        return HealthResponse(status=f"error: {e}", index=INDEX_NAME)


@app.post("/answer", response_model=AnswerResponse)
def answer(req: QuestionRequest):
    """Answer a single RFI question using the RAG pipeline."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    answer_text, reranked, model = answer_question(req.question.strip())

    sources = [
        SourceEntry(
            entry=i + 1,
            rerank_score=m.rerank_score,
            vector_score=m.vector_score,
            question=m.question,
            stack_name=m.stack_name,
            last_updated=m.last_updated,
        )
        for i, m in enumerate(reranked)
    ]

    return AnswerResponse(
        question=req.question,
        answer=answer_text,
        sources=sources,
        model=model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/batch")
async def batch(file: UploadFile = File(...), skip_sheets: str = ""):
    """Process an XLSX file: answer every question and return the filled workbook."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="File must be .xlsx")

    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))

    skip = {s.strip() for s in skip_sheets.split(",") if s.strip()}
    skip.update(["TERMS OF RFI - PLEASE READ", "Instructions For Completion"])

    Q_NUM_COL = 2
    QUESTION_COL = 3
    RESPONSE_COL = 4

    processed = 0
    for sheet_name in wb.sheetnames:
        if sheet_name in skip:
            continue
        ws = wb[sheet_name]
        for row_idx in range(1, ws.max_row + 1):
            q_num = ws.cell(row=row_idx, column=Q_NUM_COL).value
            q_text = ws.cell(row=row_idx, column=QUESTION_COL).value
            if not q_num or not q_text:
                continue
            q_num_str = str(q_num).strip()
            q_text_str = str(q_text).strip()
            if q_text_str.lower() == "question":
                continue

            answer_text, _, _ = answer_question(q_text_str)
            ws.cell(row=row_idx, column=RESPONSE_COL).value = answer_text
            processed += 1

            # Rate limiting for Pinecone rerank
            time.sleep(2.0)

    # Write to buffer and return
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"RFI_Answered_{timestamp}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """Ingest a Loopio library CSV export into Pinecone."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be .csv")

    content = (await file.read()).decode("utf-8")
    count = ingest_csv(content)
    return IngestResponse(status="complete", vectors_upserted=count)


@app.post("/ingest/loopio", response_model=IngestResponse)
def ingest_from_loopio():
    """Pull fresh data from Loopio API and ingest into Pinecone."""
    try:
        csv_content = export_from_loopio()
        count = ingest_csv(csv_content)
        return IngestResponse(status="complete", vectors_upserted=count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
