"""
FinSight AI — Benchmark Script
Measures two key metrics:
  1. Upload API response time (proves async Celery offloading benefit)
  2. List documents API latency (proves non-blocking async backend)

Usage:
  python benchmark.py --email your@email.com --password yourpassword
"""

import requests
import time
import argparse
import io
import statistics

BASE_URL = "http://127.0.0.1:8000"


def login(email: str, password: str) -> str:
    """Login and return the JWT access token."""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    token = resp.json().get("access_token")
    print(f"✅ Logged in as {email}\n")
    return token


def benchmark_upload(token: str, runs: int = 5):
    """
    Benchmark: POST /api/v1/documents/upload
    Key insight: The endpoint saves the file to disk, creates a DB record,
    enqueues a Celery task, and returns immediately.
    This measures how fast the API responds, NOT how long processing takes.
    """
    headers = {"Authorization": f"Bearer {token}"}
    timings = []

    # Create a fake small PDF-like text file for testing
    fake_file_content = b"%PDF-1.4 This is a benchmark test document. " * 500  # ~22KB

    print(f"📤 Benchmarking document upload endpoint ({runs} runs)...")
    print(f"   File size: {len(fake_file_content) / 1024:.1f} KB\n")

    for i in range(runs):
        fake_file = io.BytesIO(fake_file_content)
        files = {"file": (f"benchmark_test_{i}.txt", fake_file, "text/plain")}

        start = time.perf_counter()
        resp = requests.post(f"{BASE_URL}/api/v1/documents/upload", headers=headers, files=files)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if resp.status_code in (200, 201):
            timings.append(elapsed_ms)
            status = resp.json().get("processing_status", "unknown")
            print(f"   Run {i+1}: {elapsed_ms:.1f}ms  →  Status returned: '{status}'")
        else:
            print(f"   Run {i+1}: FAILED ({resp.status_code}) — {resp.text[:100]}")

    if timings:
        print(f"\n📊 Upload API Results:")
        print(f"   Min:    {min(timings):.1f}ms")
        print(f"   Max:    {max(timings):.1f}ms")
        print(f"   Avg:    {statistics.mean(timings):.1f}ms")
        print(f"   Median: {statistics.median(timings):.1f}ms")
        print(f"\n   ✅ The API returned in ~{statistics.median(timings):.0f}ms while Celery")
        print(f"      processes the document asynchronously in the background.")


def benchmark_list_documents(token: str, runs: int = 10):
    """
    Benchmark: GET /api/v1/documents
    Measures async DB query response time.
    """
    headers = {"Authorization": f"Bearer {token}"}
    timings = []

    print(f"\n📋 Benchmarking list documents endpoint ({runs} runs)...")

    for i in range(runs):
        start = time.perf_counter()
        resp = requests.get(f"{BASE_URL}/api/v1/documents", headers=headers)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if resp.status_code == 200:
            count = len(resp.json())
            timings.append(elapsed_ms)
            print(f"   Run {i+1}: {elapsed_ms:.1f}ms  →  {count} document(s) returned")
        else:
            print(f"   Run {i+1}: FAILED ({resp.status_code})")

    if timings:
        print(f"\n📊 List Documents API Results:")
        print(f"   Min:    {min(timings):.1f}ms")
        print(f"   Max:    {max(timings):.1f}ms")
        print(f"   Avg:    {statistics.mean(timings):.1f}ms")
        print(f"   Median: {statistics.median(timings):.1f}ms")


def main():
    parser = argparse.ArgumentParser(description="FinSight AI Benchmark Script")
    parser.add_argument("--email", required=True, help="Your FinSight AI account email")
    parser.add_argument("--password", required=True, help="Your FinSight AI account password")
    parser.add_argument("--runs", type=int, default=5, help="Number of benchmark runs (default: 5)")
    args = parser.parse_args()

    print("=" * 55)
    print("  FinSight AI — Performance Benchmark")
    print("=" * 55 + "\n")

    token = login(args.email, args.password)
    benchmark_upload(token, runs=args.runs)
    benchmark_list_documents(token, runs=args.runs)

    print("\n" + "=" * 55)
    print("  Benchmark complete! Use the median values above")
    print("  as your honest, defensible resume metrics.")
    print("=" * 55)


if __name__ == "__main__":
    main()
