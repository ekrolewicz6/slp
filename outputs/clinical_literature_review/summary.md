# Clinical Literature Review: Decision Memo

## Bottom Line

The literature pushes this project away from broad diagnostic model-chasing and toward a more clinically useful measurement science:

> Build a reliable, multidimensional language-state model from natural speech, structured tasks, audio, and longitudinal change; then test whether movement in that state predicts recovery or treatment response better than baseline labels and global scores.

The most important operational update is that Brian's access change worked: the current TalkBank cookie now downloads all 1,999 FluencyBank `.cha` transcripts in the TalkBankDB export, including 1,154 formerly password-gated transcripts from IISRP, IISRP-new, Wagovich, Ratner, Maxfield, Tellis, and Sawyer. This makes stuttering recovery the best immediate longitudinal replication target.

## Five Core Lessons

1. Measurement must come before treatment optimization.
   CATALISE, SCALES, WAB, and discourse-assessment papers all point to the same problem: clinical labels and global scores are useful but heterogeneous. A direct DLD classifier or subtype classifier is not enough.

2. Natural speech should be paired with tight tasks.
   Brian's advice matches the literature. Sentence repetition, nonword repetition, phonological probes, fluency tasks, and structured discourse prompts can expose mechanisms that open conversation misses.

3. Longitudinal movement matters more than earliest severity.
   Late-talker, stuttering recovery, and aphasia change work all converge on the same scientific question: does within-person movement predict later recovery or treatment response better than the first observed score?

4. Treatment-response requires target, dose, fidelity, and repeated probes.
   Dryad EMT-SF gives randomized aggregate treatment data, but not raw transcript/audio or target/dose detail. Calder-style single-case grammar probes are closer to the target-level modeling needed for therapy decisions.

5. The clinical AI bar is prospective treatment assignment.
   Kiran et al. (2026) is the benchmark: a double-blind randomized test of computationally selected treatment language. Retrospective prediction is preclinical evidence, not a final clinical claim.

## What This Changes Now

The next experiment should not be another aphasia text embedding or a direct DLD-vs-TD classifier. The highest-learning order is:

1. **Full FluencyBank transcript recovery model.**
   Use Purdue, IISRP, IISRP-new, Wagovich, Ratner, Tellis, Maxfield, Sawyer, UMD-CMU, and other local corpora where labels permit. Model weighted stuttering-like disfluency, longitudinal change, task type, language-growth features, and corpus-held-out validation. Probe media access separately before adding acoustics.

2. **Fiveash sentence-repetition structured-task pilot.**
   Test DLD-vs-TD separation, age/reading covariates, and regular-vs-irregular rhythm effects. This directly tests whether tight tasks reveal modifiable state.

3. **Calder repeated-probe treatment-response pilot.**
   Fit response curves for trained, untrained, extension, and control grammar targets. This is a better therapy-target sandbox than a broad standardized outcome alone.

4. **SCALES access packet.**
   SCALES is the strongest non-TalkBank DLD access target because it links structured probes to repeated language, literacy, cognition, speech/hearing, mental-health, parent/teacher, and educational outcomes.

5. **Aphasia GenAI safety and digital-twin benchmark.**
   Treat Adikari et al. (2025) as a useful assistive-reconstruction result, but preserve the measurement firewall. Use Kiran et al. (2026) as the bar for eventual treatment-personalization claims.

## What To Avoid

- Do not make a broad "DLD classifier" the central scientific claim.
- Do not score ASR or LLM-reconstructed text as if the patient independently produced it.
- Do not collapse treatment response into one global WAB-AQ or broad language score.
- Do not assume natural speech alone is a complete measurement battery.
- Do not infer treatment effects from natural recovery data.

## Most Nature-Worthy Hypothesis Now

The strongest hypothesis is cross-disorder:

> Across child language delay/DLD, stuttering, and aphasia, early within-person movement across natural speech plus structured tasks predicts long-term recovery or treatment response better than baseline diagnostic labels and global severity scores.

That is immediately testable in stuttering with the newly unlocked FluencyBank transcripts, partially testable in DLD with Dryad/Fiveash/Calder, and aligned with aphasia discourse/digital-twin work. The decisive missing data are paired natural-speech plus structured-task longitudinal samples with target, dose, and outcome metadata.

## Files

- Literature matrix: `outputs/clinical_literature_review/paper_matrix.md`
- FluencyBank access inventory: `outputs/fluencybank_download_inventory/summary.md`
- Literature/data access scan: `outputs/data_access_scan/summary.md`
