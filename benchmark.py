"""
FinSight AI — Performance Benchmark & E2E Validation Script
Measures key production performance metrics:
  1. Upload API Latency (under async Celery offloading)
  2. End-to-End Document Ingestion & Processing Time (Celery + Vector Embeddings)
  3. List Documents API Latency (non-blocking async database query)
  4. RAG Query & LLM Generation Latency (Search + Synthesis)

Usage:
  python benchmark.py --email your@email.com --password yourpassword --url https://api.finsightai.harshithshetty.dev
  python benchmark.py --email your@email.com --password yourpassword --file path/to/100page.pdf --question "Summarize key risk factors"
"""

import argparse
import io
import os
import statistics
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def login(email: str, password: str) -> str:
    """Login and return the JWT access token."""
    url = f"{BASE_URL}/api/v1/auth/login"
    print(f"[AUTH] Authenticating as {email}...")
    try:
        resp = requests.post(url, json={"email": email, "password": password})
        resp.raise_for_status()
        token = resp.json().get("access_token")
        print("[OK] Logged in successfully.\n")
        return token
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Login failed: {e}")
        if e.response is not None:
            print(f"   Details: {e.response.text}")
        sys.exit(1)


def run_upload_benchmark(token: str, runs: int = 5) -> tuple[list[float], list[str]]:
    """
    Benchmark the raw document upload API latency.
    Uploads small dummy documents to test the raw API speed.
    Captures all uploaded document IDs so they can be cleaned up later.
    """
    headers = {"Authorization": f"Bearer {token}"}
    timings = []
    doc_ids = []

    # Small mock file (~7 KB) for checking pure API latency
    fake_content = b"FinSight AI upload benchmark dummy text content. " * 100
    print(f"[BENCHMARK] Benchmarking Upload API Latency ({runs} runs) using a dummy file...")

    for i in range(runs):
        fake_file = io.BytesIO(fake_content)
        files = {"file": (f"bench_dummy_{i}.txt", fake_file, "text/plain")}

        start = time.perf_counter()
        try:
            resp = requests.post(f"{BASE_URL}/api/v1/documents/upload", headers=headers, files=files)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if resp.status_code in (200, 201):
                timings.append(elapsed_ms)
                doc_id = resp.json().get("id")
                if doc_id:
                    doc_ids.append(doc_id)
                print(f"   Run {i+1}: {elapsed_ms:.1f}ms  ->  ID: {doc_id} ({resp.json().get('processing_status')})")
            else:
                print(f"   Run {i+1}: FAILED ({resp.status_code}) — {resp.text[:100]}")
        except Exception as e:
            print(f"   Run {i+1}: ERROR — {e}")

    print("")
    return timings, doc_ids


def run_list_benchmark(token: str, runs: int = 5) -> list[float]:
    """Benchmark raw latency of GET /api/v1/documents."""
    headers = {"Authorization": f"Bearer {token}"}
    timings = []

    print(f"[BENCHMARK] Benchmarking List Documents API Latency ({runs} runs)...")

    for i in range(runs):
        start = time.perf_counter()
        try:
            resp = requests.get(f"{BASE_URL}/api/v1/documents", headers=headers)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                timings.append(elapsed_ms)
                count = len(resp.json())
                print(f"   Run {i+1}: {elapsed_ms:.1f}ms  ->  Returned {count} documents")
            else:
                print(f"   Run {i+1}: FAILED ({resp.status_code})")
        except Exception as e:
            print(f"   Run {i+1}: ERROR — {e}")

    print("")
    return timings


