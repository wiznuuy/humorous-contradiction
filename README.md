# Human and AI Interpretations of Humorous Contradictions

This repository contains the response dataset accompanying our work on how people and vision-language
models interpret visual humor. The dataset is organized around annotations of two-panel *YesBut*
comics built on top of the YESBUT benchmark, and includes marked visual regions, free-text
interpretations, title choices, contradiction-type labels, model request metadata, and the scripts
that rebuild every benchmark-derived stimulus from its original source.

## Overview

The repository currently contains:

- 4,041 human responses from 166 participants, in Korean (3,922 from 161 participants) and English
  (119 from 5 participants).
- 2,160 model responses from eight vision-language models, one per model per image.
- 270 unique comic stimuli, identified by a five-digit `image_id`, plus the 78 benchmark images
  excluded from the analysis and the reason for each.
- 11 reviewed manual corrections to the machine translations of Korean explanations.

At a high level, each dataset entry links one respondent to one comic, together with four
annotations recorded for that pairing:

| Column | What it captures |
| --- | --- |
| `bboxes` | Regions the respondent marked as carrying the contradiction or the humor |
| `reason` | Free-text explanation of why the juxtaposition is contradictory or funny |
| `title_choice` | One of four candidate titles, stored as the selected letter `A`–`D` |
| `category_choice` | Target–Norm Matrix category: `PV`, `PL`, `SV`, or `SL` |

An entry is identified by `image_id` plus the respondent — `subject_id` in `human_responses.csv`,
`model_id` in `model_responses.csv`:

```text
P001,00001,ko,"[[0.077,0.477,0.314,0.676], ...]",...,B,SL
claude_opus_4.7,00001,"[[0.08,0.35,0.48,0.72], ...]",...,B,SL
```

## Task Framing

The study compares human and model interpretation of humorous contradiction. Humans and models
performed **identical tasks on identical stimuli**, so the two response tables are comparable row
for row — `(image_id, bboxes, reason, title_choice, category_choice)` means the same thing on both
sides, and that alignment is the point of the release.

The dataset structure makes the comparison explicit:

- Both response tables carry the same four annotation columns, with no model-only or human-only
  fields beyond response language.
- Every model answered all 270 images, giving a full 8 × 270 grid; human coverage is sparse by
  design, with 19–29 responses per participant.
- `bboxes` from both sides are normalized against the same 1080 × 1080 study canvas, so spatial
  attention is directly comparable.
- `title_choice` is comparable across languages: Korean participants saw Korean options, but the
  same letter labelled the same option in both versions.

