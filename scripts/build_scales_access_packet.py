#!/usr/bin/env python3
"""Build the SCALES access packet and minimum analysis plan.

We do not yet have the participant-level UKDS files. This script turns the
local user guide and current project priorities into a reproducible packet:
which variables to request, why they matter, and what analyses run first.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scales_access_packet"
DOC_PATH = ROOT / "docs" / "scales_access_packet.md"


VARIABLE_GROUPS = [
    {
        "domain": "identifiers_design",
        "priority": "required",
        "variables": "childid; scales_schoolt1; q5gender; ethnicityt1; idaci_quintilet1; aget1; agemthst2; agemthst3; agemthst4; Agemthst5; lag1; lag2; lag3; lag4; sampling weights/strata/auxiliary variables if included",
        "waves": "T1-T5",
        "analysis_role": "participant linkage, school clustering, age adjustment, design weighting, fairness/sampling audit",
        "why_needed": "SCALES intentionally over-sampled sex and season-of-birth strata; all longitudinal models need age/lag and design variables.",
    },
    {
        "domain": "screening_context",
        "priority": "required",
        "variables": "ccctotalt1; z_cctotalt1; q11schoolaction; q13nophrasespeech; q14slt; q15edpsych; anyconcernst1; q17nodiagnoses; q17asd; q17speechlanguagedisorder; neweyfsptotalt1; neweyfsp_gldcatt1; T1 SDQ variables",
        "waves": "T1",
        "analysis_role": "pre-intensive baseline risk, teacher concern, school support, early functional impairment",
        "why_needed": "Lets us test whether later language state adds value beyond the earliest teacher-screening and school-support signals.",
    },
    {
        "domain": "diagnostic_labels",
        "priority": "required",
        "variables": "LDt2; DLDt2; biomedical/additional-diagnosis indicators used to derive DLD if available",
        "waves": "T2",
        "analysis_role": "label replication, subgroup definition, label-vs-dimensional-state comparison",
        "why_needed": "We need the published diagnostic construct, but the project question is whether dimensional state and movement outperform the label for outcomes.",
    },
    {
        "domain": "core_vocabulary",
        "priority": "required",
        "variables": "rowpvttotalt2-t5; eowpvttotalt2-t5",
        "waves": "T2-T5",
        "analysis_role": "receptive/expressive vocabulary trajectories",
        "why_needed": "Vocabulary is one axis in the language-state model and may diverge from grammar, phonology, and narrative trajectories.",
    },
    {
        "domain": "core_grammar_sentence_repetition",
        "priority": "required",
        "variables": "trogtotalt2; trogtotalt3; grammardecision_totalscoret5; sentrepcontenttotalt2-t4; sentrepfunctiontotalt2-t4; sentrepsentencetotalt2-t4; sentrepverbtotalt2-t4",
        "waves": "T2-T5",
        "analysis_role": "grammar comprehension, grammaticality judgment, sentence repetition level and scoring method comparison",
        "why_needed": "This directly connects Brian's structured-task advice, the Fiveash pilot, and Ward et al.'s SCALES sentence-repetition result.",
    },
    {
        "domain": "narrative_discourse",
        "priority": "required",
        "variables": "narrativerecalltotalt2-t4; narrativecomptotalt2-t4; narrativecompliteraltotalt2-t4; narrativecompinferencetotalt2-t4; audio availability/derived narrative transcripts if separately accessible",
        "waves": "T2-T4",
        "analysis_role": "ecological language/discourse axis, content recall, literal/inference comprehension",
        "why_needed": "Narrative is the closest SCALES analogue to the natural-speech/discourse state we have been modeling in CHILDES/AphasiaBank.",
    },
    {
        "domain": "clinical_markers_phonology_speech",
        "priority": "required",
        "variables": "ptt20completedt2; ptt20acct2; pttirregcorrectt2; pttregcorrectt2; nwrephightotalt2-t3; nwreplowtotalt2-t3; nwreptotalt2-t3; phonemedeletiontotalt2; deappcct2-t3; ddk*totalt2-t3; ddk*ratesecaveragt2-t3; hearingscreent2-t3",
        "waves": "T2-T3",
        "analysis_role": "mechanistic markers for morphology, phonological memory, speech sound production, motor speech rate, hearing confounds",
        "why_needed": "These variables let us ask which mechanism predicts persistence, literacy risk, or recovery rather than treating DLD as one condition.",
    },
    {
        "domain": "nonverbal_iq_and_cognition",
        "priority": "required",
        "variables": "blockdesigntotalt2-t4; matrixreasoningtotalt2-t5; executive-function and processing-speed variables including visual search, go/no-go, SOPT, SwIFT, WISC coding, reaction time, RAN",
        "waves": "T2-T5",
        "analysis_role": "NVIQ gatekeeping audit, cognitive covariates, competing explanations for language-growth trajectories",
        "why_needed": "Norbury et al. showed NVIQ criteria affect service access; our models must quantify whether NVIQ changes prognosis or just excludes children.",
    },
    {
        "domain": "literacy",
        "priority": "required",
        "variables": "cc2irregulartotalt2-t5; cc2nonwordtotalt2-t5; cc2regulartotalt2-t5; cc2totalt2-t5; yarclettersoundknowledgetotalt2-t3; yarc reading comprehension/error/rate/time variables at T3 and T5",
        "waves": "T2-T5",
        "analysis_role": "long-term functional outcome, reading mechanism, school-impact validation",
        "why_needed": "A clinically useful child-language state model should predict reading and academic risk, not just language-test status.",
    },
    {
        "domain": "social_emotional_mental_health",
        "priority": "high",
        "variables": "CCC-S/CCC-2 parent and teacher totals; SDQ parent/teacher/child subscales; SWAN; social skills/theory of mind; implicature comprehension; RCADS; MSLSS; bullying/victimization variables",
        "waves": "T2-T5",
        "analysis_role": "functional impact, mental-health sequelae, pragmatic/social-language pathways",
        "why_needed": "SCALES was designed to study language and socioemotional development through secondary-school transition; this is the high-impact outcome layer.",
    },
    {
        "domain": "school_support_and_send",
        "priority": "high",
        "variables": "schooltypet2-t4; SEND variables; parent/teacher reports of school support, referrals, special educational needs, and service use",
        "waves": "T2-T5",
        "analysis_role": "care pathway, service-need prediction, whether models identify unsupported children",
        "why_needed": "The end goal is better care. These variables tell us whether language-state profiles map to support received or missed.",
    },
]


MODEL_PLAN = [
    {
        "order": 1,
        "model": "data_quality_and_cohort_reconstruction",
        "question": "Can we exactly reconstruct the intensive cohort, wave participation, design strata, and published LD/DLD labels?",
        "minimum_variables": "childid, design variables, age/lags, LDt2, DLDt2, core language scores",
        "success_criterion": "Published Ns and label prevalence reproduce within documentation tolerance; missingness maps are explicit before modeling.",
    },
    {
        "order": 2,
        "model": "sentence_repetition_replication_plus_extension",
        "question": "Does sentence repetition remain a robust DLD marker across scoring methods, and does it predict later literacy/mental-health outcomes beyond DLD label?",
        "minimum_variables": "sentrepsentence/content/function/verb T2-T4, DLDt2, age, NVIQ, literacy and SDQ/RCADS outcomes",
        "success_criterion": "Replicate Ward et al. diagnostic signal, then show whether SR adds longitudinal prognostic information.",
    },
    {
        "order": 3,
        "model": "early_movement_beats_baseline",
        "question": "Does T2-to-T3 language-state movement predict T4/T5 language, literacy, and support outcomes better than T2 severity?",
        "minimum_variables": "T2/T3 repeated language measures, lag2, T4/T5 outcomes",
        "success_criterion": "Movement improves held-out prediction and calibration beyond baseline state, age, NVIQ, and screening risk.",
    },
    {
        "order": 4,
        "model": "mechanistic_subtype_discovery",
        "question": "Are there reproducible profiles such as grammar-specific, vocabulary-plus-narrative, phonological-memory, speech-sound, or pragmatic/social-language risk?",
        "minimum_variables": "core language, PTT, NWR, DEAP, DDK, CCC, social/pragmatic measures",
        "success_criterion": "Clusters/factors replicate across bootstraps and predict distinct downstream outcomes.",
    },
    {
        "order": 5,
        "model": "nviq_gatekeeping_fairness",
        "question": "Does nonverbal IQ meaningfully change prognosis or treatment-relevant profile after language state is measured?",
        "minimum_variables": "block design, matrix reasoning, language outcomes, literacy/mental health outcomes, demographics",
        "success_criterion": "Clear estimate of what is lost by excluding low-average NVIQ children from language services.",
    },
    {
        "order": 6,
        "model": "minimal_assessment_policy",
        "question": "What is the smallest feasible battery that preserves prediction of long-term functional outcomes?",
        "minimum_variables": "all core language domains plus literacy/social-emotional outcomes",
        "success_criterion": "Greedy/regularized task subsets identify a short battery with calibrated uncertainty and explicit failure cases.",
    },
]


def write_markdown(variable_map: pd.DataFrame, model_plan: pd.DataFrame) -> str:
    def md_table(frame: pd.DataFrame) -> str:
        cols = list(frame.columns)
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, row in frame.iterrows():
            cells = [str(row[col]).replace("|", "/") for col in cols]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    lines = [
        "# SCALES Access Packet and Analysis Plan",
        "",
        "## Why SCALES Matters",
        "",
        "SCALES is the strongest next dataset for the original project vision: a population-enriched child-language cohort with longitudinal language, literacy, cognition, school, and socioemotional outcomes. It is not a treatment dataset, but it can answer the prerequisite clinical-science question: which early language states and state changes actually predict later functional risk?",
        "",
        "Current access status: the University of Surrey repository page for SCALES Study 8968 says the data are held by UK Data Service and are **Safeguarded Restricted**, with access potentially granted on request. Dataset citation: Norbury, C. (2022), *Surrey Communication and Language in Education Study: Intensive Data T2-T5, 2012-2020*, UK Data Service, SN 8968, DOI: https://doi.org/10.5255/UKDA-SN-8968-1.",
        "",
        "Key scientific context:",
        "",
        "- Norbury et al. (2016), `10.1111/jcpp.12573`, showed that language disorder prevalence and service implications depend strongly on diagnostic criteria and that NVIQ-based exclusion can deny care to children with real language needs.",
        "- The 2025 SCALES cohort profile reports the longitudinal intensive sample through Year 8 and confirms public UKDS availability for screening and intensive releases.",
        "- Ward, Bannard, Norbury, and Polisenska (2026), `10.1044/2025_JSLHR-25-00058`, used SCALES to show sentence repetition is robust as a DLD marker, but additional assessment is still needed for clinical decision-making.",
        "",
        "## Access Request Rationale",
        "",
        "We should request SCALES 8968 to run secondary analyses that are aligned with the dataset's purpose and minimize clinical risk:",
        "",
        "1. Reconstruct published labels and wave participation before any new modeling.",
        "2. Test dimensional language-state and early-growth models against later literacy, school, and mental-health outcomes.",
        "3. Evaluate whether sentence repetition, narrative recall/comprehension, vocabulary, phonology, and speech measures carry different prognostic information.",
        "4. Audit NVIQ and demographic/service-access effects so models do not reproduce harmful gatekeeping.",
        "5. Produce open code and aggregate results only; no re-identification, no release of participant-level data, and no clinical deployment claims.",
        "",
        "## Minimum Variable Map",
        "",
        md_table(variable_map[["domain", "priority", "waves", "analysis_role"]]),
        "",
        "Full variable details are in `variable_request_map.csv`.",
        "",
        "## First Models After Access",
        "",
        md_table(model_plan[["order", "model", "question", "success_criterion"]]),
        "",
        "## What This Would Let Us Discover",
        "",
        "- Whether DLD persistence is better understood as a fixed diagnosis or as movement through a multidimensional language state.",
        "- Whether sentence repetition is mainly a screening marker, a mechanism marker, or a longitudinal risk marker.",
        "- Whether narrative/content measures explain later functional impact beyond vocabulary and grammar tests.",
        "- Whether low-average NVIQ changes the language-growth trajectory or mainly changes service eligibility.",
        "- Which short assessment battery best predicts outcomes an SLP and family actually care about.",
        "",
        "## Immediate Next Step",
        "",
        "Submit the UKDS/Safeguarded Restricted access request with this rationale, then run the model plan in order as soon as the participant-level files are available.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    variable_map = pd.DataFrame(VARIABLE_GROUPS)
    model_plan = pd.DataFrame(MODEL_PLAN)

    variable_map.to_csv(OUT_DIR / "variable_request_map.csv", index=False)
    model_plan.to_csv(OUT_DIR / "minimum_model_plan.csv", index=False)

    md = write_markdown(variable_map, model_plan)
    (OUT_DIR / "summary.md").write_text(md, encoding="utf-8")
    DOC_PATH.write_text(md, encoding="utf-8")
    print(f"Wrote {DOC_PATH}")
    print(f"Wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
