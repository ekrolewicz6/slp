"""Inter-task generalization within AphasiaBank Protocol.

The discourse protocol contains multiple elicitation tasks per session:
  - Free speech / personal narrative
  - Picture description (e.g., "Cat Rescue", "Refused Umbrella")
  - Cinderella narrative (story-tell from a wordless picture book)
  - Procedural ("how to make a peanut butter sandwich")

We've been pooling all PAR utterances per session into one window. This
asks: does the *task type* affect the features we extract? Two questions:

  1. Per-feature variance attributable to task vs to patient: if task
     dominates, then "z" reflects what they were asked to do, not who
     they are.
  2. Within-patient cross-task agreement: for patients with multiple
     tasks in the same session, how correlated is z(Cinderella) with
     z(picture description)? If high, the tool is task-agnostic.

The protocol task is encoded in the CHAT `@G:` (gem) markers, which
delineate task boundaries within a single transcript. We re-parse those
to extract per-task feature vectors.
"""

from __future__ import annotations

import argparse
import re
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
from tqdm import tqdm

from src.features.extractors import extract_features


# Common AphasiaBank protocol task identifiers in @G markers.
KNOWN_TASKS = {
    "stroke story": "Stroke",
    "important event": "ImportantEvent",
    "speech": "Speech",
    "cat rescue": "CatRescue",
    "refused umbrella": "RefusedUmbrella",
    "broken window": "BrokenWindow",
    "umbrella": "RefusedUmbrella",
    "cinderella": "Cinderella",
    "sandwich": "Sandwich",
    "procedural": "Sandwich",
}


def _normalise_task(label: str | None) -> str | None:
    if not label:
        return None
    s = label.strip().lower()
    for key, val in KNOWN_TASKS.items():
        if key in s:
            return val
    return s.replace(" ", "_").title()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/inter_task", type=Path)
    p.add_argument("--min-utts-per-task", type=int, default=20,
                   help="Per-task minimum PAR utts to extract features.")
    return p.parse_args()


