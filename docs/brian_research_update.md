# Follow-Up for Brian: Language-State Modeling, CHILDES/KidEval, and Treatment-Response Prediction

**Status:** Updated after the 2026-04-29 discussion with Brian MacWhinney and the follow-up local experiment batch. Post-call takeaways are in `docs/brian_meeting_2026-04-29.md`; the execution queue is in `TASKS.md` and `docs/post_brian_ordered_task_list.md`.

## Post-Call GitHub Update Draft

Subject: Post-call update: language-state measurement repo and next steps

Hi Brian,

Thank you again for taking the time to talk with us. I wanted to send a concise follow-up with the public repo and the current direction, without creating work for you.

Repo: https://github.com/ekrolewicz6/slp

The call transcript is staying private/local and is not in the repository. The repo contains the research log, code, aggregate summaries, and planning documents.

Your feedback changed the project in an important way. I am now treating this first as a measurement and recovery-prediction project, not as a treatment-recommendation product. The operating thesis is that SLP needs a reliable multidimensional language-state layer before it can make credible treatment-response claims.

Since the call, I ran the highest-value local checks that seemed possible with the data already available:

- Verified TalkBank media streaming with the local cookie and added a reusable auth helper for media access.
- Replicated the aphasia acoustic result with standard openSMILE/eGeMAPS features on balanced AphasiaBank roots.
- Found that eGeMAPS features do carry signal above random/shuffled controls, but WAB severity still outperforms eGeMAPS for broad 4-way subtype classification. This downgrades the acoustic story from "audio can classify subtype" to the more cautious "audio may add mechanism/state information."
- Compared standard eGeMAPS against the earlier custom Praat-style acoustic features. The custom features add only a modest increment after backfilling missing roots, so the earlier stronger result was partly sample-sensitive.
- Re-ran the stable-WAB mover analysis. A nontrivial subset of sessions show discourse or acoustic state movement despite stable WAB-AQ, which is now a good falsification set rather than a finished claim.
- Audited DLD/SLI models as noisy-label problems. The signal is real enough to study, but corpus/task/label uncertainty is too strong for a diagnostic claim.
- Tested task-context transfer in child language/DLD samples. Narrative and natural speech both contain signal, but cross-task transfer is weak, supporting your point that natural speech should be paired with tighter tasks.
- Revisited Rescorla late talkers. The earliest sample alone is weak, but early movement from roughly 36 to 48 months predicts later persistent-gap status better than static first-sample state.

The most useful next external inputs, if they are easy to point toward, would be:

1. Whether the Rescorla "early movement beats first sample" finding is already well known or worth pursuing.
2. Whether TalkBank has accessible sentence-repetition or nonword-repetition data that can be paired with natural speech.
3. Whether there is a preferred access path for FluencyBank recovery/persistence data.
4. Whether the BA Web recorder workflow spec is worth showing to Franklin at some point, or whether it should wait until Batchalign 3 is further along.

No need to dig into any of that unless something obvious comes to mind. For now I am keeping the work local, conservative, and focused on measurement validity.

Best,
Edan

---

The original pre-call note is preserved below for continuity.

Subject: Follow-up before Wednesday: alpha results, current direction, and questions for your guidance

Hi Brian,

Ahead of our Wednesday call, I wanted to send a concise update on what I have been building and, more importantly, ask for your guidance on whether I am aiming at the right problems.

Your earlier feedback was clarifying:

- Start with English.
- KidEval is a good starting point, but existing measures should not be treated as unquestioned ground truth.
- Spoken-language corpora have real quality problems, especially with young children, noisy recording conditions, and complex interaction formats.
- The missing link is not assessment alone, but guidance toward a therapy plan.
- Treatment-response data, especially in child language delay/DLD, are far thinner and less transcript-linked than one would want.
- Sagae's ML work and the problems with IPSyn suggest the field may be ready to move beyond hand-coded structural measures.
- Nan Bernstein Ratner's critique of SALT/SUGAR-style tools as identifying problems without guiding treatment points directly at the gap this project is trying to address.

