# Human and AI Interpretations of Humorous Contradictions

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
<!-- TODO before release: add the repository DOI badge once the archive is minted. -->

Response data accompanying the manuscript **Are We Seeing the Same Humor? Comparing Human and AI
Interpretations of Humorous Contradictions**, submitted to the *International Journal of
Human–Computer Interaction*.

**166 human participants** and **eight vision-language models** interpreted the same **270 two-panel
comics** from Gudim's *YesBut* series. Each response bundles four annotations of one comic:

| Column | What it captures |
| --- | --- |
| `bboxes` | Regions the respondent marked as carrying the contradiction or the humor |
| `reason` | Free-text explanation of why the juxtaposition is contradictory or funny |
| `title_choice` | One of four candidate titles |
| `category_choice` | Target–Norm Matrix category (`PV`, `PL`, `SV`, `SL`) |

Humans and models performed **identical tasks on identical stimuli**, so the two response tables are
comparable row for row. That alignment is the point of the release.

The comics and the English title questions come from the **YESBUT benchmark** (Hu et al., NeurIPS
2024); the responses, bounding boxes, and category labels are new. Benchmark-derived material is
**regenerated, not redistributed** — see [Rebuilding the stimuli](#rebuilding-the-stimuli).

## Contents

```text
README.md                            this file
codebook.csv                         column-by-column spec for every table  ← the authoritative one
human_responses.csv                  4,041 human responses
model_responses.csv                  2,160 model responses (8 models x 270 images)
models.csv                           8 models and their request settings
stimuli_images.csv                   the 270 analyzed images
excluded_images.csv                  the 78 benchmark images that were excluded, and why
image_transform.csv                  per-image parameters that rebuild the study images
translation_manual_corrections.csv   11 reviewed corrections to the explanation translations
scripts/build_study_images.py        upstream images      -> the 1080x1080 study images
scripts/build_title_translations.py  upstream annotations -> title_options.csv (EN + KO)
```

`codebook.csv` gives the type, permitted values, missing-value convention, and caveats for every
column in every table. **Read it before writing analysis code**; this file covers only what the
codebook cannot say in a cell.

Every table is keyed on the same `image_id`, so any two join directly:

```text
stimuli_images.csv ──image_id──┬──> image_transform.csv   (how to rebuild the stimulus)
                               ├──> excluded_images.csv   (disjoint: the other 78)
                               ├──> human_responses.csv ──subject_id──┬─> (participant, 19–29 rows)
                               │                                      └─> translation_manual_corrections.csv
                               ├──> model_responses.csv ──model_id────> models.csv
                               └──> title_options.csv ───option_letter─> title_choice, both tables
                                      (regenerated locally; see Title options)
```

All files are UTF-8 CSV with a header row and standard quoting.

## Quick start

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

## Study design

Participants completed an online study on PC or mobile, taking roughly 45 minutes. For each assigned
comic they marked the visual elements carrying the contradiction or humor, explained their
interpretation in free text, and chose one of four titles; they then classified the same comics
using the Target–Norm Matrix. Models performed the corresponding annotation tasks, prompted with the
category descriptions and example comics.

Korean participants saw a Korean interface and Korean title options; English participants and all
models saw the English options. The same letter (`A`–`D`) labelled the same option in both
languages, so `title_choice` is comparable across languages.

### Participants

**Each participant was assigned 30 comics** from a 330-comic pool. Of 220 participants, **54 were
excluded** for response quality: explanations shorter than four characters for at least 50% of
assigned comics, **or** title-selection accuracy below 25%.

- **Retained participants contribute 19–29 rows, not 30.** The analysis was later restricted to 270
  images, and responses to images that did not make that set were removed with them. Models are
  unaffected: every model answered all 270, giving a full 8 × 270 grid.
- **Screening cannot be rerun here.** It used each participant's original 30 responses; the excluded
  participants and out-of-set responses are not distributed.

### Stimulus selection

```text
348  benchmark annotation snapshot
 −18  removed before the study ran      13 non_compliant + 5 example
 330  study pool, shown to participants and models
 −60  removed after                     60 model_error
 270  analyzed
```

| Code | Images | Stage | Meaning |
| --- | ---: | --- | --- |
| `example` | 5 | before | Instructional examples: `00002`, `00018`, `00103`, `00105`, `00128`. |
| `non_compliant` | 13 | before | No comparable two-panel layout split at the vertical midline, or photographic rather than comic-style content. A grouped reason, with no per-image subtype. |
| `model_error` | 60 | after | Attributed by the authors to model-side errors. Per-image subtypes were not recorded. |

`stimuli_images.csv` and `excluded_images.csv` partition the 348. The 330-image pool is the
denominator for participant screening; the 270 analyzed images are the denominator for everything
else.

## Bounding boxes

`bboxes` holds JSON — ordinary JSON, not a Python literal — inside one CSV cell. Each inner list is
`[nx1, ny1, nx2, ny2]`: top-left and bottom-right corners of one box, normalized by the width and
height of the **full 1080 × 1080 study image**, margins included. Origin top-left, `x` rightward,
`y` downward. Box order is preserved but means nothing — not a panel label, not a ranking.

> Coordinates are relative to the **preprocessed study canvas**, not to a panel, not to the browser
> window, and **not to an upstream download**. Rebuild the study images before overlaying anything.

**Coordinates are distributed exactly as stored, unclipped.** The intended range is `[0, 1]`, but
**207 human rows contain 214 boxes with a coordinate outside it** (roughly `[-0.430, 1.449]`), from
drag gestures that ran past the image edge. Model boxes are all in range.

The study analysis applies these steps, and reproductions should too:

```python
def clean(box):
    """Clip to [0,1], order the endpoints, drop degenerate boxes."""
    x1, y1, x2, y2 = (min(max(v, 0.0), 1.0) for v in box)
    x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2))
    return None if x1 == x2 or y1 == y2 else (x1, y1, x2, y2)
```

For panel-based metrics, a box belongs to the **left (YES) panel** when its horizontal midpoint is
below `0.5`, and to the **right (BUT) panel** otherwise.

## Rebuilding the stimuli

The comics are not redistributed, and the images shown in the study were preprocessed — the YES and
BUT headings and surrounding text removed, the result standardized onto a 1080 × 1080 white canvas.
The bounding-box coordinate frame is only recoverable by rebuilding them.

```bash
# 1. originals, via the upstream repository's own downloader
git clone https://github.com/Tuo-Liang/YESBUT && cd YESBUT
git checkout 90186c127419110eb80fdce3f7336738da545303
python download_images.py --json_file data/YesBut_data.json --save_folder data/YesBut_images

# 2. the study preprocessing
python scripts/build_study_images.py --src /path/to/YesBut_images --out study_images
```

`image_transform.csv` records the crop band and canvas placement **measured from the delivered study
images**, and the script replays them; the script's header documents the transform and the original
border-detection heuristic, which `--detect` reproduces but which does not recover the delivered
layout for 21 of the 270 images. A correct build contains exactly 270 files. The folder is not
cleared first — the script warns if it holds anything else, and `--clean` removes it.

Verified: rebuilding all 270 from an upstream download gives a mean absolute pixel difference of 1.3
against the delivered stimuli (worst 6.4, JPEG and resampling noise) with identical ink bounds. Rerun
that check with `--verify /path/to/reference_images`.

## Title options

`title_choice` stores the **selected letter**, not correctness and not title text. The option text is
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
request settings, and the verbatim prompt; it applied **no manual post-editing**. Because the request
pins no temperature, a rerun gives equivalent but not character-identical Korean wording. Analyses of
`title_choice` itself are unaffected — letters and the answer key are stable upstream content.

## Target–Norm Matrix

`category_choice` records the **respondent's own interpretation**, not a ground-truth label. The
matrix crosses a *personal* versus *social/non-personal* target with a *value-based* versus
*logic-based/situational* norm.

| Code | Target | Norm or expectation |
| --- | --- | --- |
| `PV` | Personal: an individual character's actions, choices, beliefs, circumstances | Value-based: moral or social norms, beliefs, principles, convictions |
| `PL` | Personal | Logic-based/situational: physical circumstances, logic, common sense, factual incongruity |
| `SV` | Social/non-personal: institutions, collective practices, environments, structures | Value-based |
| `SL` | Social/non-personal | Logic-based/situational |

## Explanations and translation

`reason` preserves the original free-text response verbatim, including spelling and punctuation, and
is never replaced by the translation. For Korean responses, `translated_reason` holds the English
text used in the translation-based analysis: `gpt-4o-mini` at temperature `0`, instructed to preserve
nuance and causal logic without summarizing or adding interpretation.

Translations were verified by cross-lingual similarity against the Korean source
(`paraphrase-multilingual-mpnet-base-v2`), and flagged items were repaired three ways: batches that
returned shifted results were re-translated one at a time; confirmed mistranslations were
re-translated individually; and 11 fragmentary responses across 9 participants were corrected by
hand. `translation_manual_corrections.csv` logs all 11 in full — participant, Korean source, the
machine output that was replaced, the corrected English, and the reason — so every difference
between raw and distributed translation is attributable to a named row.

These are **reviewed derived text**: not raw API output, and not independent responses.

## Models

Join on `model_id`; quote `api_model_id` when reporting what was called. Responses were collected on
2026-07-20 and 2026-07-21.

| `model_id` | Model | Provider | `api_model_id` |
| --- | --- | --- | --- |
| `claude_opus_4.7` | Claude Opus 4.7 | Anthropic | `claude-opus-4-7` |
| `gemini_3.1_pro` | Gemini 3.1 Pro Preview | Google | `gemini-3.1-pro-preview` |
| `gpt_5.5` | GPT-5.5 | OpenAI | `gpt-5.5` |
| `gpt_5.6_sol` | GPT-5.6 Sol | OpenAI | `gpt-5.6-sol` |
| `grok_4.3` | Grok 4.3 | xAI | `grok-4.3` |
| `mistral_large_3` | Mistral Large 3 | Mistral AI | `mistral-large-2512` |
| `mistral_small_4` | Mistral Small 4 | Mistral AI | `mistral-small-2603` |
| `qwen_3.7_plus` | Qwen3.7-Plus | Alibaba Cloud | `qwen3.7-plus` |

Request settings in `models.csv` were **reconstructed from the experiment configuration and client
code, not from logged payloads**. `not_explicitly_set` means the request omits the parameter — not
that it was zero, and not a provider default; the per-model `notes` column says how each temperature
resolved. One retained response per image does not establish that only one API call was made, and
because API aliases change and generation is nondeterministic, the recorded settings do not
regenerate the saved outputs verbatim. Timestamps carry no timezone and describe the *retained*
responses, not the full run.

**Not bundled:** comic images, preprocessed study images, title option text, the annotation task
prompts, analysis code, and complete API and error logs. The first three are regenerable with
`scripts/`.

## Ethics and privacy

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

## Sources and attribution

- **Original benchmark:** [YESBUT_Benchmark on Hugging Face](https://huggingface.co/datasets/zhehuderek/YESBUT_Benchmark)
- **Pinned annotation snapshot** (the version the study used, and what the scripts expect):
  [`data/Yesbut_data.json` at YESBUT commit `90186c1`](https://github.com/Tuo-Liang/YESBUT/blob/90186c127419110eb80fdce3f7336738da545303/data/Yesbut_data.json).
  This identifies the annotation version, not the download date.
- **Original artwork:** the *YesBut* comics by Anton Gudim. No rights to the artwork are transferred
  here; the images are referenced, not redistributed.

> Hu, Z., Liang, T., Li, J., Lu, Y., Zhou, Y., Qiao, Y., Ma, J., & Yin, Y. (2024). *Cracking the
> Code of Juxtaposition: Can AI Models Understand the Humorous Contradictions?* NeurIPS 2024.
> [arXiv:2405.19088](https://arxiv.org/abs/2405.19088)

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

## Citation

<!-- TODO before release: mint a DOI by depositing on OSF or Zenodo, then fill in the placeholders
     and add the DOI badge at the top of this file. -->

Please cite both the article and the dataset deposit, and also the underlying benchmark (Hu et al.,
2024, above).

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

**Data availability statement** — for the manuscript, not this file. Taylor & Francis asks that it
sit in the text before the References, under that heading. This wording combines their *"openly
available in a public repository that issues datasets with DOIs"* and *"data derived from public
domain resources"* templates:

> The data that support the findings of this study are openly available in *[repository]* at
> *[DOI]*. These data were derived from the following resource available in the public domain: the
> YESBUT benchmark (Hu et al., 2024), https://huggingface.co/datasets/zhehuderek/YESBUT_Benchmark.
> The comic stimuli and title questions are not redistributed; the repository provides the scripts
> needed to reconstruct them from that source.

## Contact

TODO — corresponding author name and email.
<!-- Omit until after review if the journal uses anonymous peer review: a statement naming the
     authors or an identifying repository can break anonymity. -->
