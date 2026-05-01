"""Reusable data-quality gates for publication-facing experiments.

The goal is not to make dirty data disappear. It is to make failure modes
visible before a model produces an impressive number:

* duplicate IDs;
* missing participant/transcript identifiers;
* row-wise train/test participant leakage;
* high feature missingness or all-zero artifacts;
* missing CHAT time marks for audio-linked analyses;
* stale TalkBank media authentication.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
import requests
from sklearn.model_selection import GroupKFold, KFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.talkbank_media import load_dotenv, request_headers  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--aphasia-features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--childes-features",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--aphasia-transcripts",
                   default="data/features/aphasiabank_transcripts.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/data_quality_gates", type=Path)
    p.add_argument("--time-mark-limit", type=int, default=0,
                   help="0 = scan all AphasiaBank transcript index rows.")
    p.add_argument("--strict", action="store_true",
                   help="Exit nonzero when any required gate fails.")
    return p.parse_args()


def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    show = df.head(max_rows).copy()
    cols = list(show.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in show.itertuples(index=False):
        vals = []
        for value in row:
            if isinstance(value, float):
                vals.append(f"{value:.4g}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def feature_table_audit(path: Path, table_name: str) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if not path.exists():
        return pd.DataFrame([{
            "table": table_name,
            "gate": "file_exists",
            "status": "FAIL",
            "detail": str(path),
            "value": np.nan,
        }]), None

    df = pd.read_parquet(path)
    rows = []
    rows.append({
        "table": table_name,
        "gate": "file_exists",
        "status": "PASS",
        "detail": str(path),
        "value": 1,
    })
    rows.append({
        "table": table_name,
        "gate": "row_count",
        "status": "PASS" if len(df) > 0 else "FAIL",
        "detail": "rows",
        "value": len(df),
    })

    for col in ["window_id", "transcript_id"]:
        if col in df.columns:
            n_missing = int(df[col].isna().sum())
            n_dup_rows = int(df[col].duplicated(keep=False).sum())
            n_dup_ids = int(df.loc[df[col].duplicated(keep=False), col].nunique(dropna=True))
            rows.append({
                "table": table_name,
                "gate": f"{col}_present",
                "status": "PASS",
                "detail": col,
                "value": 1,
            })
            rows.append({
                "table": table_name,
                "gate": f"{col}_missing",
                "status": "PASS" if n_missing == 0 else "FAIL",
                "detail": "missing rows",
                "value": n_missing,
            })
            rows.append({
                "table": table_name,
                "gate": f"{col}_duplicate_rows" if col == "window_id" else f"{col}_repeated_windows",
                "status": ("PASS" if n_dup_rows == 0 else "FAIL") if col == "window_id" else "INFO",
                "detail": f"{n_dup_ids} duplicated IDs",
                "value": n_dup_rows,
            })
        else:
            rows.append({
                "table": table_name,
                "gate": f"{col}_present",
                "status": "FAIL",
                "detail": col,
                "value": 0,
            })

    participant_col = "participant_id" if "participant_id" in df.columns else "child_id"
    if participant_col in df.columns:
        rows.append({
            "table": table_name,
            "gate": "participant_id_missing",
            "status": "PASS" if df[participant_col].isna().sum() == 0 else "FAIL",
            "detail": participant_col,
            "value": int(df[participant_col].isna().sum()),
        })
        rows.append({
            "table": table_name,
            "gate": "participant_count",
            "status": "PASS" if df[participant_col].nunique(dropna=True) >= 10 else "WARN",
            "detail": participant_col,
            "value": int(df[participant_col].nunique(dropna=True)),
        })

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if numeric_cols:
        missing = df[numeric_cols].isna().mean()
        all_zero = [
            c for c in numeric_cols
            if df[c].fillna(0).eq(0).all()
        ]
        rows.append({
            "table": table_name,
            "gate": "numeric_feature_columns",
            "status": "PASS",
            "detail": "numeric columns",
            "value": len(numeric_cols),
        })
        rows.append({
            "table": table_name,
            "gate": "columns_over_50pct_missing",
            "status": "PASS" if int((missing > 0.5).sum()) == 0 else "WARN",
            "detail": "numeric columns",
            "value": int((missing > 0.5).sum()),
        })
        rows.append({
            "table": table_name,
            "gate": "all_zero_numeric_columns",
            "status": "PASS" if not all_zero else "WARN",
            "detail": ", ".join(all_zero[:10]),
            "value": len(all_zero),
        })

    return pd.DataFrame(rows), df


def split_leakage_audit(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    participant_col = "patient_root" if "patient_root" in df.columns else None
    if participant_col is None:
        participant_col = "participant_id" if "participant_id" in df.columns else None
    if participant_col is None:
        participant_col = "child_id" if "child_id" in df.columns else None
    if participant_col is None or len(df) < 2:
        return pd.DataFrame([{
            "table": table_name,
            "splitter": "group",
            "fold": -1,
            "train_test_group_overlap": np.nan,
            "status": "SKIP",
            "detail": "no participant grouping column",
        }])

    work = df.dropna(subset=[participant_col]).reset_index(drop=True)
    groups = work[participant_col].astype(str).to_numpy()
    n_groups = len(np.unique(groups))
    if n_groups < 2:
        return pd.DataFrame([{
            "table": table_name,
            "splitter": "group",
            "fold": -1,
            "train_test_group_overlap": n_groups,
            "status": "FAIL",
            "detail": f"only {n_groups} groups",
        }])

    rows = []
    gkf = GroupKFold(n_splits=max(2, min(5, n_groups)))
    for fold, (tr, te) in enumerate(gkf.split(work, groups=groups)):
        overlap = len(set(groups[tr]) & set(groups[te]))
        rows.append({
            "table": table_name,
            "splitter": "GroupKFold",
            "fold": fold,
            "train_test_group_overlap": overlap,
            "status": "PASS" if overlap == 0 else "FAIL",
            "detail": participant_col,
        })

    if len(work) >= 5:
        kf = KFold(n_splits=min(5, len(work)), shuffle=True, random_state=0)
        naive_overlaps = []
        for tr, te in kf.split(work):
            naive_overlaps.append(len(set(groups[tr]) & set(groups[te])))
        rows.append({
            "table": table_name,
            "splitter": "naive_KFold_demonstration",
            "fold": -1,
            "train_test_group_overlap": int(np.mean(naive_overlaps)),
            "status": "WARN" if np.mean(naive_overlaps) > 0 else "PASS",
            "detail": "expected leakage if row-wise KFold is used",
        })
    return pd.DataFrame(rows)


def time_mark_audit(transcripts_path: Path, limit: int) -> pd.DataFrame:
    if not transcripts_path.exists():
        return pd.DataFrame([{
            "transcript_id": "",
            "file_path": str(transcripts_path),
            "status": "missing_transcript_index",
            "par_utts": 0,
            "par_utts_with_time_marks": 0,
            "time_mark_fraction": 0.0,
            "invalid_time_marks": 0,
        }])
    idx = pd.read_parquet(transcripts_path)
    if "file_path" not in idx.columns:
        return pd.DataFrame()
    cols = [c for c in ["transcript_id", "file_path", "corpus"] if c in idx.columns]
    files = idx[cols].drop_duplicates("file_path").copy()
    if limit > 0:
        files = files.head(limit)

    rows = []
    for rec in files.itertuples(index=False):
        file_path = Path(getattr(rec, "file_path"))
        tid = getattr(rec, "transcript_id", file_path.stem)
        corpus = getattr(rec, "corpus", "")
        if not file_path.exists():
            rows.append({
                "transcript_id": tid,
                "corpus": corpus,
                "file_path": str(file_path),
                "status": "missing_file",
                "par_utts": 0,
                "par_utts_with_time_marks": 0,
                "time_mark_fraction": 0.0,
                "invalid_time_marks": 0,
            })
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                chat = pla.read_chat(str(file_path), strict=False)
            par = [u for u in chat.utterances() if u.participant == "PAR"]
            with_tm = 0
            invalid = 0
            for utt in par:
                tm = utt.time_marks
                if tm is None or len(tm) != 2:
                    continue
                if tm[1] <= tm[0]:
                    invalid += 1
                else:
                    with_tm += 1
            rows.append({
                "transcript_id": tid,
                "corpus": corpus,
                "file_path": str(file_path),
                "status": "ok",
                "par_utts": len(par),
                "par_utts_with_time_marks": with_tm,
                "time_mark_fraction": with_tm / len(par) if par else 0.0,
                "invalid_time_marks": invalid,
            })
        except Exception as exc:
            rows.append({
                "transcript_id": tid,
                "corpus": corpus,
                "file_path": str(file_path),
                "status": f"read_error:{type(exc).__name__}",
                "par_utts": 0,
                "par_utts_with_time_marks": 0,
                "time_mark_fraction": 0.0,
                "invalid_time_marks": 0,
            })
    return pd.DataFrame(rows)


def media_auth_audit() -> pd.DataFrame:
    load_dotenv()
    headers, _, source = request_headers()
    if "Cookie" not in headers:
        return pd.DataFrame([{
            "gate": "talkbank_media_auth",
            "status": "WARN",
            "detail": "no TALKBANK_COOKIE_HEADER or APHASIABANK_COOKIE",
        }])
    url = (
        "https://media.talkbank.org/aphasia/English/Protocol/"
        "NEURAL-2/Control/103-1.mp4"
    )
    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=20,
            allow_redirects=True,
            stream=True,
        )
        content_type = r.headers.get("content-type", "")
        first = next(r.iter_content(chunk_size=32), b"")
        is_html = "text/html" in content_type.lower() or first.lstrip().startswith(b"<html")
        return pd.DataFrame([{
            "gate": "talkbank_media_auth",
            "status": "FAIL" if is_html or r.status_code >= 400 else "PASS",
            "detail": f"source={source}; status={r.status_code}; content_type={content_type}",
        }])
    except Exception as exc:
        return pd.DataFrame([{
            "gate": "talkbank_media_auth",
            "status": "FAIL",
            "detail": f"{type(exc).__name__}: {exc}",
        }])


def write_summary(
    out_dir: Path,
    gates: pd.DataFrame,
    split_gates: pd.DataFrame,
    time_marks: pd.DataFrame,
    media: pd.DataFrame,
) -> None:
    fail_count = int((gates["status"] == "FAIL").sum()) + int((split_gates["status"] == "FAIL").sum())
    warn_count = int((gates["status"] == "WARN").sum()) + int((split_gates["status"] == "WARN").sum())
    media_status = media.iloc[0]["status"] if not media.empty else "SKIP"

    tm_summary = pd.DataFrame()
    if not time_marks.empty and "status" in time_marks.columns:
        ok = time_marks[time_marks["status"] == "ok"].copy()
        if not ok.empty:
            tm_summary = ok.groupby("corpus", dropna=False).agg(
                files=("file_path", "nunique"),
                median_time_mark_fraction=("time_mark_fraction", "median"),
                transcripts_under_80pct=("time_mark_fraction", lambda x: int((x < 0.8).sum())),
                total_invalid_time_marks=("invalid_time_marks", "sum"),
            ).reset_index().sort_values("files", ascending=False)

    lines = [
        "# Data Quality Gates",
        "",
        f"- Required gate failures: {fail_count}",
        f"- Warnings: {warn_count}",
        f"- TalkBank media auth: {media_status}",
        "",
        "## Feature Table Gates",
        "",
        md_table(gates),
        "",
        "## Split Leakage Gates",
        "",
        md_table(split_gates),
        "",
        "## TalkBank Media Auth",
        "",
        md_table(media),
        "",
        "## Time-Mark Summary By Corpus",
        "",
        md_table(tm_summary),
        "",
        "## Interpretation",
        "",
        "A headline experiment is not review-grade until required ID gates pass, "
        "participant-level splits show zero train/test overlap, and audio-linked "
        "analyses either have adequate time marks or explicitly exclude sessions "
        "that do not.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    gate_frames = []
    split_frames = []
    for path, name in [
        (args.aphasia_features, "aphasia_windowed"),
        (args.childes_features, "childes_windowed"),
    ]:
        gates, df = feature_table_audit(path, name)
        gate_frames.append(gates)
        if df is not None:
            split_frames.append(split_leakage_audit(df, name))

    gates_df = pd.concat(gate_frames, ignore_index=True)
    splits_df = pd.concat(split_frames, ignore_index=True) if split_frames else pd.DataFrame()
    time_marks_df = time_mark_audit(args.aphasia_transcripts, args.time_mark_limit)
    media_df = media_auth_audit()

    gates_df.to_csv(args.output_dir / "feature_table_gates.csv", index=False)
    splits_df.to_csv(args.output_dir / "split_leakage_gates.csv", index=False)
    time_marks_df.to_csv(args.output_dir / "aphasia_time_mark_audit.csv", index=False)
    media_df.to_csv(args.output_dir / "media_auth_gate.csv", index=False)
    write_summary(args.output_dir, gates_df, splits_df, time_marks_df, media_df)

    print(f"wrote {args.output_dir / 'summary.md'}")

    if args.strict:
        n_fail = int((gates_df["status"] == "FAIL").sum()) + int((splits_df["status"] == "FAIL").sum())
        if not media_df.empty and media_df.iloc[0]["status"] == "FAIL":
            n_fail += 1
        if n_fail:
            sys.exit(1)


if __name__ == "__main__":
    main()
