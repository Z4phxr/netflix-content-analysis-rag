import argparse
import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import faiss

# Make `app` importable when running this file directly: python scripts/build_embeddings.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.embeddings import batch_generate_embeddings  # noqa: E402


def _parse_embedding(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
        return parsed if isinstance(parsed, list) else None
    return None


def build(args):
    input_path = Path(args.input)
    out_csv = Path(args.out_csv)
    faiss_out = Path(args.faiss_out)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    print("Loading input CSV...")
    df = pd.read_csv(input_path)

    if "content" not in df.columns:
        print("Required column 'content' not found in CSV")
        sys.exit(1)

    df["content"] = df["content"].fillna("").astype(str).str.strip()
    if (df["content"] == "").any():
        empty_count = int((df["content"] == "").sum())
        print(f"Found {empty_count} empty content rows; dropping them before embedding.")
        df = df[df["content"] != ""].copy()

    embeddings = None
    if args.reuse_existing_embeddings and "embedding" in df.columns:
        parsed = df["embedding"].apply(_parse_embedding)
        if parsed.notna().all():
            embeddings = parsed.tolist()
            print(f"Reusing {len(embeddings)} precomputed embeddings from CSV...")

    if embeddings is None:
        texts = df["content"].tolist()
        print(f"Generating embeddings for {len(texts)} rows (batch {args.batch})...")
        embeddings = batch_generate_embeddings(texts, batch_size=args.batch)

    print("Attaching embeddings to dataframe and saving CSV...")
    df["embedding"] = embeddings
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8")

    print("Building FAISS index...")
    vectors = np.array(embeddings).astype("float32")
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    faiss_out.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(faiss_out))

    print(f"Done. CSV saved to {out_csv}, FAISS index saved to {faiss_out}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out-csv", required=True)
    p.add_argument("--faiss-out", required=True)
    p.add_argument("--batch", type=int, default=100)
    p.add_argument(
        "--reuse-existing-embeddings",
        action="store_true",
        help="Reuse existing embedding column if valid vectors are already present",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(args)
