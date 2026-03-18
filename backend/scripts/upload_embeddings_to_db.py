#!/usr/bin/env python3
"""Upload CSV rows to backend indexing endpoint in batches.

Usage:
  python backend/scripts/upload_embeddings_to_db.py --csv data/netflix_with_embeddings.csv --url http://localhost:8000/api/v1/rag/index --batch 200
"""
import argparse
import ast
import time
from pathlib import Path

import pandas as pd
import httpx


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--url", default="http://localhost:8000/api/v1/rag/index")
    p.add_argument("--batch", type=int, default=200)
    p.add_argument("--start", type=int, default=0, help="Row index to start from")
    p.add_argument("--max-retries", type=int, default=5)
    return p.parse_args()


def parse_embedding(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
        if isinstance(parsed, list) and parsed:
            return [float(x) for x in parsed]
    return None


def make_item(row):
    # Use `title` column for title and `content` for description if present.
    title = row.get("title") or ""
    # Try to extract a shorter description from content if possible
    content = row.get("content") or ""
    # If the CSV has a dedicated "description" column, prefer it
    description = row.get("description") or content
    if not title or not str(description).strip():
        return None
    genre = row.get("genre") if "genre" in row else None
    payload = {"title": title, "description": description, "genre": genre}
    embedding = parse_embedding(row.get("embedding")) if "embedding" in row else None
    if embedding:
        payload["embedding"] = embedding
    return payload


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print("CSV not found:", csv_path)
        raise SystemExit(1)

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")

    url = args.url
    batch = args.batch

    with httpx.Client(timeout=120.0) as client:
        for i in range(args.start, len(df), batch):
            chunk = df.iloc[i : i + batch]
            items = [make_item(row) for _, row in chunk.iterrows()]
            items = [item for item in items if item is not None]
            if not items:
                print(f"Skipping batch {i}..{i+len(chunk)-1}: no valid rows")
                continue
            payload = {"items": items}
            print(f"Posting batch {i}..{i+len(items)-1} -> {len(items)} items")

            backoff = 1.0
            for attempt in range(1, args.max_retries + 1):
                try:
                    r = client.post(url, json=payload)
                    if r.status_code == 200:
                        print("OK", r.text)
                        break
                    if attempt == args.max_retries:
                        print("Failed batch", i, r.status_code, r.text)
                        raise SystemExit(1)
                    print(f"Retrying batch {i}: status={r.status_code}, attempt={attempt}")
                except httpx.HTTPError as exc:
                    if attempt == args.max_retries:
                        print(f"Failed batch {i} due to network error: {exc}")
                        raise SystemExit(1)
                    print(f"Retrying batch {i} after network error: {exc}")

                time.sleep(backoff)
                backoff *= 2

            time.sleep(0.1)

    print("All done")


if __name__ == "__main__":
    main()