The original vision still stands:

> Build a computational layer that connects a person's language profile to likely developmental or recovery trajectories, and eventually to better treatment planning.

The work so far has become an alpha version of the measurement/discovery layer underneath that vision. It does not yet solve treatment-response prediction, because the shared treatment-linked data appear too sparse. But it has helped clarify what the first publishable and clinically meaningful step might be.

## High-Level Summary

### The goal

The long-term goal is to move SLP from static language-sample description toward dynamic treatment planning:

1. run a speech/language sample through a reliable analysis pipeline,
2. infer the person's current language state,
3. compare that state to developmentally or clinically relevant trajectories,
4. estimate what is likely to change under different supports or treatment conditions,
5. update the model as new samples arrive.

In the first email, I framed this around CHILDES/KidEval and DLD treatment-response modeling. That remains the highest-impact clinical vision, especially for children. The aphasia work I have done since then should be understood as a parallel validation track: AphasiaBank has richer clinical metadata and recovery structure, so it lets us test the same language-state idea faster.

### The current thesis

The main thing we are learning is that broad labels and broad scores compress multiple separable dimensions of communication.

In child language, a single measure such as MLU or a diagnostic label such as DLD/SLI does not fully describe the child's language state.

In aphasia, a broad score like WAB-AQ or a subtype label does not fully describe what is breaking down in discourse.

Across both domains, the same pattern keeps appearing:

> "Low language output" is not one thing. Similar surface scores can reflect different underlying states, different risks, and likely different treatment needs.

That seems directly related to the treatment-planning gap. If current tools identify that a person has a problem but do not tell the clinician what kind of state produced the problem, they will struggle to guide therapy.

### What we have found so far

The strongest findings are exploratory, but coherent:

- KidEval-style and related language-sample features do contain meaningful developmental and clinical signal.
- Existing surface measures like MLU are useful but not sufficient.
- DLD/SLI, late-talker delay, and Broca aphasia can all involve low output, but they are clearly not the same language state.
- Broca aphasia appears to be low-output but not child-like, which argues against a simple "aphasia as developmental regression" analogy.
- Aphasia discourse features sometimes move even when broad WAB-AQ scores are stable.
- Acoustic/prosodic features add information beyond transcript text, especially for aphasia subtype and fluent aphasia distinctions.
- AI/ASR reconstruction can make impaired speech look cleaner than it was, so it should not replace the raw sample for measurement.

The most important negative result is also useful:

- Current public child-language/DLD data are not yet enough to build a reliable clinical screener or treatment-response predictor without stronger deconfounding, better outcome labels, and better demographic/task metadata.

### What this means

The project is not ready to claim a clinical tool.

But I think it is ready to make a more focused research claim:

> A useful next-generation SLP measurement system should model language as a multidimensional state, not only as a score, label, or list of deficits.

That state model could then become the foundation for treatment-response prediction once the right longitudinal and intervention-linked data are available.

## Where This Fits With the Original CHILDES/KidEval Vision

My original proposal was:

1. run KidEval across eligible English CHILDES corpora,
2. build a properly characterized developmental landscape,
3. extract DLD treatment studies into a structured database,
4. align baseline profiles, treatment parameters, and outcome trajectories,
5. fit hierarchical models that predict treatment response with uncertainty.

After working through the data, I would now slightly revise the plan.

### Revised plan

1. Use KidEval and related CLAN-computable features as the starting measurement layer, but do not treat them as final truth.
2. Build a corpus-quality and task-quality audit first, because data quality can easily dominate developmental signal.
3. Separate three problems that are often collapsed:
   - developmental norming,
   - disorder/risk identification,
   - treatment-response prediction.
4. Use DLD/child-language work for the highest-impact long-term goal.
5. Use aphasia as a faster validation environment for the general language-state framework because AphasiaBank has richer clinical labels, severity scores, and longitudinal structure.
6. Treat treatment-response prediction as the eventual target, but first build a robust state space that clinicians agree is meaningful.

