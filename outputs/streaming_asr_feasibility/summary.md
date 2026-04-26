# Streaming ASR Feasibility

- TalkBank cookie present: True
- Transcript sessions indexed: 2896
- Sessions with acoustic features from streamed media: 691
- Acoustic windows persisted: 1058
- Local audio/video files intentionally persisted: 1 demo WAV plus scratch dirs

## Acoustic Feature Files

| source_file | rows | sessions | windows | size_kb |
| --- | --- | --- | --- | --- |
| acoustic_g0.parquet | 364 | 190 | 364 | 135.30 |
| acoustic_g1.parquet | 232 | 195 | 232 | 95.60 |
| acoustic_g2.parquet | 110 | 79 | 110 | 58.20 |
| acoustic_g3.parquet | 352 | 227 | 352 | 132.00 |

## ASR Backend Status

| kind | name | available | path |
| --- | --- | --- | --- |
| python_module | whisper | False |  |
| python_module | faster_whisper | False |  |
| python_module | mlx_whisper | False |  |
| python_module | torch | True |  |
| python_module | torchaudio | False |  |
| python_module | openai | False |  |
| command | ffmpeg | True | /usr/local/bin/ffmpeg |
| command | whisper | False |  |

## Remote Size Probe

| transcript_id | corpus | participant_id | acoustic_windows | remote_size_mb | candidate_under_limit |
| --- | --- | --- | --- | --- | --- |
| Famous/Control/nrl18a | Control | nrl18a | 1 | 54 | True |
| Famous/Control/nrl19a | Control | nrl19a | 1 | 53 | True |
| Famous/Control/nrl20a | Control | nrl20a | 1 | 245 | True |
| Famous/Control/nrl23a | Control | nrl23a | 1 | 91 | True |
| Famous/Control/nrl24a | Control | nrl24a | 1 | 60 | True |
| Famous/Control/nrl26a | Control | nrl26a | 1 | 43 | True |
| Famous/Control/nrl27a | Control | nrl27a | 1 | 107 | True |
| Famous/Control/nrl28a | Control | nrl28a | 1 | 44 | True |
| Famous/Control/nrl29a | Control | nrl29a | 1 | 40 | True |
| Famous/Control/nrl30a | Control | nrl30a | 1 | 103 | True |
| Famous/Control/nrl31a | Control | nrl31a | 1 | 106 | True |
| Famous/Control/nrl33a | Control | nrl33a | 1 | 98 | True |
| Famous/Control/nrl36a | Control | nrl36a | 1 | 52 | True |
| Famous/Control/nrl38a | Control | nrl38a | 1 | 75 | True |
| Famous/Control/nrl53a | Control | nrl53a | 1 | 145 | True |
| Famous/Control/nrl57a | Control | nrl57a | 1 | 91 | True |
| Famous/Control/nrl58a | Control | nrl58a | 1 | 114 | True |
| Famous/Control/wozniak201 | Control | wozniak201 | 1 | 65 | True |
| Famous/Elman/elman16a | Elman | Elman16a | 1 | 147 | True |
| Famous/Elman/elman18a | Elman | Elman18a | 1 | 195 | True |
| Famous/Kurland/kurland100a | Kurland | Kurland100a | 1 | 223 | True |
| Famous/Kurland/kurland22a | Kurland | Kurland22a | 1 | 249 | True |
| Famous/NRL/nrl09a | NRL | NRL09a | 1 | 72 | True |
| Famous/NRL/nrl11a | NRL | NRL11a | 1 | 87 | True |
| Famous/NRL/nrl16a | NRL | NRL16a | 1 | 72 | True |
| Famous/Pilot/ACWT01a | Pilot | ACWT01a | 1 | 149 | True |
| Famous/Pilot/adler11b | Pilot | adler11b | 1 | 186 | True |
| Famous/Pilot/scale14b | Pilot | scale14b | 1 | 141 | True |
| Famous/SCALE/scale15c | SCALE | SCALE15c | 1 | 106 | True |
| Famous/SCALE/scale17b | SCALE | SCALE17b | 1 | 111 | True |
| Famous/SCALE/scale18c | SCALE | SCALE18c | 1 | 115 | True |
| Famous/Tucson/tucson22a | Tucson | Tucson22a | 1 | 162 | True |
| Famous/Whiteside/whiteside07a | Whiteside | Whiteside07a | 1 | 100 | True |
| Famous/Whiteside/whiteside13a | Whiteside | Whiteside13a | 1 | 121 | True |
| Famous/Whiteside/whiteside18a | Whiteside | Whiteside18a | 1 | 138 | True |
| Famous/Wozniak/wozniak01a | Wozniak | Wozniak01a | 1 | 137 | True |
| Famous/Wozniak/wozniak03a | Wozniak | Wozniak03a | 1 | 167 | True |
| Famous/Wozniak/wozniak05a | Wozniak | Wozniak05a | 1 | 187 | True |
| NonProtocol/ChialFlahive/1 | ChialFlahive | 1 | 1 | 22 | True |
| NonProtocol/ChialFlahive/2 | ChialFlahive | 2 | 1 | 24 | True |

## Interpretation

The real-ASR branch is feasible as a streaming experiment, not a local-file experiment. The next blocker is choosing/installing an ASR backend or using an external API; the media access pattern itself is already implemented by `scripts/extract_aphasia_acoustic.py`.
