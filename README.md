# Human and AI Interpretations of Humorous Contradictions Dataset

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
<!-- TODO before release: add the repository DOI badge once the archive is minted. -->

Response data accompanying the manuscript **Are We Seeing the Same Humor? Comparing Human and AI
Interpretations of Humorous Contradictions**, submitted to the *International Journal of
Human–Computer Interaction*.

The dataset records how **166 human participants** and **eight vision-language models** interpreted
the same **270 two-panel comics** from Gudim's *YesBut* series. Every response bundles four
coordinated annotations of a single comic:

| Response component | Column | What it captures |
| --- | --- | --- |
| Visual attention | `bboxes` | Regions the respondent marked as carrying the contradiction or the humor |
| Free-text interpretation | `reason` | Why the respondent found the juxtaposition contradictory or funny |
| Forced choice | `title_choice` | One of four candidate titles for the comic |
| Structured label | `category_choice` | Target–Norm Matrix category (`PV`, `PL`, `SV`, `SL`) |

Because humans and models performed **identical tasks on identical stimuli**, the two response
tables are directly comparable row for row: `(image_id, bboxes, reason, title_choice,
category_choice)` has the same meaning on both sides. That alignment is the point of the release.

The comics and the English title questions come from the **YESBUT benchmark** (Hu et al., NeurIPS
2024). The human and model responses, the bounding-box annotations, and the Target–Norm Matrix
labels were collected for the present study.