def extract_per_task_features(file_path: Path,
                               min_utts: int = 20) -> list[dict]:
    """Walk @G markers in a .cha file, return one feature dict per task."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            chat = pla.read_chat(str(file_path), strict=False)
        utts = chat.utterances()
    except Exception:
        return []

    # Read the raw file to walk @G markers in order; pylangacq tucks them
    # under utterance.changeable_header.
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    # Build a map from utterance index → current task label by linearly
    # scanning lines.
    task_for_idx = []
    cur_task = None
    utt_idx = -1
    for line in lines:
        if line.startswith("@G:"):
            cur_task = _normalise_task(line[3:].strip())
        elif line.startswith("*"):
            utt_idx += 1
            task_for_idx.append(cur_task)
    # Defensive: lengths may not match utts list exactly due to comments etc.
    n = min(len(utts), len(task_for_idx))
    utts = utts[:n]
    task_for_idx = task_for_idx[:n]

    by_task: dict[str, list] = defaultdict(list)
    for u, t in zip(utts, task_for_idx):
        if u.participant != "PAR" or t is None:
            continue
        by_task[t].append(u)

    rows = []
    for task, ts in by_task.items():
        if len(ts) < min_utts:
            continue
        feats = extract_features(ts, participant="PAR",
                                 min_utterances=min_utts)
        if feats is None:
            continue
        rows.append({"task": task, "n_utts": len(ts), **feats})
    return rows


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    print(f"sessions in features parquet: {df['transcript_id'].nunique()}")

    # We need original file_paths — re-load from the transcript index.
    idx = pd.read_parquet("data/features/aphasiabank_transcripts.parquet")
    path_lookup = idx.drop_duplicates("transcript_id").set_index(
        "transcript_id")["file_path"].to_dict()

    # For each session, extract per-task features.
    print("Extracting per-task features ...")
    rows = []
    for tid in tqdm(sorted(df["transcript_id"].unique())):
        path = path_lookup.get(tid)
        if path is None or not Path(path).exists():
            continue
        meta = df[df.transcript_id == tid].iloc[0]
        per_task = extract_per_task_features(Path(path), args.min_utts_per_task)
        for tr in per_task:
            row = {
                "transcript_id": tid,
                "participant_id": meta["participant_id"],
                "subtype": meta["subtype"],
                "wab_aq": meta["wab_aq"],
                "corpus": meta["corpus"],
                **tr,
            }
            rows.append(row)
    out = pd.DataFrame(rows)
    print(f"per-task feature rows: {len(out)}")
    if not len(out):
        return

    print(f"\nTask distribution (top 15):")
    print(out["task"].value_counts().head(15).to_string())

    out.to_parquet(args.output_dir / "per_task_features.parquet", index=False)

    # ----- Variance partitioning: between-task vs between-patient -----
    META = {"transcript_id", "participant_id", "subtype", "wab_aq",
            "corpus", "task", "n_utts"}
    feat_cols = sorted(c for c in out.columns if c not in META)

    # Restrict to (patient, task) pairs that appear at least twice across
    # the dataset (i.e. a patient does the same task multiple times) —
    # too rare in AphasiaBank since most patients do each task once per
    # session. So we focus on per-feature ANOVA-style decomposition:
    # for each feature, what fraction of variance is patient vs task?
    print("\n--- variance attributable to patient vs task per feature ---")
    var_rows = []
    multi_task_pats = (out.groupby("participant_id")["task"].nunique()
                          .where(lambda s: s >= 2).dropna().index)
    sub = out[out["participant_id"].isin(multi_task_pats)].copy()
    print(f"  patients with ≥2 tasks: {len(multi_task_pats)} "
          f"(rows: {len(sub)})")

    for f in feat_cols:
        x = pd.to_numeric(sub[f], errors="coerce").to_numpy()
        if not np.isfinite(x).any():
            continue
        # patient effect
        pat_mean = sub.groupby("participant_id")[f].mean()
        pat_var = float(np.var(pat_mean))
        # task effect
        task_mean = sub.groupby("task")[f].mean()
        task_var = float(np.var(task_mean))
        # residual
        total = float(np.var(x))
        var_rows.append({
            "feature": f,
            "patient_var": pat_var,
            "task_var": task_var,
            "total_var": total,
            "patient_share": pat_var / total if total > 0 else float("nan"),
            "task_share": task_var / total if total > 0 else float("nan"),
        })
    vdf = pd.DataFrame(var_rows).sort_values("task_share", ascending=False)
    vdf.to_csv(args.output_dir / "variance_partition.csv", index=False)
    print("\n  Top 10 features dominated by TASK:")
    print(vdf.head(10).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n  Top 10 features dominated by PATIENT (where task contributes least):")
    print(vdf.sort_values("task_share").head(10).to_string(
        index=False, float_format=lambda v: f"{v:.4f}"))

    # ----- Within-patient cross-task correlation of feature vectors -----
    print("\n--- within-patient cross-task feature correlation ---")
    rows_wcorr = []
    for pat in multi_task_pats:
        rows_p = sub[sub.participant_id == pat]
        tasks = rows_p["task"].unique()
        if len(tasks) < 2:
            continue
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1, t2 = tasks[i], tasks[j]
                v1 = rows_p[rows_p.task == t1][feat_cols].iloc[0]
                v2 = rows_p[rows_p.task == t2][feat_cols].iloc[0]
                v1 = pd.to_numeric(v1, errors="coerce")
                v2 = pd.to_numeric(v2, errors="coerce")
                ok = v1.notna() & v2.notna()
                if ok.sum() < 5:
                    continue
                corr = float(np.corrcoef(v1[ok], v2[ok])[0, 1])
                rows_wcorr.append({"patient_id": pat,
                                   "task_a": t1, "task_b": t2,
                                   "feature_corr": corr})
    wcorr = pd.DataFrame(rows_wcorr)
    wcorr.to_csv(args.output_dir / "within_patient_task_corr.csv", index=False)
    if len(wcorr):
        print(f"  {len(wcorr)} cross-task pairs from "
              f"{wcorr['patient_id'].nunique()} patients")
        print(f"  feature-vector correlation: "
              f"mean={wcorr['feature_corr'].mean():+.3f}  "
              f"median={wcorr['feature_corr'].median():+.3f}  "
              f"min={wcorr['feature_corr'].min():+.3f}  "
              f"max={wcorr['feature_corr'].max():+.3f}")
        print(f"\n  Median per task pair:")
        pair_med = wcorr.groupby(["task_a", "task_b"])["feature_corr"].agg(
            ["count", "median"]).reset_index().sort_values("count", ascending=False)
        print(pair_med.head(15).to_string(index=False,
                                           float_format=lambda v: f"{v:.3f}"))

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