The key shift is that I would not immediately jump from KidEval features to treatment-response modeling unless we can get stronger outcome-linked data. I would first establish that the language-state representation is reliable, clinically interpretable, and not mostly an artifact of corpus, task, age, or transcription quality.

## What We Have Done in More Detail

### 1. Child language and DLD experiments

We used CHILDES-derived language features to test whether DLD/SLI-like samples differ from typically developing samples beyond age and MLU.

The first-pass models found a strong signal, but further checks showed serious confounding by corpus and task. That is not surprising, given your warning that spoken-language corpora have data-quality issues, but it is important. It means the easy win would be misleading.

Current interpretation:

- There is likely real DLD/SLI signal in the available language features.
- MLU and age alone do not explain everything.
- But corpus/task artifacts are strong enough that current public-data models should not be treated as diagnostic screeners.
- The right next step is careful corpus/task deconfounding, not bigger models.

This makes me think the first CHILDES/KidEval contribution should be an honest developmental landscape with uncertainty and data-quality annotations, rather than a model that pretends the data are cleaner than they are.

### 2. Late talker trajectory experiments

We looked at late-talker longitudinal samples where possible.

Many late talkers moved toward typical-development ranges over time, while a meaningful subset appeared to retain persistent gaps. However, early transcript features did not robustly predict final typical-development-band status in the current data.

Current interpretation:

- Predicting persistence versus catch-up is exactly the kind of question that could matter clinically.
- Current transcript-only data may be too small or missing key predictors.
- Environmental variables, intervention history, family history, hearing status, SES, bilingualism, and broader developmental measures may be necessary.

This seems highly aligned with the original goal, but it probably requires better longitudinal datasets than what is immediately available in public CHILDES alone.

### 3. Cross-lifespan state experiments

We compared DLD/SLI, late talkers, typically developing children, aphasia samples, and controls in shared feature spaces.

The key conceptual finding is that low output does not imply the same language state.

DLD/SLI, late talker delay, and Broca aphasia can overlap on surface measures such as MLU, but they remain separable using richer language-state features. This is a useful guardrail: if a measurement system collapses these cases into one "simple language" axis, it is probably not measuring the clinically important structure.

### 4. Aphasia experiments as a validation track

We used AphasiaBank because it provides a richer adult clinical testbed for the same ideas:

- transcript data,
- streamed audio,
- subtype labels,
- WAB scores and subtests,
- repeated sessions for some participants,
- structured discourse tasks.

The strongest aphasia result is:

> Broca aphasia appears low-output but not child-like.

That result is interesting because it challenges an overly simple analogy between aphasia and early child language. The adult system is damaged, not developmentally early.

We also found evidence that:

- acoustic/prosodic features add clinically meaningful signal,
- WAB-AQ is useful but too coarse to describe all discourse-state differences,
- some discourse dimensions may change even when WAB-AQ is stable,
- content-state and task-conditioned informativeness may matter more than syntactic richness alone.

I see this as supporting the same broader measurement claim that motivated the CHILDES work: broad scores are not enough to guide treatment.

### 5. AI/ASR safety experiments

We also tested how AI-style reconstruction or ASR cleanup might interact with clinical measurement.

The concern is that modern systems can silently normalize a patient's impaired language. That may be helpful for communication access, but dangerous for assessment.

Current safety principle:

> Raw transcript/audio must remain the measurement source of truth. AI reconstruction can be a support layer, but should not become the clinical scoring layer.

This seems important because generative AI is advancing quickly. The smarter the model gets, the more likely it is to fill gaps and hide the original signal unless the system is designed carefully.

## What Seems Most Scientifically Interesting Now

### 1. Same score, different state

This is the cleanest organizing hypothesis.

Two children may have the same MLU but different developmental risks.

Two adults with aphasia may have the same WAB-AQ but different discourse breakdowns.

Two patients may produce the same number of words but differ in whether their intended message is recoverable.

The clinical question is not just "how low is the score?" It is "what kind of state produced this score, and what should we do next?"