> **Benchmark-derived material is regenerated, not redistributed.** The comic images, the
> preprocessed study images, and the title option text all derive from a CC BY-NC-ND benchmark.
> This package ships the exact transform parameters and the scripts that rebuild them from the
> original source, so every stimulus a respondent saw is reproducible without redistributing a
> derivative. See [Rebuilding the stimuli](#rebuilding-the-stimuli).

---

## Contents

```text
.
├── README.md                     this file
├── codebook.csv                  machine-readable definition of every column in every table
├── human_responses.csv           4,041 human responses
├── model_responses.csv           2,160 model responses (8 models x 270 images)
├── models.csv                    8 evaluated models and their request settings
├── stimuli_images.csv            270 analyzed image filenames
├── excluded_images.csv           78 benchmark images excluded from the analysis
├── image_transform.csv           per-image parameters that rebuild the study images
├── translation_manual_corrections.csv   11 reviewed corrections to the explanation translations
└── scripts/
    ├── build_study_images.py            upstream images      -> the 1080x1080 study images
    └── build_title_translations.py      upstream annotations -> title_options.csv (EN + KO)
```

| File | Data rows | Primary key | Contents |
| --- | ---: | --- | --- |
| `human_responses.csv` | 4,041 | `subject_id` + `image_id` | 3,922 Korean responses from 161 participants; 119 English responses from 5 participants. |
| `model_responses.csv` | 2,160 | `model_id` + `image_id` | One retained response per model per image; every model answered all 270. All explanations are in English. |
| `models.csv` | 8 | `model_id` | Model names, API identifiers, retained-response timestamps, and request settings reconstructed from the experiment code. |
| `stimuli_images.csv` | 270 | `image_id` | The comics in the analysis. Image files are **not** included. |
| `excluded_images.csv` | 78 | `image_id` | Other benchmark images and why they were excluded. |
| `image_transform.csv` | 270 | `image_id` | Source crop band and canvas placement for each study image. |
| `translation_manual_corrections.csv` | 11 | `image_id` + `subject_id` | Every manual correction applied to `translated_reason`, with the machine output it replaced and the stated reason. |
| `codebook.csv` | 49 | `file` + `column` | Type, permitted values, missing-value convention, and caveats for every column. |

All CSVs are UTF-8 with a header row and standard CSV quoting (commas, quotation marks, and
embedded newlines are quoted).

### Entity relationships

Every table is keyed on the same `image_id`, so any two of them join directly with no string
surgery:

```text
stimuli_images.csv ──image_id──┬──> image_transform.csv   (how to rebuild the stimulus)
                               ├──> excluded_images.csv   (disjoint: the other 78)
                               ├──> human_responses.csv ──subject_id──┬─> (participant, 19–29 rows each)
                               │                                      └─> translation_manual_corrections.csv
                               ├──> model_responses.csv ──model_id────> models.csv
                               └──> title_options.csv ───option_letter─> title_choice in both response tables
                                      (regenerated locally; see Title options)
```

`image_id` is the identifier, not a filename. The corresponding image file is `image_id + ".jpg"`,
which is also the key used by the upstream annotation file and by the scripts in `scripts/`.

---

## Quick start

```python
import csv, json

def load(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))      # keeps image_id as a string

human = load("human_responses.csv")
row = human[0]
boxes = json.loads(row["bboxes"])            # [[nx1, ny1, nx2, ny2], ...]
```

```python
import pandas as pd
human = pd.read_csv("human_responses.csv", dtype=str)   # dtype=str is required
```

> **Read `image_id` as a string.** It is a five-digit, zero-padded identifier (`00001`), used
> unchanged in every table; parsing it as an integer silently breaks every join. Append `".jpg"`
> only when you need the image file itself or the upstream annotation record.

---

## Study design

Human participants completed an online study on PC or mobile, taking roughly 45 minutes. For each
assigned comic they (1) marked the visual elements carrying the contradiction or the humor by
drawing boxes, (2) explained their interpretation in free text, and (3) chose one of four candidate
titles. They then classified the same comics using the Target–Norm Matrix. Models performed the
corresponding annotation tasks, prompted with the category descriptions and example comics.

Korean participants saw a Korean interface and Korean title options; English participants and all
models saw the English options. The same letter (`A`–`D`) labelled the same option in both
languages, so `title_choice` is comparable across languages.

### Participants and screening

**Each participant was assigned 30 comics** drawn from a 330-comic study pool. Of 220 participants,
**54 were excluded** under the response-quality criteria reported in the manuscript: explanations
shorter than four characters for at least 50% of assigned comics, **or** title-selection accuracy
below 25%.

Two consequences for anyone reusing these CSVs:

- **Retained participants contribute 19–29 rows, not 30.** After screening, the analysis was
  restricted to the final 270 images, and each participant's responses to images that did not make
  that set — mostly images dropped for model-side errors — were removed along with the images. The
  unequal row counts are this filtering, not rows lost during export. Models are unaffected: each
  model answered all 270 retained images, giving a full 8 × 270 grid.
- **Screening cannot be rerun from this package alone.** It used each participant's original 30
  responses, and the excluded participants and out-of-set responses are not distributed.

### Stimulus selection

The benchmark snapshot was narrowed in two stages. `excluded_images.csv` lists all 78 images that
did not reach the analysis, and together with `stimuli_images.csv` it partitions the 348.

```text
348  benchmark annotation snapshot
 −18  removed before the study ran      13 non_compliant + 5 example
 330  study pool, shown to participants and models
 −60  removed after                     60 model_error
 270  analyzed
```

| Code | Images | Stage | Meaning |
| --- | ---: | --- | --- |
| `example` | 5 | before | Shown as instructional examples: `00002`, `00018`, `00103`, `00105`, `00128`. |
| `non_compliant` | 13 | before | No comparable two-panel layout split at the vertical midline, or photographic rather than comic-style content. A grouped reason, without an image-specific subtype. |
| `model_error` | 60 | after | Attributed by the authors to model-side errors. Per-image error subtypes were not recorded. |

The 330-image study pool is the denominator for participant screening; the 270 analyzed images are
the denominator for everything else.

---

## Variables

`codebook.csv` is the authoritative, machine-readable specification: one row per column, with data
type, permitted values, missing-value convention, and caveats. The tables below are a readable
summary of the same information — consult the codebook before writing analysis code.

### `human_responses.csv`

| Column | Type | Description |
| --- | --- | --- |
| `subject_id` | string | Pseudonymous participant ID, `P001`–`P166`. Links repeated responses by the same person. |
| `image_id` | string | Five-digit comic ID. |
| `response_lang` | categorical | `ko` (161 participants, 3,922 rows) or `en` (5 participants, 119 rows). |
| `bboxes` | JSON array | Marked regions; see [Bounding boxes](#bounding-boxes). 2–26 boxes per response. |
| `reason` | string | Original free-text explanation, verbatim, in the language given by `response_lang`. |
| `translated_reason` | string | English translation of a Korean `reason`; the literal string `null` for English responses. |
| `title_choice` | categorical | Selected letter `A`–`D`. **Not** a correctness indicator. |
| `category_choice` | categorical | `PV`, `PL`, `SV`, or `SL`; see [Target–Norm Matrix](#targetnorm-matrix). |

### `model_responses.csv`

| Column | Type | Description |
| --- | --- | --- |
| `model_id` | categorical | Dataset identifier; foreign key to `models.csv`. |
| `image_id` | string | Five-digit comic ID. |
| `bboxes` | JSON array | Marked regions; 2–7 boxes per response, all within `[0, 1]`. |
| `reason` | string | Retained free-text explanation. English for every model, so there is no `response_lang` or `translated_reason` column. |
| `title_choice` | categorical | Selected letter `A`–`D`. |
| `category_choice` | categorical | `PV`, `PL`, `SV`, or `SL`. |

### `image_transform.csv`

| Column | Type | Description |
| --- | --- | --- |
| `image_id` | string | Five-digit comic ID. |
| `src_width`, `src_height` | integer | Pixel dimensions of the upstream source image, before processing. Widths of 680–1200 occur. |
| `src_band_top` | integer | Top row of the retained comic band, measured **after** the source is scaled to width 1080. |
| `src_band_height` | integer | Height of that band (445–853 observed). It spans the full 1080-pixel width. |
| `dst_band_top` | integer | Row at which the band is pasted onto the 1080 × 1080 study canvas (113–424 observed). |

### `translation_manual_corrections.csv`

| Column | Type | Description |
| --- | --- | --- |
| `image_id` + `subject_id` | string | Identify exactly one row of `human_responses.csv`. 11 corrections across 9 participants. |
| `reason` | string | The original Korean, copied verbatim from `human_responses.csv`. Same column name, same value. |
| `old_translated_reason` | string | What `gpt-4o-mini` returned before correction. **Does not appear in the distributed data** — kept so the change is auditable. |
| `new_translated_reason` | string | The corrected English, copied verbatim from `translated_reason` in `human_responses.csv`. |
| `correction_details` | string | Why the machine translation was wrong, and the evidence for the correction. |

### `models.csv`, `stimuli_images.csv`, `excluded_images.csv`

See `codebook.csv`. Two `models.csv` conventions are easy to misread: **`not_explicitly_set`** means
the request omits the parameter — not that it was zero, and not a provider default;
**`not_recorded`** means the information was never stored.

---

## Bounding boxes

`bboxes` holds a JSON-encoded nested list inside one CSV cell — ordinary JSON, not a Python literal.
Each inner list is `[nx1, ny1, nx2, ny2]`: the top-left and bottom-right corners of one box,
normalized by the width and height of the **full 1080 × 1080 study image**, margins included. The
origin is the top-left corner; `x` increases rightward and `y` downward.

Box order is preserved but carries no meaning — it is neither a panel label nor a ranking of
importance. A single response may place several boxes in either panel.

> Coordinates are relative to the **preprocessed study canvas**, not to an individual panel, not to
> the browser window, and **not to an upstream download**. Rebuild the study images with
> [`scripts/build_study_images.py`](#rebuilding-the-stimuli) before overlaying them on anything.

### Cleaning the coordinates

**Coordinates are distributed exactly as stored, without clipping or rounding.** The intended range
is `[0, 1]`, but **207 human response rows contain 214 boxes with at least one coordinate outside
it** (observed range approximately `[-0.430, 1.449]`), the result of drag gestures that ran past the
image edge. Model boxes are all in range.

The study analysis applies these steps, and reproductions should apply them too:

1. Clip every coordinate to `[0, 1]`.
2. Sort the two `x` endpoints and the two `y` endpoints (a box drawn right-to-left stores `nx1 > nx2`).
3. Discard boxes with zero width or height after clipping.
4. For panel-based metrics, assign a box to the **left (YES) panel** when its horizontal midpoint is
   below `0.5`, and to the **right (BUT) panel** otherwise.

```python
def clean(box):
    x1, y1, x2, y2 = (min(max(v, 0.0), 1.0) for v in box)
    x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2))
    return None if x1 == x2 or y1 == y2 else (x1, y1, x2, y2)
```

---

## Rebuilding the stimuli

The comic images are not redistributed. The images **shown in the study** were preprocessed and
differ from an upstream download, so the bounding-box coordinate frame is only recoverable by
rebuilding them. Both steps below take one command.

### 1. Download the originals

Use the upstream repository's own downloader against the pinned annotation snapshot:

```bash
git clone https://github.com/Tuo-Liang/YESBUT && cd YESBUT
git checkout 90186c127419110eb80fdce3f7336738da545303
python download_images.py --json_file data/YesBut_data.json --save_folder data/YesBut_images
```

### 2. Apply the study preprocessing

```bash
python scripts/build_study_images.py \
    --src /path/to/YESBUT/data/YesBut_images \
    --out study_images
```

The output folder is not cleared first, so a re-run into a folder that already holds files leaves
them in place; the script warns when that happens and reports the real file count. Pass `--clean` to
remove anything the run did not write. A correct build contains exactly 270 files, one per row of
`stimuli_images.csv`.

The preprocessing removed the text outside the comic panels — including the YES and BUT headings —
and standardized every stimulus to a 1080 × 1080 white canvas with the YES panel on the left and the
BUT panel on the right. Per image, the transform is:

1. Scale the source to width 1080, preserving aspect ratio. Source widths range from 680 to 1200.
2. Keep only the vertical band between the comic's top and bottom border lines, recorded as
   `src_band_top` and `src_band_height`. Everything above and below — heading text and margin — is
   discarded.
3. Paste that band onto a white 1080 × 1080 canvas at row `dst_band_top`.

The original border detection scanned in from the top and bottom of each image for the first row in
which ink covered at least 80% of the width. `--detect` reproduces that heuristic, but it is **not**
the default: 21 of the 270 images were left at their source vertical position rather than centred,
so the heuristic alone does not recover the delivered layout. `image_transform.csv` records the band
and placement measured from the images respondents actually saw, and the default path replays those.

Verified reproduction: rebuilding all 270 images from the upstream download and comparing against
the delivered stimuli gives a mean absolute pixel difference of 1.3 (worst case 6.4), consistent
with JPEG requantization and resampling, with identical ink bounds. To re-run that check yourself,
pass `--verify /path/to/reference_images`.

---

## Title options

`title_choice` stores the **selected letter**, not correctness and not title text. To recover the
option text, regenerate `title_options.csv`:

```bash
# English options and the reference answer key -- no API key needed
python scripts/build_title_translations.py --upstream /path/to/Yesbut_data.json \
                                      --out title_options.csv --english-only

# add the Korean options shown to Korean-language participants
ANTHROPIC_API_KEY=... python scripts/build_title_translations.py \
    --upstream /path/to/Yesbut_data.json --out title_options.csv
```

| Column | Description |
| --- | --- |
| `image_id` | Five-digit comic ID. |
| `option_letter` | `A`–`D`; joins to `title_choice` in both response tables. |
| `option_en` | English option text, copied verbatim from the upstream `title_mcq` field. Shown to English participants and to all models. |
| `option_ko` | Korean option text shown to Korean participants. Machine translation of `option_en`. |
| `is_reference_answer` | `true` for the single upstream reference answer per image (upstream `title_mcq_answer`), else `false`. |

The English options and reference answers are upstream content and reproduce exactly — all 1,080
option strings match the pinned snapshot. The Korean options are a **translation, and therefore an
adaptation of CC BY-NC-ND material**, which is why they are regenerated locally rather than shipped.

### Korean translation provenance

The settings below are what the study issued, and what the script reproduces:

| Setting | Value |
| --- | --- |
| Provider / API | Anthropic Messages API |
| Model | `claude-haiku-4-5-20251001` |
| `max_tokens` | `4096` |
| Temperature | not set in the request (provider default) |
| Batch size | 10 images per request |
| Post-editing | none — the delivered Korean options are the model output as returned |

The prompt was issued in Korean, verbatim as follows, with `{numbered}` replaced by the batch's
option blocks each prefixed with a `[n]` marker:

```text
다음은 웹툰/만화 이미지에 대한 영어 제목 4지선다 문제들입니다.
각 항목을 한국어로 번역해주세요.

번역 규칙:
- A. B. C. D. 기호는 그대로 유지하세요
- 의미와 뉘앙스를 최대한 보존하세요
- 자연스러운 한국어로 번역하세요
- 고유명사(브랜드, 제품명 등)는 영어 또는 한국어 표기 중 자연스러운 것으로 하세요
- 각 항목은 [숫자] 형식으로 구분해서 출력하세요
- 번역 외 다른 설명은 출력하지 마세요

{numbered}
```

Because the request pins no temperature and commercial model aliases change over time, **a rerun
produces equivalent but not character-identical Korean wording.** Analyses that depend on the exact
strings presented should report the regeneration date and settings. Analyses of `title_choice`
itself are unaffected: the letter labels and the reference answer are upstream content and are
stable.

---

## Target–Norm Matrix

`category_choice` records the **respondent's own interpretation**, not a benchmark ground-truth
label. The matrix crosses a *personal* versus *social/non-personal* target with a *value-based*
versus *logic-based/situational* norm.

| Code | Target | Norm or expectation |
| --- | --- | --- |
| `PV` | Personal: an individual character's actions, choices, beliefs, or circumstances | Value-based: moral or social norms, beliefs, principles, convictions |
| `PL` | Personal | Logic-based/situational: physical circumstances, logic, common sense, factual incongruity |
| `SV` | Social/non-personal: institutions, collective practices, environments, broader structures | Value-based |
| `SL` | Social/non-personal | Logic-based/situational |

---

## Explanations and translation

`reason` preserves the original free-text response, including its spelling, punctuation, and
whitespace. It is never replaced by the translation.

For Korean responses, `translated_reason` holds the final English text used in the translation-based
analysis. Unlike the title options, these are participants' own words — the study's own data — and
are distributed in full.

| Setting | Value |
| --- | --- |
| Model | `gpt-4o-mini`, temperature `0` |
| Prompt | *Translate the Korean research-survey reason into natural English. Preserve the original nuance, causal logic, humor interpretation, and key wording as closely as possible. Do not summarize or add interpretation. Return only the English translation as plain text, with no quotes and no commentary.* |
| Verification | Cross-lingual similarity between each Korean source and its English translation, using `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |
| Flagging rule | Similarity below `0.55` flagged for review; flagged items back-translated and confirmed as mistranslations below a back-translation similarity of `0.75`. Sources under 12 characters score low even when correct and were judged individually. |

Corrections followed three rules, applied only to flagged items:

1. **Batch-misalignment repair.** Batched requests occasionally returned translations shifted within
   a batch, so a response received a neighbour's English text while its own was dropped. Affected
   items were re-translated **one at a time**, which cannot misalign, and re-verified.
2. **Individual mistranslation repair.** Items confirmed by back-translation were re-translated
   individually and manually checked.
3. **Reviewed manual substitution — 11 responses, 9 participants.** Fragmentary or ambiguous Korean
   (mostly 3–12 characters) where the correct reading depends on what the comic shows, and where the
   model refused, transliterated instead of translating, or inverted the meaning. Each substitution
   was decided by reading other participants' responses to the same image.
   `translation_manual_corrections.csv` logs all 11 in full — the participant, the Korean source, the
   machine output that was replaced, the corrected English, and the reason — so every difference
   between raw and distributed translation is attributable to a named row.

The distributed translations are therefore **reviewed derived text** — not raw API output, and not
independent responses. Treat them as a support for the original Korean, not a replacement.

---

## Models

`models.csv` separates three identifiers: the display `model_name`, the dataset's normalized
`model_id`, and the `api_model_id` actually configured in the experiment. Always join on `model_id`;
quote `api_model_id` when reporting what was called.

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

Responses were collected on 2026-07-20 and 2026-07-21.

---

## Known limitations

Stated plainly so that reuse does not over-read the tables:

- **Participant screening cannot be rerun.** It used each participant's original 30 responses, and
  the excluded participants and out-of-set responses are not distributed.
- **Bounding boxes are uncleaned and tied to a stimulus image that is not bundled.** Apply the
  cleaning steps above, and rebuild the study images before overlaying anything.
- **Request settings are reconstructed from the experiment configuration and client code, not from
  logged payloads.** An omitted parameter is not evidence of a provider default, and one retained
  response per image does not establish that only one API call was made.
- **Exact regeneration is not guaranteed.** Commercial API aliases change and generation is
  nondeterministic, so the recorded names and settings do not reproduce the saved model outputs or
  the Korean title wording verbatim.
- **Timestamps carry no timezone,** and describe the *retained* responses rather than the full run.
- **Not bundled:** comic images, preprocessed study images, title option text, the annotation task
  prompts, analysis code, and complete API and error logs. The first three are regenerable with
  `scripts/`.

---

## Ethics and privacy

<!-- Anonymous review: no institution or approval number below. After acceptance, restore the
     committee's full name and the approval number, which journals normally require. -->

The study was reviewed and approved by the institutional review board of the authors' university.
All participants gave informed consent, which covered public sharing of the research data.

Direct identifiers were replaced with pseudonymous IDs. **Phone numbers, dates of birth,
participant-level timestamps, demographic records, and the private identifier mapping are not
distributed.** Repeated responses by the same person remain linked through `subject_id`, which
carries no information about who that person is.

Free-text explanations are participants' own words about publicly published comics and were not
screened for re-identifying content; none is expected, but the text is distributed verbatim.

---

## Sources and attribution

- **Original benchmark:** [YESBUT_Benchmark on Hugging Face](https://huggingface.co/datasets/zhehuderek/YESBUT_Benchmark)
- **Pinned annotation snapshot** (the version this study used, and the one the scripts expect):
  [`data/Yesbut_data.json` at YESBUT commit `90186c1`](https://github.com/Tuo-Liang/YESBUT/blob/90186c127419110eb80fdce3f7336738da545303/data/Yesbut_data.json)
  — this identifies the matching annotation version; it does not establish the download date.
- **Original artwork:** the *YesBut* comics by Anton Gudim. No rights to the artwork are transferred
  by this release, which references rather than redistributes the images.

> Hu, Z., Liang, T., Li, J., Lu, Y., Zhou, Y., Qiao, Y., Ma, J., & Yin, Y. (2024). *Cracking the
> Code of Juxtaposition: Can AI Models Understand the Humorous Contradictions?* NeurIPS 2024.
> [arXiv:2405.19088](https://arxiv.org/abs/2405.19088)

---

## License

<!-- TODO before release: confirm with your institution, then delete this comment. -->

**Data and scripts in this repository: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).**
This covers the human and model responses, the bounding boxes, the Target–Norm Matrix labels, the
explanation translations, the model metadata, the transform manifest, the codebook, and the scripts
in `scripts/` — all newly produced for this study.

No benchmark content is redistributed here. The comic images, the preprocessed study images, and the
title option text remain under the upstream benchmark's
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) terms, and reach you from the
upstream source via the scripts in `scripts/`. `image_transform.csv` records measurements of those
images, not the images themselves. Anything you generate by running these scripts is governed by the
upstream license, not by this one.

---

## Citation

<!-- TODO before release: mint a DOI by depositing this package on OSF or Zenodo, then replace the
     placeholders below and add the DOI badge at the top of this file. -->

If you use this dataset, please cite both the accompanying article and the dataset deposit:

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

Please also cite the underlying benchmark (Hu et al., 2024; see [Sources and
attribution](#sources-and-attribution)).

### Data availability statement

For the manuscript, not for this file. Taylor & Francis asks that the statement sit **in the text
before the References section, under the heading "Data availability statement"**. The wording below
combines their *"openly available in a public repository that issues datasets with DOIs"* and
*"data derived from public domain resources"* templates, which is what this deposit is:

> The data that support the findings of this study are openly available in *[repository]* at
> *[DOI]*. These data were derived from the following resource available in the public domain: the
> YESBUT benchmark (Hu et al., 2024), https://huggingface.co/datasets/zhehuderek/YESBUT_Benchmark.
> The comic stimuli and title questions are not redistributed; the repository provides the scripts
> needed to reconstruct them from that source.

---

## Contact

TODO — corresponding author name and email.
<!-- Omit until after review if the journal uses anonymous peer review: a statement naming the
     authors or an identifying repository can break anonymity. -->
