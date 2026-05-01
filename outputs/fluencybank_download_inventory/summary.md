# FluencyBank Download Inventory

**Source:** local TalkBankDB transcript export `data/external/fluencybank/TalkBankDB_transcripts.tsv` originally downloaded as `TalkBankDB_transcripts.xls`.

## Bottom Line

- TalkBankDB FluencyBank rows in export: 1,999
- Local accessible corpora downloaded with the current TalkBank cookie: 10
- Local `.cha` transcripts downloaded: 845
- Password-gated transcript rows still not locally available: 1,154

The current cookie is sufficient for all non-password FluencyBank corpora in the export. The biggest recovery-relevant blocked corpus is IISRP, followed by Wagovich, Ratner, IISRP-new, Maxfield, and several cross-sectional password corpora.

## Downloaded Corpora

| corpus | talkbankdb_rows | local_cha_files | languages | designs | groups |
| --- | --- | --- | --- | --- | --- |
| Purdue | 359 | 359 | eng | long:359 | CWS:359 |
| UMD-CMU | 143 | 143 | eng, eng,spa | cross:143 | CWS:87, TD:56 |
| Ulm | 140 | 140 | deu | cross:140 | CWS:140 |
| Voices-AWS | 102 | 102 | eng | cross:102 | AWS:102 |
| Voices-CWS | 48 | 48 | eng | cross:48 | CWS:48 |
| Hakim | 32 | 32 | eng | cross:32 | CWS:16, TD:16 |
| Brejon | 8 | 8 | fra | cross:8 | CWS:8 |
| Voices-AWC | 7 | 7 | eng | cross:7 | AWC:7 |
| VanZaalen | 5 | 5 | eng, nld | null:5 | null:5 |
| Examples | 1 | 1 | eng | null:1 | null:1 |

## Password-Gated Corpora Still Blocked

| corpus | talkbankdb_rows | password_rows | languages | designs | groups |
| --- | --- | --- | --- | --- | --- |
| Maxfield | 17 | 17 | eng | long:17 | AWS:17 |
| Sawyer | 51 | 51 | eng | null:51 | null:51 |
| Ratner | 60 | 60 | eng | long:60 | CWS:44, TD:16 |
| IISRP-new | 89 | 89 | eng | long:54, null:35 | CWS:49, null:35, TD:5 |
| Wagovich | 90 | 90 | eng | long:90 | CWS:90 |
| Tellis | 95 | 95 | eng | cross:95 | CWS:95 |
| IISRP | 752 | 752 | eng | long:752 | CWS:611, TD:141 |

## Research Implication

Purdue is now enough to run a first recovered-versus-persistent stuttering pilot because its local `demographics.xlsx` includes strict `Rec/Per` labels. UMD-CMU is useful for CWS-vs-control and task/year structure, but the local public package does not expose a recovery label. The password-gated IISRP family likely matters most for replication because it has the largest longitudinal recovered/persistent path structure in the TalkBankDB export.
