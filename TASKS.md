# Language-State Modeling Task Board

**Last updated:** 2026-05-01
**Source plan:** `docs/post_brian_ordered_task_list.md`

This is the working board. The detailed rationale lives in the ordered plan; this file is for execution.

## Doing

- [ ] None. Current local-data work is either completed or blocked on external data/access/review.

## Next

- [ ] **DLD EMT-SF treatment-response pilot.** Run after the Dryad dataset is downloaded into `data/external/dryad_emt_sf_dld/`.

## Backlog

- [ ] **4.1 First-pass stuttering recovery model.** Run after FluencyBank access/download confirms usable recovery labels.
- [ ] **4.2 Stuttering feature ablation.**
- [ ] **4.3 Stuttering robustness audit.**
- [ ] **8.2 Future update gatekeeping.**
- [ ] **8.3 Franklin-specific technical note if needed.**

## Blocked

- [ ] Manchester Language Study modeling: requires registered access and data download.
- [ ] True treatment-response prediction: requires treatment type, dose, goals, repeated samples, and outcomes.
- [ ] BA Web API integration: requires clarity from Brian/Franklin on service access and expected upload path.
- [ ] **6.5 BA Web integration after workflow review.** Requires API/upload contract from Brian/Franklin.
- [ ] **5.3 Informal SLP review.** Protocol and packet are ready; requires actual SLP reviewer responses.
- [ ] Full AphasiaBank openSMILE streaming extraction: now technically feasible, but a full all-corpus run is multi-hour; use balanced patient-root chunks before launching all sessions.
- [ ] Dryad EMT-SF DLD data download: CLI download is blocked by Dryad/AWS WAF; manual browser download should place files in `data/external/dryad_emt_sf_dld/`.
- [ ] Prospective clinical collection: requires consent/IRB path and partner workflow.
- [ ] Stuttering recovery modeling: local checkout lacks FluencyBank child longitudinal recovery data; requires separate FluencyBank access/download.
- [ ] Full natural-plus-tight-task battery: local headers show no sentence-repetition or nonword-repetition candidates.

## Done