The comics and the English title questions come from the YESBUT benchmark (Hu et al., NeurIPS 2024).
Benchmark-derived material is **regenerated, not redistributed** — see
[Rebuilding the stimuli](#rebuilding-the-stimuli).

## Repository Structure

```text
.
├── README.md
├── codebook.csv
├── human_responses.csv
├── model_responses.csv
├── models.csv
├── stimuli_images.csv
├── excluded_images.csv
├── image_transform.csv
├── translation_manual_corrections.csv
└── scripts/
    ├── build_study_images.py
    └── build_title_translations.py
```

Every table is keyed on the same `image_id`, so any two join directly:

```text
stimuli_images.csv ──image_id──┬──> image_transform.csv   (how to rebuild the stimulus)
                               ├──> excluded_images.csv   (disjoint: the other 78)
                               ├──> human_responses.csv ──subject_id──┬─> (participant)
                               │                                      └─> translation_manual_corrections.csv
                               ├──> model_responses.csv ──model_id────> models.csv
                               └──> title_options.csv ───option_letter─> title_choice, both tables
                                      (regenerated locally; see Title options)
```

## Files

**`codebook.csv` is the authoritative specification** — one row per column of every table, with data
type, permitted values, missing-value conventions, and caveats. Read it before writing analysis code.
This file covers only what the codebook cannot say in a cell.

### Response tables

- `human_responses.csv`: one row per `(subject_id, image_id)` pair. `response_lang` gives the
  language of `reason`; `translated_reason` holds the English translation used in the
  translation-based analysis, or the literal string `null` for responses already in English.
- `model_responses.csv`: one row per `(model_id, image_id)` pair. All explanations are in English,
  so there is no language or translation column.

### Supporting tables

- `models.csv`: display name, dataset `model_id`, provider, and `api_model_id` for each model, with
  the request settings and retained-response timestamps.
- `stimuli_images.csv` / `excluded_images.csv`: the 270 analyzed images and the 78 excluded ones,
  with an exclusion code per excluded image. Together they partition the 348-image benchmark
  annotation snapshot.
- `image_transform.csv`: the crop band and canvas placement that turn each upstream image into the
  stimulus respondents saw.
- `translation_manual_corrections.csv`: all 11 hand corrections to `translated_reason`, each with the
  participant, the Korean source, the machine output it replaced, and the reason — so every
  difference between raw and distributed translation is attributable to a named row.

### Scripts

- `build_study_images.py`: rebuilds the 270 preprocessed study images from an upstream download.
- `build_title_translations.py`: rebuilds `title_options.csv`, the four title options per comic in
  English and Korean.

Each script's header documents its inputs, its transform, and the exact request settings used in the
study.

## Using the Dataset

```python
import csv, json

with open("human_responses.csv", encoding="utf-8", newline="") as fh:
    human = list(csv.DictReader(fh))        # keeps image_id as a string

boxes = json.loads(human[0]["bboxes"])      # [[nx1, ny1, nx2, ny2], ...]
```

```python
import pandas as pd
human = pd.read_csv("human_responses.csv", dtype=str)   # dtype=str is required
```

> **Read `image_id` as a string.** It is a five-digit, zero-padded identifier (`00001`), used
> unchanged in every table; parsing it as an integer silently breaks every join. Append `".jpg"`
> only when you need the image file itself or the upstream annotation record.

### Bounding boxes

`bboxes` holds JSON — ordinary JSON, not a Python literal — inside one CSV cell. Each inner list is
`[nx1, ny1, nx2, ny2]`: top-left and bottom-right corners of one box, normalized by the width and
height of the **full 1080 × 1080 study image**, margins included. Origin top-left, `x` rightward, `y`
downward. Box order is preserved but means nothing — not a panel label, not a ranking.

> Coordinates are relative to the **preprocessed study canvas**, not to a panel, not to the browser
> window, and **not to an upstream download**. Rebuild the study images before overlaying anything.

**Coordinates are distributed exactly as stored, unclipped.** The intended range is `[0, 1]`, but
**207 human rows contain 214 boxes with a coordinate outside it** (roughly `[-0.430, 1.449]`), from
drag gestures that ran past the image edge. Model boxes are all in range. The study analysis applies
these steps, and reproductions should too:

```python
def clean(box):
    """Clip to [0,1], order the endpoints, drop degenerate boxes."""
    x1, y1, x2, y2 = (min(max(v, 0.0), 1.0) for v in box)
    x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2))
    return None if x1 == x2 or y1 == y2 else (x1, y1, x2, y2)
```

For panel-based metrics, a box belongs to the **left (YES) panel** when its horizontal midpoint is
below `0.5`, and to the **right (BUT) panel** otherwise.

### Model request settings

Settings in `models.csv` were **reconstructed from the experiment configuration and client code, not
from logged payloads.** `not_explicitly_set` means the request omits the parameter — not that it was
zero, and not a provider default; the per-model `notes` column says how each temperature resolved.
One retained response per image does not establish that only one API call was made, and because API
aliases change and generation is nondeterministic, the recorded settings do not regenerate the saved
outputs verbatim. Timestamps carry no timezone and describe the *retained* responses, not the full
run.

## Rebuilding the stimuli

The repository stores responses and transform metadata, but does not redistribute the comic images.
The images shown in the study were preprocessed — the YES and BUT headings and surrounding text
removed, the result standardized onto a 1080 × 1080 white canvas — so the bounding-box coordinate
frame is only recoverable by rebuilding them.

```bash
# 1. originals, via the upstream repository's own downloader
git clone https://github.com/Tuo-Liang/YESBUT && cd YESBUT
git checkout 90186c127419110eb80fdce3f7336738da545303
python download_images.py --json_file data/YesBut_data.json --save_folder data/YesBut_images

# 2. the study preprocessing
python scripts/build_study_images.py --src /path/to/YesBut_images --out study_images
```

`image_transform.csv` records the crop band and canvas placement **measured from the delivered study
images**, and the script replays them. The original border-detection heuristic is reproduced by
`--detect`, but is not the default: it does not recover the delivered layout for 21 of the 270
images. A correct build contains exactly 270 files; the output folder is not cleared first, so the
script warns if it holds anything else, and `--clean` removes it.

Verified: rebuilding all 270 from an upstream download gives a mean absolute pixel difference of 1.3
against the delivered stimuli (worst 6.4, JPEG and resampling noise) with identical ink bounds. Rerun
that check with `--verify /path/to/reference_images`.

## Title options

`title_choice` stores the selected letter, not correctness and not title text. The option text is
benchmark-derived, so it is regenerated rather than shipped:

```bash
# English options and the reference answer key — no API key needed
python scripts/build_title_translations.py --upstream /path/to/Yesbut_data.json \
                                           --out title_options.csv --english-only

# add the Korean options shown to Korean-language participants
ANTHROPIC_API_KEY=... python scripts/build_title_translations.py \
    --upstream /path/to/Yesbut_data.json --out title_options.csv
```

This yields `image_id`, `option_letter`, `option_en`, `option_ko`, `is_reference_answer`. The English
options and answer key are upstream content and reproduce exactly — all 1,080 strings match the
pinned snapshot. The Korean options are a machine translation, and therefore an **adaptation of
CC BY-NC-ND material**, which is why they are not distributed. The script's header records the model,
request settings, and the verbatim prompt; no manual post-editing was applied. Because the request
pins no temperature, a rerun gives equivalent but not character-identical Korean wording. Analyses of
`title_choice` itself are unaffected — letters and the answer key are stable upstream content.

`translated_reason` in `human_responses.csv` was produced the same way, with `gpt-4o-mini` at
temperature `0`, then verified by cross-lingual similarity and repaired where flagged; the 11 hand
corrections are logged in `translation_manual_corrections.csv`. Both translation sets are **reviewed
derived text**: not raw API output, and not independent responses.

**Not bundled:** comic images, preprocessed study images, title option text, the annotation task
prompts, analysis code, and complete API and error logs. The first three are regenerable with
`scripts/`.

## Ethics and Privacy

<!-- Anonymous review: no institution or approval number below. After acceptance, restore the
     committee's full name and the approval number, which journals normally require. -->

The study was reviewed and approved by the institutional review board of the authors' university.
All participants gave informed consent, which covered public sharing of the research data.

Direct identifiers were replaced with pseudonymous IDs. **Phone numbers, dates of birth,
participant-level timestamps, demographic records, and the private identifier mapping are not
distributed.** Repeated responses stay linked through `subject_id`, which says nothing about who the
person is. Free-text explanations are participants' own words about publicly published comics; they
were not screened for re-identifying content, and none is expected, but they are distributed
verbatim.

## Sources and Attribution

- **Original benchmark:** [YESBUT_Benchmark on Hugging Face](https://huggingface.co/datasets/zhehuderek/YESBUT_Benchmark)
- **Pinned annotation snapshot** (the version the study used, and what the scripts expect):
  [`data/Yesbut_data.json` at YESBUT commit `90186c1`](https://github.com/Tuo-Liang/YESBUT/blob/90186c127419110eb80fdce3f7336738da545303/data/Yesbut_data.json).
  This identifies the annotation version, not the download date.
- **Original artwork:** the *YesBut* comics by Anton Gudim. No rights to the artwork are transferred
  here; the images are referenced, not redistributed.

> Hu, Z., Liang, T., Li, J., Lu, Y., Zhou, Y., Qiao, Y., Ma, J., & Yin, Y. (2024). *Cracking the
> Code of Juxtaposition: Can AI Models Understand the Humorous Contradictions?* NeurIPS 2024.
> [arXiv:2405.19088](https://arxiv.org/abs/2405.19088)
<!--
## Citation
-->
<!-- TODO before release: mint a DOI by depositing on OSF or Zenodo, then fill in the placeholders
     and add a DOI badge at the top of this file. -->
<!-- 
If you use this dataset, please cite our article and the dataset deposit, and also the underlying
benchmark (Hu et al., 2024, above):

```bibtex
@article{TODO_study_key,
  author  = {TODO},
  title   = {Are We Seeing the Same Humor? Comparing Human and AI Interpretations of Humorous Contradictions},
  journal = {International Journal of Human--Computer Interaction},
  year    = {TODO},
  doi     = {TODO}
}

@dataset{TODO_dataset_key,
  author    = {TODO},
  title     = {Human and AI Interpretations of Humorous Contradictions},
  year      = {TODO},
  publisher = {TODO (Zenodo / OSF)},
  doi       = {TODO}
}
```
-->
## License

<!-- TODO before release: confirm with your institution, then delete this comment. -->

**Data and scripts: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)** — the responses,
bounding boxes, category labels, explanation translations, model metadata, transform manifest,
codebook, and `scripts/`, all newly produced for this study.

No benchmark content is redistributed. The comic images, preprocessed study images, and title option
text stay under the upstream benchmark's
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) terms and reach you from the
upstream source via `scripts/`; anything you generate by running them is governed by that license,
not this one. `image_transform.csv` records measurements of those images, not the images themselves.
