# SCALES Access Packet and Analysis Plan

## Why SCALES Matters

SCALES is the strongest next dataset for the original project vision: a population-enriched child-language cohort with longitudinal language, literacy, cognition, school, and socioemotional outcomes. It is not a treatment dataset, but it can answer the prerequisite clinical-science question: which early language states and state changes actually predict later functional risk?

Current access status: the University of Surrey repository page for SCALES Study 8968 says the data are held by UK Data Service and are **Safeguarded Restricted**, with access potentially granted on request. Dataset citation: Norbury, C. (2022), *Surrey Communication and Language in Education Study: Intensive Data T2-T5, 2012-2020*, UK Data Service, SN 8968, DOI: https://doi.org/10.5255/UKDA-SN-8968-1.

Key scientific context:

- Norbury et al. (2016), `10.1111/jcpp.12573`, showed that language disorder prevalence and service implications depend strongly on diagnostic criteria and that NVIQ-based exclusion can deny care to children with real language needs.
- The 2025 SCALES cohort profile reports the longitudinal intensive sample through Year 8 and confirms public UKDS availability for screening and intensive releases.
- Ward, Bannard, Norbury, and Polisenska (2026), `10.1044/2025_JSLHR-25-00058`, used SCALES to show sentence repetition is robust as a DLD marker, but additional assessment is still needed for clinical decision-making.

## Access Request Rationale

We should request SCALES 8968 to run secondary analyses that are aligned with the dataset's purpose and minimize clinical risk:

1. Reconstruct published labels and wave participation before any new modeling.
2. Test dimensional language-state and early-growth models against later literacy, school, and mental-health outcomes.
3. Evaluate whether sentence repetition, narrative recall/comprehension, vocabulary, phonology, and speech measures carry different prognostic information.
4. Audit NVIQ and demographic/service-access effects so models do not reproduce harmful gatekeeping.
5. Produce open code and aggregate results only; no re-identification, no release of participant-level data, and no clinical deployment claims.

## Minimum Variable Map

| domain | priority | waves | analysis_role |
| --- | --- | --- | --- |
| identifiers_design | required | T1-T5 | participant linkage, school clustering, age adjustment, design weighting, fairness/sampling audit |
| screening_context | required | T1 | pre-intensive baseline risk, teacher concern, school support, early functional impairment |
| diagnostic_labels | required | T2 | label replication, subgroup definition, label-vs-dimensional-state comparison |
| core_vocabulary | required | T2-T5 | receptive/expressive vocabulary trajectories |
| core_grammar_sentence_repetition | required | T2-T5 | grammar comprehension, grammaticality judgment, sentence repetition level and scoring method comparison |
| narrative_discourse | required | T2-T4 | ecological language/discourse axis, content recall, literal/inference comprehension |
| clinical_markers_phonology_speech | required | T2-T3 | mechanistic markers for morphology, phonological memory, speech sound production, motor speech rate, hearing confounds |
| nonverbal_iq_and_cognition | required | T2-T5 | NVIQ gatekeeping audit, cognitive covariates, competing explanations for language-growth trajectories |
| literacy | required | T2-T5 | long-term functional outcome, reading mechanism, school-impact validation |
| social_emotional_mental_health | high | T2-T5 | functional impact, mental-health sequelae, pragmatic/social-language pathways |
| school_support_and_send | high | T2-T5 | care pathway, service-need prediction, whether models identify unsupported children |

Full variable details are in `variable_request_map.csv`.

## First Models After Access

| order | model | question | success_criterion |
| --- | --- | --- | --- |
| 1 | data_quality_and_cohort_reconstruction | Can we exactly reconstruct the intensive cohort, wave participation, design strata, and published LD/DLD labels? | Published Ns and label prevalence reproduce within documentation tolerance; missingness maps are explicit before modeling. |
| 2 | sentence_repetition_replication_plus_extension | Does sentence repetition remain a robust DLD marker across scoring methods, and does it predict later literacy/mental-health outcomes beyond DLD label? | Replicate Ward et al. diagnostic signal, then show whether SR adds longitudinal prognostic information. |
| 3 | early_movement_beats_baseline | Does T2-to-T3 language-state movement predict T4/T5 language, literacy, and support outcomes better than T2 severity? | Movement improves held-out prediction and calibration beyond baseline state, age, NVIQ, and screening risk. |
| 4 | mechanistic_subtype_discovery | Are there reproducible profiles such as grammar-specific, vocabulary-plus-narrative, phonological-memory, speech-sound, or pragmatic/social-language risk? | Clusters/factors replicate across bootstraps and predict distinct downstream outcomes. |
| 5 | nviq_gatekeeping_fairness | Does nonverbal IQ meaningfully change prognosis or treatment-relevant profile after language state is measured? | Clear estimate of what is lost by excluding low-average NVIQ children from language services. |
| 6 | minimal_assessment_policy | What is the smallest feasible battery that preserves prediction of long-term functional outcomes? | Greedy/regularized task subsets identify a short battery with calibrated uncertainty and explicit failure cases. |

## What This Would Let Us Discover

- Whether DLD persistence is better understood as a fixed diagnosis or as movement through a multidimensional language state.
- Whether sentence repetition is mainly a screening marker, a mechanism marker, or a longitudinal risk marker.
- Whether narrative/content measures explain later functional impact beyond vocabulary and grammar tests.
- Whether low-average NVIQ changes the language-growth trajectory or mainly changes service eligibility.
- Which short assessment battery best predicts outcomes an SLP and family actually care about.

## Immediate Next Step

Submit the UKDS/Safeguarded Restricted access request with this rationale, then run the model plan in order as soon as the participant-level files are available.
