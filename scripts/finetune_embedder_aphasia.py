"""Contrastive fine-tune of MiniLM on AphasiaBank PAR utterances.

Hypothesis: an embedder trained on neurotypical text places aphasic
semantic anomalies in regions it doesn't model well, hence the Wernicke
F1 = 0.20 ceiling. Fine-tuning the embedder so that within-patient
utterances cluster together (and across-patient stay apart) should give
us a representation that respects the structure of aphasic speech.

Method:
  - Sample pairs (anchor, positive) from same-patient utterances
  - Sample (anchor, negative) from different-patient utterances of the
    same subtype (so we learn within-subtype distinctions, not just
    'same vs different patient')
  - Train MultipleNegativesRankingLoss for 1 epoch
  - Re-embed all AphasiaBank windows
  - Compare Wernicke F1 to baseline

Uses all-MiniLM-L6-v2 (384-d, fast on MPS).
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd
import pylangacq as pla
from sentence_transformers import (InputExample, SentenceTransformer,
                                    losses)
from sentence_transformers.datasets import NoDuplicatesDataLoader
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--idx-path",
                   default="data/features/aphasiabank_transcripts.parquet",
                   type=Path)
    p.add_argument("--output-dir",
                   default="data/features/finetuned_embedder",
                   type=Path)
    p.add_argument("--base-model",
                   default="sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--max-pairs", type=int, default=20000)
    return p.parse_args()


def utt_text(u) -> str:
    out = []
    for t in u.tokens:
        word = (t.word or "").strip()
        if not word or word in {".", "?", "!", ",", ";", ":"}:
            continue
        out.append(word)
    return " ".join(out)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    idx = pd.read_parquet(args.idx_path)
    path_lookup = idx.drop_duplicates("transcript_id").set_index(
        "transcript_id")["file_path"].to_dict()

    # Collect (participant_id, utterance_text) — only PAR with non-empty text.
    print("collecting utterances ...")
    by_pat: dict[str, list[str]] = {}
    sessions = feats.drop_duplicates("transcript_id")[
        ["transcript_id", "participant_id", "subtype"]]
    for _, row in tqdm(sessions.iterrows(), total=len(sessions)):
        path = path_lookup.get(row["transcript_id"])
        if path is None or not Path(path).exists():
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                chat = pla.read_chat(str(path), strict=False)
        except Exception:
            continue
        for u in chat.utterances():
            if u.participant != "PAR":
                continue
            txt = utt_text(u)
            if len(txt.split()) < 3:
                continue
            by_pat.setdefault(row["participant_id"], []).append(txt)

    eligible_pats = [p for p, ts in by_pat.items() if len(ts) >= 4]
    print(f"\n{len(eligible_pats)} patients with ≥4 utterances "
          f"(of {len(by_pat)} total)")

    # Build training pairs: for each anchor, sample a positive from the
    # same patient. The MultipleNegativesRankingLoss treats other batch
    # examples as negatives automatically.
    rng = Random(0)
    examples: list[InputExample] = []
    while len(examples) < args.max_pairs:
        pat = rng.choice(eligible_pats)
        utts = by_pat[pat]
        a, p = rng.sample(utts, 2)
        examples.append(InputExample(texts=[a, p]))
    print(f"built {len(examples)} positive pairs")

    print(f"\nloading {args.base_model} on MPS ...")
    model = SentenceTransformer(args.base_model, device="mps")
    loss = losses.MultipleNegativesRankingLoss(model)

    loader = NoDuplicatesDataLoader(examples, batch_size=args.batch_size)

    print(f"fine-tuning {args.epochs} epoch(s) ...")
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=args.epochs,
        warmup_steps=int(0.1 * len(loader)),
        output_path=str(args.output_dir / "model"),
        show_progress_bar=True,
    )

    # Save info
    print("done — fine-tuned model at:", args.output_dir / "model")


if __name__ == "__main__":
    main()
