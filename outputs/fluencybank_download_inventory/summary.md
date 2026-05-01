# FluencyBank Download Inventory

**Source:** local TalkBankDB transcript export `data/external/fluencybank/TalkBankDB_transcripts.tsv`.

## Bottom Line

- TalkBankDB FluencyBank rows in export: 1,999
- Corpus ZIPs requested: 17
- Local `.cha` transcripts downloaded: 1,999
- Password-gated `.cha` transcripts now local: 1,154

The current TalkBank cookie can access the formerly password-gated transcript
ZIPs. This unblocks IISRP, IISRP-new, Wagovich, Ratner, Maxfield, Tellis, and
Sawyer for transcript-level modeling. Media access still needs separate probing
before acoustic extraction.

## Downloaded Corpora

| corpus | TalkBankDB rows | password rows | local `.cha` files | status | languages | designs | groups |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| IISRP | 752 | 752 | 752 | cached | eng | long:752 | CWS:611, TD:141 |
| Purdue | 359 | 0 | 359 | not_requested | eng | long:359 | CWS:359 |
| UMD-CMU | 143 | 0 | 143 | not_requested | eng, eng,spa | cross:143 | CWS:87, TD:56 |
| Ulm | 140 | 0 | 140 | not_requested | deu | cross:140 | CWS:140 |
| Voices-AWS | 102 | 0 | 102 | not_requested | eng | cross:102 | AWS:102 |
| Tellis | 95 | 95 | 95 | cached | eng | cross:95 | CWS:95 |
| Wagovich | 90 | 90 | 90 | cached | eng | long:90 | CWS:90 |
| IISRP-new | 89 | 89 | 89 | cached | eng | long:54, null:35 | CWS:49, TD:5, null:35 |
| Ratner | 60 | 60 | 60 | cached | eng | long:60 | CWS:44, TD:16 |
| Sawyer | 51 | 51 | 51 | cached | eng | null:51 | null:51 |
| Voices-CWS | 48 | 0 | 48 | not_requested | eng | cross:48 | CWS:48 |
| Hakim | 32 | 0 | 32 | not_requested | eng | cross:32 | CWS:16, TD:16 |
| Maxfield | 17 | 17 | 17 | cached | eng | long:17 | AWS:17 |
| Brejon | 8 | 0 | 8 | not_requested | fra | cross:8 | CWS:8 |
| Voices-AWC | 7 | 0 | 7 | not_requested | eng | cross:7 | AWC:7 |
| VanZaalen | 5 | 0 | 5 | not_requested | eng, nld | null:5 | null:5 |
| Examples | 1 | 0 | 1 | not_requested | eng | null:1 | null:1 |

## Still Missing

| corpus | TalkBankDB rows | password rows | status | error |
| --- | ---: | ---: | --- | --- |
| none | 0 | 0 | n/a | n/a |

## Research Implication

The stuttering recovery track should move from a Purdue-only feasibility pilot
to a replication-grade FluencyBank analysis. The highest-priority next model is
not another earliest-transcript classifier. It should use longitudinal change,
group path structure (`CWS-rec`, `CWS-per`, TD/CWNS), disfluency classes,
language-growth features, and corpus-held-out validation across Purdue, IISRP,
IISRP-new, Wagovich, Ratner, and UMD-CMU where labels permit.
