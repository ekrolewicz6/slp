# Cross-Disorder Language-State Generalization Plan

## Purpose

The broader project should not stop at aphasia or DLD. The real scientific claim is cross-lifespan and cross-disorder:

> Language and communication difficulties can be represented as state dimensions that cut across development, acquired injury, neurodegeneration, fluency, voice, and motor speech conditions, while preserving disorder-specific mechanisms.

## Candidate Disorders And Data Needs

| Domain | Likely Public/Requestable Source | State Axes To Test |
| --- | --- | --- |
| Aphasia | AphasiaBank | content, recoverability, acoustic/prosody, WAB/subtype, longitudinal change |
| DLD / SLI / late talkers | CHILDES Clinical-Eng, Manchester Language Study | developmental residuals, narrative state, literacy risk, catch-up |
| Dementia | DementiaBank | semantic content, discourse coherence, lexical retrieval, longitudinal decline |
| TBI | TBIBank / TalkBank-style resources if approved | discourse organization, attention/executive coherence, informativeness |
| Right hemisphere disorder | RHDBank if approved | pragmatics, coherence, inference, discourse organization |
| Fluency disorders | FluencyBank | timing, repetitions, blocks, avoidance, communication participation |
| Dysarthria / motor speech | public dysarthric speech datasets where licensed | intelligibility, acoustic timing, voice quality, ASR uncertainty |
| Voice disorders | voice corpora with clinical labels | pitch, intensity, perturbation, voice quality, participation |

## Core Cross-Disorder Experiments

1. Shared-axis test
   - Fit a common state space over safe structural/acoustic features.
   - Test whether content, output, fluency, acoustic quality, and repairability axes recur.

2. Disorder-specific residual test
   - Remove shared severity/output axes.
   - Ask what remains uniquely predictive of each disorder.

3. Same-score/different-mechanism test
   - Find pairs with similar broad severity but different state profiles.
   - Test whether state profiles imply different functional risks.

4. ASR safety generalization
   - Test whether ASR/LLM reconstruction corrupts measurement similarly across aphasia, dysarthria, fluency, and dementia.

5. Cross-disorder target policy simulation
   - Compare weakest-target, near-threshold, and function-first policies across disorders.

## Required Controls

- corpus-held-out evaluation
- participant-held-out evaluation
- task-held-out evaluation
- age and demographic balancing
- shuffled-label controls
- random-feature controls
- disorder-vs-corpus artifact classifiers

## Scientific Payoff

A strong result would show that SLP conditions are not isolated silos. They may share measurement primitives such as content carried, intent clarity, output capacity, fluency/timing, acoustic quality, and repairability, while still requiring disorder-specific interpretation.

That would move the project from an aphasia/DLD model to a general measurement science for SLP.

