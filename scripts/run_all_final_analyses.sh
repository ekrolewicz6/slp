#!/usr/bin/env bash
# When all background extractors have finished, run the final analyses
# that depend on acoustic + fine-tuned-embedding outputs.

set -e
cd "$(dirname "$0")/.."

echo "===== Phase 2 with structural + embeddings + acoustic ====="
.venv/bin/python -m scripts.run_phase2_with_acoustics 2>&1 | tee outputs/phase2_aphasia_acoustic_log.txt

echo ""
echo "===== Cross-population mapping (re-run with acoustics if available) ====="
# The cross_population script doesn't yet support acoustic features as
# input — but it can still benefit from being re-run with embeddings
# active.
.venv/bin/python -m scripts.run_cross_population_mapping --use-embeddings \
  2>&1 | tee outputs/cross_population_with_emb_log.txt

echo ""
echo "===== Fine-tuned embedder: re-test Wernicke F1 ====="
.venv/bin/python -m scripts.test_finetuned_embeddings \
  2>&1 | tee outputs/finetuned_embedder_log.txt

echo ""
echo "All final analyses complete. Outputs in outputs/."