### 2. State change before score change

Broad standardized scores may move slowly or be too coarse. Discourse-state dimensions may move earlier.

If this is true, SLPs could detect meaningful change sooner and adjust treatment earlier.

The aphasia data give us a place to test this idea now. Child-language/DLD data would be the higher-impact domain if we can access the right longitudinal outcome datasets.

### 3. Repairability and treatment targeting

Some errors may be more useful targets than others.

For example:

- a near-miss where the intended word/concept is recoverable,
- a missing concept that is central to the task,
- a repeated structural gap,
- an acoustic/prosodic disruption that affects intelligibility,
- a functional communication target that matters to the person.

The hypothesis is that treatment should target not only deficits, but high-value, near-threshold, repairable breakdowns.

This is speculative, but it is exactly the kind of idea that could connect measurement to therapy planning.

### 4. Measurement before optimization

The original vision was treatment optimization. I still believe that is the right long-term goal.

But the work so far suggests the first scientific step is measurement:

- Can we define a reliable language-state space?
- Does it generalize across corpora and tasks?
- Does it match clinician judgment?
- Does it predict future change better than broad scores alone?
- Does it identify treatment-relevant differences between people who look similar under current measures?

If the answer is yes, then treatment-response modeling becomes much more realistic.

## Questions I Would Love Your Guidance On

### 1. Is the revised framing right?

Does it make sense to frame the project as:

> first build a reliable multidimensional language-state measurement layer, then use it for treatment-response prediction once outcome-linked data are available?

Or should I stay more directly focused on the original KidEval-to-treatment-response pipeline, even if the intervention data are sparse?

### 2. Where should the first proof of concept live?

Which domain is the best first target?

- English CHILDES developmental landscape,
- DLD/SLI and late-talker risk,
- AphasiaBank recovery/discourse state,
- aphasia treatment response,
- another TalkBank clinical population,
- a cross-database measurement framework.

My instinct is:

- CHILDES/DLD is the highest-impact long-term clinical area,
- AphasiaBank is the most practical near-term validation environment,
- the shared contribution is the language-state measurement framework.

I would value your pushback if that division is wrong.

### 3. Which English CHILDES corpora should be in the first serious pass?

You mentioned that the easiest format is one child, one adult, all in one room, and that noisy corpora such as Hall could be problematic.

For an alpha developmental landscape, which English corpora would you include first, and which would you exclude or flag?

It would help to know whether there are known landmines around:

- transcription quality,
- recording noise,
- multi-party interaction,
- age ranges,
- clinical status labels,
- task comparability,
- demographic representativeness,
- duplicate participants,
- longitudinal structure.

### 4. How should we handle KidEval, IPSyn, and learned features?

I do not want to build a model that simply reproduces flawed hand-coded measures.

Would you recommend treating KidEval/CLAN outputs as:

- baseline features,
- validation anchors,
- partial clinical descriptors,
- or something closer to normative outputs to preserve?

And for Sagae's work, is there a specific paper, codebase, or current implementation that should be the technical starting point for a learned replacement or complement to IPSyn?

### 5. What data exists for actual treatment response?

Your earlier point was that longitudinal treatment-linked data are extremely sparse, especially for child language delay/DLD, and that many studies use gross measures without shared transcripts.

Given that, what is the best feasible strategy?

Possibilities:

- start with developmental/recovery trajectories without treatment labels,
- extract structured treatment/outcome information from published studies even if transcripts are missing,
- focus on aphasia or stuttering first if treatment data are better,
- build the measurement layer now and design a prospective treatment-response study later,
- use short-term apraxia/script data only as a narrow pilot,
- work with published aggregate effects rather than individual-level prediction.

What would you consider scientifically credible rather than overreaching?

### 6. What would make this useful to clinicians?

Nan Bernstein Ratner's point, as I understand it, is that tools like SALT/SUGAR can identify problems but do not give enough treatment guidance.

If we built a language-state report, what would make it useful rather than just another descriptive profile?