- [x] **0.1 Project charter.** Created `docs/project_charter.md`.
- [x] **0.2 Publishable claims.** Defined in `docs/project_charter.md`.
- [x] **0.3 Local task board.** Created this `TASKS.md`.
- [x] **1.1 Minimum language-state battery.** Created `docs/minimum_language_state_battery.md`.
- [x] **1.2 Adult/child/stuttering variants.** Included in `docs/minimum_language_state_battery.md`.
- [x] **1.3 State dimensions.** Included in `docs/minimum_language_state_battery.md`.
- [x] **1.4 SLP-facing output requirements.** Included in `docs/minimum_language_state_battery.md`.
- [x] **2.1 Structured-task inventory.** Created `outputs/structured_task_inventory/summary.md`.
- [x] **2.2 Stuttering recovery inventory.** Created `outputs/stuttering_recovery_inventory/summary.md`; local recovery modeling is blocked pending FluencyBank access.
- [x] **2.3 DLD/late-talker longitudinal inventory.** Created `outputs/dld_longitudinal_inventory/summary.md`; local data have repeated samples but no explicit outcome/literacy/school columns.
- [x] **2.4 Treatment-response evidence inventory.** Created `outputs/treatment_response_inventory/summary.md`; identified Dryad EMT-SF DLD as the first public treatment-response pilot and FluencyBank as the first recovery-prediction target.
- [x] **2.5 BA Web/Batchalign/CLAN/KidEval infrastructure inventory.** Created `docs/ba_web_integration_notes.md`; API details remain a Brian/Franklin question.
- [x] **3.1 Standard acoustic extraction path.** Added openSMILE scripts and smoke outputs: `scripts/extract_opensmile_features.py`, `scripts/extract_aphasia_opensmile.py`, `outputs/opensmile_smoke/summary.md`, and `outputs/opensmile_aphasia_smoke/summary.md`.
- [x] **4.7 openSMILE/eGeMAPS aphasia pilot.** Refreshed TalkBank media auth works; created `data/features/aphasia_opensmile_egemaps_balanced48.parquet` and `outputs/aphasia_standard_acoustic_replication/balanced48_model_summary.md`.
- [x] **4.7 openSMILE/eGeMAPS aphasia replication expansion.** Created `data/features/aphasia_opensmile_egemaps_balanced84.parquet`, `outputs/aphasia_standard_acoustic_replication/balanced84_model_summary.md`, and `outputs/aphasia_standard_acoustic_replication/summary.md`; standard eGeMAPS adds modest signal but does not support a broad subtype-classifier claim.
- [x] **4.7b Custom-vs-standard acoustic audit.** Created `scripts/run_acoustic_feature_set_comparison.py` and `outputs/aphasia_standard_acoustic_replication/feature_set_comparison_summary.md`; custom acoustic features add only a modest increment over WAB after backfilling missing roots.
- [x] **4.8 Same-score different-state demonstration.** Created `scripts/run_same_score_different_state_demo.py` and `outputs/same_score_different_state_demo/summary.md`; found 11,398 same-subtype pairs within WAB-AQ diff <= 2 with substantial state-plan contrasts.
- [x] **4.9 Stable-score mover replication.** Updated `scripts/run_stable_wab_mover_analysis.py` and `outputs/stable_wab_movers/summary.md`; found 66 stable-WAB discourse movers, 17 stable-WAB acoustic movers among 110 stable pairs with acoustic coverage, and 11 acoustic-only falsification candidates.
- [x] **4.10 Acoustic mechanism audit.** Created `scripts/run_acoustic_mover_artifact_audit.py` and `outputs/acoustic_mover_artifact_audit/summary.md`; 6 acoustic-only stable-WAB cases look like likely voice/pitch state changes, 3 like possible recording/sample artifacts, and 2 like quantity/transcription shifts.
- [x] **4.4 DLD label-noise sensitivity.** Created `scripts/run_dld_label_noise_sensitivity.py` and `outputs/dld_label_noise_sensitivity/summary.md`; full-language DLD signal remains under moderate simulated label noise, but 82 participants show high-confidence label/corpus/state conflicts that require corpus-level review.
- [x] **4.5 DLD structured-task plus natural-speech experiment.** Created `scripts/run_dld_task_context_comparison.py` and `outputs/dld_task_context_comparison/summary.md`; within-context DLD signal is strong, but cross-context transfer is weaker, supporting a prospective battery that pairs natural speech with structured tasks.
- [x] **4.6 Late-talker and DLD persistent-risk rerun.** Created `scripts/run_dld_late_talker_persistence_sensitivity.py` and `outputs/dld_late_talker_persistence_sensitivity/summary.md`; earliest state alone is weak, but 36-to-48-month movement predicts later TD-band/persistent-gap status better in Rescorla.
- [x] **3.2 CAF-plus-content feature map.** Created `docs/state_feature_schema.md`.
- [x] **3.3 Data-quality gates.** Created `scripts/run_data_quality_gates.py` and `outputs/data_quality_gates/summary.md`; current required failure is duplicated AphasiaBank `window_id`s, which strict experiments must drop.
- [x] **5.1 SLP state report v2.** Created `docs/slp_state_report_v2_spec.md`, `scripts/run_slp_state_report_v2.py`, and `outputs/slp_state_report_v2/summary.md`.
- [x] **5.2 Create adult aphasia, child-language, and stuttering report sets.** Created `scripts/create_slp_report_packets.py` and `outputs/slp_report_packets/`; adult aphasia uses real V2 report rows, child/DLD separates trajectories from target/probe profiles, and stuttering remains a data-access wireframe.
- [x] **6.1 BA Web recorder workflow spec.** Created `docs/ba_web_recorder_workflow_spec.md`.
- [x] **6.2 Recording protocol scripts.** Created `docs/recording_protocols.md`.
- [x] **6.3 Privacy and consent packet.** Created `docs/privacy_irb_plan.md`.
- [x] **6.4 Local-only recorder prototype.** Created `scripts/create_recording_package.py` and demo summary `outputs/recorder_package_demo/summary.md`; raw package media stay under gitignored `data/`.
- [x] **7.1 Partner profile list.** Created `docs/partner_profile_list.md`.
- [x] **7.2 Independent IRB feasibility.** Created `docs/independent_irb_options.md`; independent IRB is feasible but should wait until a concrete prospective protocol and partner path are clearer.
- [x] **7.3 Prospective pilot design.** Created `docs/prospective_pilot_design.md`; recommended order is SLP report usability, non-sensitive recorder feasibility, then one partner-based longitudinal pilot.
- [x] **7.4 Funding path memo.** Created `docs/funding_path_memo.md`; recommended route is partner-led science first, then SBIR/STTR product translation only after the recorder/report workflow has stronger evidence.
- [x] **8.1 Post-call thank-you and GitHub link.** Drafted in `docs/brian_research_update.md`; send after the pushed GitHub branch is available.

## Deprioritized

- [ ] Full mobile/cloud app before BA Web workflow and privacy plan.
- [ ] Direct DLD diagnostic classifier as the main product.
- [ ] EHR extraction as a near-term data source.
- [ ] LLM reconstruction as an assessment source of truth.
- [ ] New model architectures before data/task/measurement questions are settled.
