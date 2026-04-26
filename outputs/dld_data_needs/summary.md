# DLD Data Needs And Acquisition Memo

## Goal

The DLD track needs outcome data that can answer questions CHILDES transcripts alone cannot answer:

- Which children catch up versus remain persistently impaired?
- Which early speech-state dimensions predict literacy, school, social, or participation outcomes?
- Which targets are associated with later improvement?
- Which model failures reflect dialect, corpus, task, or socioeconomic artifacts?

## Highest-Value Dataset To Pursue

### Manchester Language Study / Conti-Ramsden Cohort

ReShare page: https://reshare.ukdataservice.ac.uk/853965/

Why it matters:

- Longitudinal DLD cohort recruited at age 7 and followed into later childhood and young adulthood.
- Age-11 dataset explicitly includes aims around sensitive DLD markers, literacy, social difficulty/victimization, educational placement, National Curriculum outcomes, and long-term educational needs.
- The ReShare page reports 200 of the original 242 children participated at age 11.
- Related resources include the initial age-7 cohort, age-16 data, and young-adulthood data.

Access:

- Data files are available to registered UK Data Service users under safeguarded access.
- Documentation files are open access.

Why this is more important than another classifier:

This is the first obvious path to testing whether early language state predicts real-world outcomes, not just diagnostic label.

## Other Useful Data Sources

### E-DLD Project

PubMed page: https://pubmed.ncbi.nlm.nih.gov/36565246/

Why it matters:

- International DLD participant database.
- Includes yearly surveys and domains such as SLT support, school support, socialisation, early milestones, strengths/challenges, and well-being.

Access:

- Appears primarily designed as a participant/research engagement database, not an immediately downloadable open dataset.
- Worth contacting for collaboration or prospective validation.

### CHILDES Clinical-Eng

Local status:

- Already downloaded and parsed.
- Useful for transcript-based state discovery, DLD/SLI versus TD screening, late-talker analyses, and heterogeneity.

Limitations:

- Labels are path-derived.
- Outcomes are inconsistent.
- Corpus/task confounding is strong.
- Some older follow-up ages exceed the external TD age-model ceiling.

### Rescorla Late Talker Data In CHILDES

Local status:

- Already present in Clinical-Eng.
- Contains late-talker and TD samples at multiple ages.

Current blocker:

- Some later-age samples have missing `age_months` in the extracted feature table even though age is encoded in paths such as `156`.
- Fixing age parsing for these files should be a near-term task because late-talker catch-up is one of the highest-value DLD questions.

## Data Fields Needed For A Clinically Meaningful DLD Study

Minimum:

- child ID stable across time
- age at every sample
- diagnosis or risk status at each timepoint
- transcript/audio task type
- standardized language scores
- reading/literacy outcomes
- school support or educational placement
- intervention history if available

High value:

- bilingual/multilingual exposure
- dialect/region
- socioeconomic indicators
- sex/gender
- hearing status
- nonverbal cognition
- parent/teacher functional communication ratings
- participation and quality-of-life measures

## Immediate Next Data Tasks

1. Fix Clinical-Eng participant and age parsing for Rescorla and other longitudinal corpora.
2. Use ReShare documentation to map Manchester Language Study variables before requesting/downloading safeguarded data.
3. Build a schema that can join transcript-state features to outcome tables if MLS data are obtained.
4. Prepare a fairness audit plan before any DLD screening claim is framed clinically.

## Current Conclusion

The local CHILDES data are enough for discovery and hypothesis generation. They are not enough to prove clinical utility.

The most important next data acquisition is not more transcript volume. It is longitudinal outcome linkage, especially literacy, school participation, and intervention exposure.