Would useful outputs include:

- likely developmental/recovery trajectory,
- comparison to task-matched peers,
- high-confidence strengths,
- high-value breakdowns,
- near-threshold targets,
- content conveyed versus content missed,
- change since prior sample,
- uncertainty estimates,
- treatment-planning hypotheses,
- specific transcript examples,
- warnings about what not to infer?

What would SLPs actually trust?

### 7. What are the most important papers and datasets?

I would especially appreciate recommendations for:

- the best entry point to Sagae's ML work,
- the IPSyn critique paper when available,
- the strongest KidEval/norming documentation,
- DLD longitudinal prognosis papers,
- DLD treatment-response reviews or datasets,
- aphasia treatment-response reviews, including Marian Brady's recent meta-analysis,
- discourse outcome measurement papers,
- main-concept analysis / CIU work,
- functional communication and participation measures,
- any TalkBank corpora with treatment, recovery, or repeated-measure structure.

### 8. How should Franklin's infrastructure work inform this?

You mentioned that Franklin has made large advances with the infrastructure and related work. I do not want to duplicate or conflict with that.

It would be helpful to know:

- what is already automated or validated,
- what pieces are ready to build on,
- what should not be touched yet,
- what outputs would be most useful for you and Franklin to review,
- where an external alpha could help rather than create cleanup work.

## What I Think the Near-Term Plan Should Be

Unless you steer me elsewhere, I would propose the following sequence.

### Step 1: English CHILDES/KidEval quality audit

Run a careful English-only pass that does not just compute metrics, but documents:

- eligible corpora,
- age coverage,
- participant structure,
- transcript counts,
- one-child/one-adult suitability,
- noisy or complex interaction settings,
- longitudinal structure,
- available clinical labels,
- missing metadata,
- obvious data-quality risks.

Output: a corpus map and quality-filtered developmental landscape.

### Step 2: Measurement benchmark

Compare:

- KidEval/CLAN features,
- IPSyn-style features where appropriate,
- learned language representations,
- simple baselines such as age and MLU,
- task/corpus controls.

Goal: find which features add real signal and which mainly reproduce corpus artifacts.

### Step 3: AphasiaBank validation track

Continue using AphasiaBank to test the general language-state ideas where clinical labels and repeated measures are stronger:

- same WAB-AQ, different discourse state,
- stable WAB but moving discourse state,
- acoustic plus transcript state,
- content-state and repairability,
- Broca not child-like.

Output: a stronger empirical paper or technical report on multidimensional language-state measurement.

### Step 4: Treatment-response data inventory

Systematically inventory what actually exists for treatment-response modeling:

- child language/DLD,
- aphasia,
- apraxia/script training,
- stuttering,
- any other TalkBank-linked or transcript-linked intervention data.

For each source, record:

- individual-level data availability,
- transcript availability,
- baseline measures,
- treatment parameters,
- dose,
- outcome measures,
- timepoints,
- whether data can be shared or reanalyzed.

Output: an honest map of whether treatment-response prediction is possible now, and where a prospective study would be needed.

### Step 5: Clinician-review prototype

Create a small set of de-identified state reports and ask SLPs to judge:

- interpretability,
- usefulness,
- clinical face validity,
- missing constructs,
- risk of misleading recommendations,
- whether the report would change assessment or treatment planning.

This could be the bridge between computational measurement and actual SLP practice.

## Current Bottom Line

I still believe the original project is the right one:

> connect language profiles to likely trajectories and treatment decisions.

But the most responsible path now seems to be:

1. build and validate the language-state measurement layer,
2. audit the available developmental and clinical data honestly,
3. identify where treatment-response data are actually strong enough,
4. use clinician feedback to decide which state dimensions matter,
5. only then claim treatment optimization.

If you think I am aiming too broadly, too clinically, or in the wrong population, I would really value that feedback. The most useful outcome of the call for me would be understanding where this work could genuinely help the field, what I should stop doing, and which data/papers/people should shape the next phase.
