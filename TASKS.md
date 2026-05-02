# Language-State Modeling Task Board

**Last updated:** 2026-05-01
**Source plan:** `docs/post_brian_ordered_task_list.md`

This is the working board. The detailed rationale lives in the ordered plan; this file is for execution.

## Doing

None.

## Next

None.

## Backlog

- [ ] **8.2 Future update gatekeeping.**
- [ ] **8.3 Franklin-specific technical note if needed.**

## Blocked

- [ ] Manchester Language Study modeling: requires registered access and data download.
- [ ] True treatment-response prediction: requires treatment type, dose, goals, repeated samples, and outcomes.
- [ ] BA Web API integration: requires clarity from Brian/Franklin on service access and expected upload path.
- [ ] **6.5 BA Web integration after workflow review.** Requires API/upload contract from Brian/Franklin.
- [ ] **5.3 Informal SLP review.** Protocol and packet are ready; requires actual SLP reviewer responses.
- [ ] Full AphasiaBank openSMILE streaming extraction: now technically feasible, but a full all-corpus run is multi-hour; use balanced patient-root chunks before launching all sessions.
- [ ] EMT-SF raw language samples/audio/session targets/dose: the public Dryad package is local, but raw samples and session-level treatment details are not public.
- [ ] Prospective clinical collection: requires consent/IRB path and partner workflow.
- [ ] Full stuttering acoustic/media replication: transcript access now works for all 1,999 FluencyBank `.cha` files in the TalkBankDB export; media access and quality still need probing before acoustic recovery modeling.
- [ ] Full natural-plus-tight-task battery: Fiveash OSF sentence-repetition data are local, but paired natural speech plus structured tasks still require SCALES/Manchester/TalkBank access or prospective collection.
- [ ] SCALES participant-level modeling: requires UK Data Service safeguarded/restricted access.

## Done

