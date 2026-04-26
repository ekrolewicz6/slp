"""Per-transcript feature extraction.

Operates on lists of `pylangacq.Utterance` filtered to a single participant
(typically `CHI`). Produces a flat dict of numeric features per transcript.

Feature groups (see SPEC §Phase 1):

- KidEval-style: MLU (words & morphemes), NDW, total tokens, verbs/utterance.
- Lexical: type-token ratio, function-word ratio, hapax ratio.
- Utterance-shape: mean/std/p10/p50/p90 utterance length in tokens.
- Sagae-style syntax: POS distribution, dependency-relation distribution,
  mean dependency distance, head-dep & head-rel-dep n-gram counts.
- Disfluency markers: repetition / retracing rates from %mor tier annotations.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Iterable

# CHAT POS tags for closed-class function words (used for function-word ratio).
FUNCTION_POS_PREFIXES = (
    "det",      # determiners
    "pro",      # pronouns
    "prep",     # prepositions
    "conj",     # conjunctions
    "coord",    # coordinators
    "aux",      # auxiliaries
    "mod",      # modals
    "inf",      # infinitival "to"
    "qn",       # quantifiers
    "co",       # communicators (uh, oh)
    "neg",      # negators
)

# Top POS categories tracked individually as fractions.
TRACKED_POS = ("n", "v", "adj", "adv", "pro", "det", "prep", "aux", "mod",
               "conj", "coord", "co", "part", "qn", "neg", "inf")

# Top dependency relations tracked individually as fractions.
TRACKED_REL = ("SUBJ", "OBJ", "DET", "MOD", "ROOT", "COORD", "PUNCT",
               "PRED", "JCT", "AUX", "NEG", "COMP", "POBJ", "INF")


def _safe_div(num: float, denom: float, default: float = 0.0) -> float:
    return num / denom if denom else default


def _utterance_tokens(utt) -> list:
    """Filter out punctuation/empty tokens; keep real word tokens."""
    out = []
    for t in utt.tokens:
        word = (t.word or "").strip()
        if not word or word in {".", "?", "!", ",", ";", ":"}:
            continue
        out.append(t)
    return out


# Map Universal-Dependencies POS tags (used in AphasiaBank) onto the CHILDES
# MOR convention (used in Eng-NA / Eng-UK / Clinical-Eng). Anything not listed
# is passed through unchanged. Applied inside `_pos_root` so all downstream
# features see one tag space.
_UD_TO_MOR = {
    "verb": "v",
    "noun": "n",
    "propn": "n:prop",
    "adp": "prep",
    "pron": "pro",
    "intj": "co",
    "punct": "punct",
    "sym": "sym",
    "num": "qn",
    # adv, adj, det, aux, conj, cm, part, neg already match across both.
}


def _pos_root(pos: str | None) -> str:
    """Strip POS subtype and normalise UD → MOR convention.

    Examples:
      "det:art"     → "det"
      "verb"        → "v"     (UD)
      "noun-Acc"    → "n"     (UD with morphology suffix; '-' stripped)
      "n:prop"      → "n:prop" (MOR sub-tag for proper noun, kept intact)
    """
    if not pos:
        return ""
    head = pos.split(":", 1)[0]
    head = head.split("-", 1)[0]  # strip UD morphology suffixes (Acc, Plur, ...)
    return _UD_TO_MOR.get(head, head)


def extract_features(
    utterances: Iterable,
    *,
    participant: str = "CHI",
    min_utterances: int = 20,
) -> dict[str, float] | None:
    """Compute all features for one transcript's utterances.

    Returns None if the participant produced fewer than `min_utterances`
    usable utterances — those transcripts are dropped from training.
    """
    chi_utts = [u for u in utterances if u.participant == participant and _utterance_tokens(u)]
    if len(chi_utts) < min_utterances:
        return None

    feats: dict[str, float] = {}
    feats.update(_kideval_features(chi_utts))
    feats.update(_lexical_features(chi_utts))
    feats.update(_utterance_shape_features(chi_utts))
    feats.update(_pos_features(chi_utts))
    feats.update(_dependency_features(chi_utts))
    feats.update(_disfluency_features(chi_utts))
    feats["n_utterances"] = float(len(chi_utts))
    return feats


# ---- KidEval-style ----------------------------------------------------------

def _kideval_features(utts) -> dict[str, float]:
    n_utts = len(utts)
    word_lens = []
    morph_counts = []
    verb_count = 0
    word_types = set()
    total_words = 0

    for u in utts:
        toks = _utterance_tokens(u)
        word_lens.append(len(toks))
        # morpheme count: count `-` (suffix) and `&` (fusion) markers in mor tag.
        morphs = 0
        for t in toks:
            mor = t.mor or ""
            morphs += 1 + mor.count("-") + mor.count("&") + mor.count("~")
            word = (t.word or "").lower()
            if word:
                word_types.add(word)
                total_words += 1
            if _pos_root(t.pos) == "v":
                verb_count += 1
        morph_counts.append(morphs)

    return {
        "mlu_words": _safe_div(sum(word_lens), n_utts),
        "mlu_morphemes": _safe_div(sum(morph_counts), n_utts),
        "ndw": float(len(word_types)),
        "total_words": float(total_words),
        "verbs_per_utterance": _safe_div(verb_count, n_utts),
    }


# ---- Lexical ----------------------------------------------------------------

def _lexical_features(utts) -> dict[str, float]:
    word_counter: Counter = Counter()
    func_count = 0
    content_count = 0
    for u in utts:
        for t in _utterance_tokens(u):
            w = (t.word or "").lower()
            if not w:
                continue
            word_counter[w] += 1
            pos = _pos_root(t.pos)
            if pos and pos.startswith(FUNCTION_POS_PREFIXES):
                func_count += 1
            elif pos:
                content_count += 1
    total = sum(word_counter.values())
    hapax = sum(1 for c in word_counter.values() if c == 1)
    return {
        "ttr": _safe_div(len(word_counter), total),
        "function_word_ratio": _safe_div(func_count, func_count + content_count),
        "hapax_ratio": _safe_div(hapax, len(word_counter)),
        "log_total_tokens": math.log1p(total),
    }


# ---- Utterance shape --------------------------------------------------------

def _utterance_shape_features(utts) -> dict[str, float]:
    lens = [len(_utterance_tokens(u)) for u in utts]
    if not lens:
        return {"utt_len_mean": 0.0, "utt_len_std": 0.0,
                "utt_len_p10": 0.0, "utt_len_p50": 0.0, "utt_len_p90": 0.0,
                "single_word_ratio": 0.0}
    sorted_lens = sorted(lens)

    def pct(p: float) -> float:
        idx = max(0, min(len(sorted_lens) - 1, int(p * (len(sorted_lens) - 1))))
        return float(sorted_lens[idx])

    return {
        "utt_len_mean": float(statistics.mean(lens)),
        "utt_len_std": float(statistics.pstdev(lens)) if len(lens) > 1 else 0.0,
        "utt_len_p10": pct(0.10),
        "utt_len_p50": pct(0.50),
        "utt_len_p90": pct(0.90),
        "single_word_ratio": _safe_div(sum(1 for length in lens if length == 1), len(lens)),
    }


# ---- POS distribution -------------------------------------------------------

def _pos_features(utts) -> dict[str, float]:
    counter: Counter = Counter()
    total = 0
    for u in utts:
        for t in _utterance_tokens(u):
            pos = _pos_root(t.pos)
            if not pos:
                continue
            counter[pos] += 1
            total += 1
    out = {}
    for pos in TRACKED_POS:
        out[f"pos_{pos}_frac"] = _safe_div(counter.get(pos, 0), total)
    out["pos_unique_tags"] = float(len(counter))
    return out


# ---- Dependency / Sagae-style syntax ---------------------------------------

def _dependency_features(utts) -> dict[str, float]:
    rel_counter: Counter = Counter()
    head_dep_pairs: Counter = Counter()
    head_rel_dep_triples: Counter = Counter()
    dep_distances: list[int] = []
    total_deps = 0

    for u in utts:
        toks = _utterance_tokens(u)
        for i, t in enumerate(toks):
            gra = t.gra
            if gra is None:
                continue
            rel = (gra.rel or "").upper()
            if rel:
                rel_counter[rel] += 1
                total_deps += 1
            head_idx = (gra.head or 0) - 1
            if 0 <= head_idx < len(toks):
                head_pos = _pos_root(toks[head_idx].pos) or "?"
                dep_pos = _pos_root(t.pos) or "?"
                head_dep_pairs[(head_pos, dep_pos)] += 1
                head_rel_dep_triples[(head_pos, rel, dep_pos)] += 1
                dep_distances.append(abs(head_idx - i))

    out = {}
    for rel in TRACKED_REL:
        out[f"rel_{rel}_frac"] = _safe_div(rel_counter.get(rel, 0), total_deps)
    out["unique_head_dep_pairs"] = float(len(head_dep_pairs))
    out["unique_head_rel_dep_triples"] = float(len(head_rel_dep_triples))
    out["mean_dep_distance"] = (
        float(statistics.mean(dep_distances)) if dep_distances else 0.0
    )
    out["max_dep_distance"] = float(max(dep_distances)) if dep_distances else 0.0
    return out


# ---- Disfluency / retracing -------------------------------------------------

def _disfluency_features(utts) -> dict[str, float]:
    """Approximate disfluency from raw CHAT markers in the main tier.

    pylangacq strips most markers from `.word`, so we read the raw tier text
    when available and count a few canonical CHAT conventions:
      - `[/]`  immediate repetition
      - `[//]` retracing with reformulation
      - `&-`   filled pauses (uh, um)
      - `(.)` and `(..)` short pauses
    """
    n_utts = len(utts)
    rep = retr = pause = filler = 0
    for u in utts:
        # pylangacq stores raw lines under `.tiers`, including the `*CHI:` line.
        raw = ""
        try:
            raw = u.tiers.get("CHI", "") or u.tiers.get("*CHI", "") or ""
        except Exception:
            raw = ""
        rep += raw.count("[/]")
        retr += raw.count("[//]")
        pause += raw.count("(.)") + raw.count("(..)") + raw.count("(...)")
        filler += raw.count("&-") + raw.count("&=")
    return {
        "repetition_per_utt": _safe_div(rep, n_utts),
        "retracing_per_utt": _safe_div(retr, n_utts),
        "pause_per_utt": _safe_div(pause, n_utts),
        "filler_per_utt": _safe_div(filler, n_utts),
    }