def run_e2e_benchmark(token: str, file_path: str | None, question: str, poll_interval: float = 2.0) -> dict:
    """
    Runs an end-to-end flow:
      1. Uploads target file (either provided or dummy) and times the upload API response.
      2. Polls status until completed/failed to measure Celery background ingestion time.
      3. Creates a new Chat session.
      4. Submits a RAG query and measures RAG response latency.
      5. Returns performance metrics.
    """
    headers = {"Authorization": f"Bearer {token}"}
    metrics = {
        "upload_time_ms": 0.0,
        "process_duration_s": 0.0,
        "query_duration_s": 0.0,
        "status": "failed",
        "doc_id": None,
        "filename": "",
        "file_size_mb": 0.0,
        "answer": ""
    }

    if file_path:
        if not os.path.isfile(file_path):
            print(f"[ERROR] Custom file not found at: {file_path}")
            return metrics
        filename = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"[FILE] Preparing to upload custom file: {filename} ({file_size_mb:.2f} MB)")
        with open(file_path, "rb") as f:
            file_data = f.read()
    else:
        filename = "bench_e2e_dummy.txt"
        file_data = (
            b"FinSight AI End-to-End RAG Demonstration Document.\n"
            b"Company Name: TechNova Inc. Financial Year: 2025.\n"
            b"Key Strengths: Strong revenue growth driven by cloud software sales.\n"
            b"Major Risks: Supply chain disruptions, chip shortages, and model validation delays."
        )
        file_size_mb = len(file_data) / (1024 * 1024)
        print(f"[FILE] Generating standard test file for End-to-End RAG test ({len(file_data)/1024:.1f} KB)...")

    metrics["filename"] = filename
    metrics["file_size_mb"] = file_size_mb

    # 1. Upload Target File
    print("[UPLOAD] Uploading document...")
    fake_file = io.BytesIO(file_data)
    files = {"file": (filename, fake_file, "application/octet-stream")}

    start_upload = time.perf_counter()
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/documents/upload", headers=headers, files=files)
        upload_time_ms = (time.perf_counter() - start_upload) * 1000
    except Exception as e:
        print(f"[ERROR] Upload request failed: {e}")
        return metrics

    if resp.status_code not in (200, 201):
        print(f"[ERROR] Upload failed with status {resp.status_code}: {resp.text}")
        return metrics

    doc_info = resp.json()
    doc_id = doc_info.get("id")
    metrics["doc_id"] = doc_id
    metrics["upload_time_ms"] = upload_time_ms
    print(f"[OK] Upload API responded in {upload_time_ms:.1f}ms. Document ID: {doc_id}")

    # 2. Poll Processing Status
    print("[PROCESS] Waiting for backend processing to complete (Celery extraction + vector DB index)...")
    start_process = time.perf_counter()
    status = "pending"

    while True:
        try:
            status_resp = requests.get(f"{BASE_URL}/api/v1/documents/{doc_id}/status", headers=headers)
            if status_resp.status_code == 200:
                doc_status_info = status_resp.json()
                status = doc_status_info.get("processing_status")
                elapsed = time.perf_counter() - start_process
                sys.stdout.write(f"\r   [{status.upper()}] Elapsed: {elapsed:.1f}s")
                sys.stdout.flush()

                if status in ("completed", "failed"):
                    break
            else:
                print(f"\n[WARN] Status check returned HTTP {status_resp.status_code}")
        except Exception as e:
            print(f"\n[WARN] Error checking status: {e}")

        time.sleep(poll_interval)

    process_duration_s = time.perf_counter() - start_process
    print(f"\n[PROCESS] Processing finished in {process_duration_s:.2f}s with status: {status.upper()}")
    metrics["process_duration_s"] = process_duration_s
    metrics["status"] = status

    if status == "failed":
        return metrics

    # 3. Create Chat Session
    print("\n[CHAT] Creating chat session...")
    try:
        chat_resp = requests.post(f"{BASE_URL}/api/v1/chats", headers=headers, json={"mode": "HYBRID"})
        chat_resp.raise_for_status()
        chat_id = chat_resp.json().get("id")
    except Exception as e:
        print(f"[ERROR] Chat session creation failed: {e}")
        return metrics

    # 4. Submit RAG Question
    print(f"[QUERY] Submitting RAG query: \"{question}\"")
    start_query = time.perf_counter()
    try:
        query_resp = requests.post(
            f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
            headers=headers,
            json={"content": question}
        )
        query_duration_s = time.perf_counter() - start_query
        query_resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] RAG query request failed: {e}")
        # Clean up chat
        requests.delete(f"{BASE_URL}/api/v1/chats/{chat_id}", headers=headers)
        return metrics

    metrics["query_duration_s"] = query_duration_s
    answer_data = query_resp.json()

    # Find the AI message
    messages = answer_data.get("messages", [])
    assistant_reply = ""
    for m in reversed(messages):
        if m.get("role") == "assistant":
            assistant_reply = m.get("content", "")
            break

    metrics["answer"] = assistant_reply
    print(f"[OK] RAG Response Latency: {query_duration_s:.2f}s")
    print(f"\n[AI] Assistant Response Snippet:\n{'-'*50}\n{assistant_reply[:500]}...\n{'-'*50}")

    # Clean up Chat session
    try:
        requests.delete(f"{BASE_URL}/api/v1/chats/{chat_id}", headers=headers)
    except Exception:
        pass

    return metrics