- [x] **0.1 Project charter.** Created `docs/project_charter.md`.
- [x] **0.2 Publishable claims.** Defined in `docs/project_charter.md`.
- [x] **0.3 Local task board.** Created this `TASKS.md`.
- [x] **1.1 Minimum language-state battery.** Created `docs/minimum_language_state_battery.md`.
- [x] **1.2 Adult/child/stuttering variants.** Included in `docs/minimum_language_state_battery.md`.
- [x] **1.3 State dimensions.** Included in `docs/minimum_language_state_battery.md`.
- [x] **1.4 SLP-facing output requirements.** Included in `docs/minimum_language_state_battery.md`.
- [x] **2.1 Structured-task inventory.** Created `outputs/structured_task_inventory/summary.md`.
- [x] **2.2 Stuttering recovery inventory.** Created `outputs/stuttering_recovery_inventory/summary.md`; later transcript access is now unblocked by task 13.3.
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
- [x] **9.1 Acoustic mover media-quality audit.** Created `scripts/run_acoustic_mover_media_quality_audit.py` and `outputs/acoustic_mover_media_quality_audit/summary.md`; all 11 acoustic-only stable-WAB pairs show medium/high recording-artifact risk on the leading-clip technical screen, so acoustic-only claims need task-aligned manual audio review before being treated as evidence.
- [x] **9.2 DLD high-conflict taxonomy.** Created `scripts/run_dld_conflict_taxonomy.py` and `outputs/dld_conflict_taxonomy/summary.md`; the 82 high-confidence conflicts split into label-history/resolved-state cases, corpus-age deconfounding warnings, 12 highest-scientific-review language-risk cases, and 3 highest-clinical-fairness review cases.
- [x] **9.3 Late-talker trajectory typology.** Created `scripts/run_late_talker_trajectory_typology.py` and `outputs/late_talker_trajectory_typology/summary.md`; strong 36-to-48-month gains predict higher final TD-band rates and lower persistent-gap rates in Rescorla, while earliest severity remains weak.
- [x] **9.4 Current discovery scorecard.** Created `docs/current_discovery_scorecard.md`; the current top discovery thread is early movement/state disagreement rather than standalone diagnosis or acoustic subtype classification.
- [x] **10.1 Utterance-aligned acoustic mover quality audit.** Created `scripts/run_acoustic_mover_utterance_aligned_quality_audit.py` and `outputs/acoustic_mover_utterance_quality_audit/summary.md`; task-aligned PAR spans still flag most acoustic-only stable-WAB pairs as medium/high technical risk, leaving one low-risk voice/pitch candidate for manual clinical audio review.
- [x] **10.2 Late-talker leave-one-out robustness audit.** Created `scripts/run_late_talker_leave_one_out_robustness.py` and `outputs/late_talker_leave_one_out_robustness/summary.md`; the 0.75 z early-movement result keeps the same direction after every one-child deletion, but persistent-gap significance is not deletion-proof.
- [x] **10.3 DLD conflict review packet.** Created `scripts/create_dld_conflict_review_packet.py`, `outputs/dld_conflict_review_packet/summary.md`, and `outputs/dld_conflict_review_packet/review_packet.md`; packaged the 15 highest-value DLD/TD conflict cases for expert review and future structured-probe design.
- [x] **11.1 DLD conflict mechanism audit.** Created `scripts/run_dld_conflict_mechanism_audit.py` and `outputs/dld_conflict_mechanism_audit/summary.md`; the 15 review cases split into sample-constrained, possible hidden TD risk, non-MLU language-state, language-not-corpus-prior, and low-output/MLU-aligned mechanisms.
- [x] **11.2 Late-talker bootstrap/permutation audit.** Created `scripts/run_late_talker_bootstrap_permutation_audit.py` and `outputs/late_talker_bootstrap_permutation/summary.md`; the 0.75 z early-movement effect has positive bootstrap CIs and permutation support for final TD-band lift and persistent-gap reduction.
- [x] **12.1 Dryad EMT-SF data inventory.** Extracted the public Dryad EMT-SF dataset into gitignored `data/external/dryad_emt_sf_dld/` and audited structure/missingness in `outputs/dryad_emt_sf_treatment_pilot/summary.md`.
- [x] **12.2 Dryad EMT-SF treatment effect replication.** Added transparent Python treatment contrasts in `scripts/run_dryad_emt_sf_treatment_pilot.py`; grammar effects are clearer than short-term vocabulary effects.
- [x] **12.3 Dryad EMT-SF heterogeneous response pilot.** Added baseline moderator screening with BH and max-T checks; no robust moderator survived correction in the shared dataset.
- [x] **12.4 Dryad early-movement outcome pilot.** Created `scripts/run_dryad_early_movement_response_pilot.py` and `outputs/dryad_early_movement_response/summary.md`; early language-sample movement predicts later grammar/vocabulary outcomes beyond baseline state and treatment group, but treatment assignment only weakly moves the aggregate early state.
- [x] **13.1 FluencyBank public download inventory.** Used the local TalkBankDB transcript export to download all non-password FluencyBank corpora with the current TalkBank cookie; 845 local `.cha` transcripts are now under gitignored `data/raw/fluencybank/`.
- [x] **4.1 First-pass stuttering recovery model.** Created `scripts/run_fluencybank_purdue_recovery_pilot.py` and `outputs/fluencybank_purdue_recovery_pilot/summary.md`; Purdue strict Rec/Per labels are usable, but earliest-transcript prediction is modest rather than publishable on its own.
- [x] **13.2 Data access and literature scan.** Downloaded open papers/docs/supplements into gitignored `data/external/literature/` and committed `outputs/data_access_scan/summary.md`; SCALES and Manchester participant-level data are UKDS gated, FluencyBank recovery corpora remain consortium/password gated, and Fiveash/Calder are now immediate local analysis targets.
- [x] **13.3 Full FluencyBank transcript access.** Confirmed Brian's access change worked and reran `scripts/download_fluencybank_transcripts.py --only-password`; all 1,999 FluencyBank `.cha` transcripts in the TalkBankDB export are now local, including 1,154 formerly password-gated transcript files.
- [x] **13.4 Clinical literature review matrix.** Created `outputs/clinical_literature_review/summary.md` and `outputs/clinical_literature_review/paper_matrix.md`; the papers push the next work toward longitudinal state movement, natural-plus-structured tasks, and treatment-response datasets rather than broad diagnostic classifiers.
- [x] **4.2a Full FluencyBank inventory/label audit.** Created `outputs/fluencybank_full_recovery_model/summary.md`; parsed 1,922 of 1,999 local `.cha` files and found 253 recovery-labelled CWS participants with usable transcript features.
- [x] **4.2b Full FluencyBank transcript feature extraction.** Created row-level gitignored session/participant feature tables under `data/parsed/fluencybank/` and aggregate corpus/endpoint inventories under `outputs/fluencybank_full_recovery_model/`.
- [x] **4.2c Early-movement recovery test.** Compared earliest-session state with early movement among 152 multi-session labelled participants; early movement did not improve AUC in the first transcript-only test.
- [x] **4.3 Stuttering robustness audit.** Added bootstrap CIs, shuffled-label controls, and leave-corpus-out checks in `outputs/fluencybank_full_recovery_model/`; first-language features were strongest, while movement-only was below chance.
- [x] **4.3b FluencyBank media access probe.** Created `scripts/probe_fluencybank_media_access.py` and `outputs/fluencybank_media_access_probe/summary.md`; 12 of 17 sampled corpora have accessible media, but IISRP/IISRP-new/Wagovich and Purdue are not streamable in the current environment.
- [x] **14.1 Fiveash sentence-repetition structured-task pilot.** Created `scripts/run_fiveash_sentence_repetition_pilot.py` and `outputs/fiveash_sentence_repetition_pilot/summary.md`; sentence-repetition level strongly separates DLD from TD in leave-one-child-out testing, while rhythm response alone is much weaker and not clearly DLD-specific.
- [x] **14.2 Calder repeated-probe treatment-response pilot.** Created `scripts/run_calder_repeated_probe_pilot.py` and `outputs/calder_repeated_probe_pilot/summary.md`; PDF supplemental probe tables were parsed into gitignored row-level data and aggregate response metrics showing strong target-specific expressive maintenance gains for untrained past tense.
- [x] **14.3 SCALES access packet and analysis plan.** Created `scripts/build_scales_access_packet.py`, `docs/scales_access_packet.md`, and `outputs/scales_access_packet/summary.md`; defined the minimum variable request and first six analyses for SCALES Study 8968 after UKDS safeguarded/restricted access.
- [x] Documentation and push prep for tasks 4.2a-4.3b and 14.1-14.3.

## Deprioritized

- [ ] Full mobile/cloud app before BA Web workflow and privacy plan.
- [ ] Direct DLD diagnostic classifier as the main product.
- [ ] EHR extraction as a near-term data source.
- [ ] LLM reconstruction as an assessment source of truth.
- [ ] New model architectures before data/task/measurement questions are settled.