def delete_documents(token: str, doc_ids: list[str]):
    """Clean up uploaded benchmark documents from backend."""
    if not doc_ids:
        return
    print(f"[CLEANUP] Cleaning up {len(doc_ids)} benchmark document(s)...")
    headers = {"Authorization": f"Bearer {token}"}
    for doc_id in doc_ids:
        try:
            resp = requests.delete(f"{BASE_URL}/api/v1/documents/{doc_id}", headers=headers)
            if resp.status_code == 204:
                print(f"   Deleted document: {doc_id}")
        except Exception as e:
            print(f"   Failed to delete {doc_id}: {e}")


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="FinSight AI Production Benchmark Tool")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of the FinSight AI API")
    parser.add_argument("--email", required=True, help="Your registered email")
    parser.add_argument("--password", required=True, help="Your password")
    parser.add_argument("--runs", type=int, default=5, help="Number of benchmark runs for pure API endpoints")
    parser.add_argument("--file", help="Path to a custom document (PDF/TXT/DOCX) to test end-to-end ingestion")
    parser.add_argument("--question", default="What are the main risks mentioned in this document?", help="Question to test RAG response")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Polling interval in seconds for processing status")
    args = parser.parse_args()

    BASE_URL = args.url.rstrip("/")

    print("=" * 60)
    print("  FinSight AI -- E2E Production Performance Benchmark")
    print("=" * 60)
    print(f"Target URL: {BASE_URL}\n")

    token = login(args.email, args.password)

    # 1. Benchmark raw upload latency (dummy files)
    upload_timings, dummy_doc_ids = run_upload_benchmark(token, runs=args.runs)

    # 2. Benchmark raw list API latency
    list_timings = run_list_benchmark(token, runs=args.runs)

    # 3. Benchmark End-to-End Processing and RAG
    e2e_metrics = run_e2e_benchmark(token, args.file, args.question, args.poll_interval)

    # Clean up uploaded files
    all_to_cleanup = dummy_doc_ids.copy()
    if e2e_metrics.get("doc_id"):
        all_to_cleanup.append(e2e_metrics["doc_id"])
    delete_documents(token, all_to_cleanup)

    # 4. Print Summary Report
    print("\n" + "=" * 60)
    print("  FinSight AI -- Performance Benchmark Summary")
    print("=" * 60)
    print(f"Target Host:             {BASE_URL}")
    print(f"Benchmark Runs:          {args.runs}")
    print("")

    if upload_timings:
        print("API Endpoint Latency (Pure HTTP roundtrip):")
        print(f"   * Document Upload API (queues to Celery task):")
        print(f"     - Median:           {statistics.median(upload_timings):.1f} ms")
        print(f"     - Average:          {statistics.mean(upload_timings):.1f} ms")
        print(f"     - Min / Max:        {min(upload_timings):.1f} ms / {max(upload_timings):.1f} ms")
        print(f"   * List Documents API (async DB query):")
        print(f"     - Median:           {statistics.median(list_timings):.1f} ms")
        print(f"     - Average:          {statistics.mean(list_timings):.1f} ms")
        print(f"     - Min / Max:        {min(list_timings):.1f} ms / {max(list_timings):.1f} ms")
        print("")

    print("End-to-End Processing & RAG Metrics:")
    print(f"   * Test File:          {e2e_metrics.get('filename')} ({e2e_metrics.get('file_size_mb'):.3f} MB)")
    print(f"   * Ingestion Status:   {e2e_metrics.get('status', 'unknown').upper()}")
    print(f"   * Ingestion Duration: {e2e_metrics.get('process_duration_s'):.2f} seconds")
    if e2e_metrics.get("query_duration_s"):
        print(f"   * RAG Query Latency:  {e2e_metrics.get('query_duration_s'):.2f} seconds")
    else:
        print("   * RAG Query Latency:  FAILED")
    print(f"   * RAG Question:       \"{args.question}\"")
    print("=" * 60)
    print("  Benchmark complete! Use these metrics as your resume points.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
