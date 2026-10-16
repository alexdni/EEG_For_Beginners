# Authoring guide

How the Markdown in this repo is written, so it reads the same everywhere and the site builder (`site/build.py`) can turn it into HTML.

## Files

- `modules/NN-slug.md`: one module per file, numbered in teaching order.
- Top-level pages: `README.md`, `schedule.md`, `checkpoints.md`, `resources.md`, `glossary.md`, `notes-template.md`, `data/README.md`.
- Figures: `assets/figures/*.png`, all drawn by `code/figures/make_figures.py` from the sample recordings. Never edit a PNG by hand; change the function and re-run.
- Runnable code: `code/labs/*.py`, using the `code/eeg101` helpers.

## Front matter

Every page starts with YAML front matter. Modules use all fields; other pages need only `title` and `summary`.

```yaml
---
title: "Filtering"
module: 7
week: 2
session: 5
time: "25 min read, 15 min hands-on"
summary: "One sentence that appears on the index card."
---
```

## Building blocks

- **Images**: relative paths, alt text that says what the figure shows: `![Spectrum of O1/O2/Pz eyes closed vs open](../assets/figures/psd_eyes_closed_vs_open.png)`. Follow each figure with an italic caption line naming the sample file it came from.
- **Callouts**: GitHub alert syntax, which renders on GitHub and on the site: `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`.
- **Videos**: a thumbnail that links to the video: `[![Title](https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)`. Only use video IDs that appear in the syllabus or that you have verified.
- **Diagrams**: fenced ```` ```mermaid ```` blocks. Keep them small.
- **Self-check questions**: `<details><summary>Question</summary>Answer</details>`, with a blank line after `<summary>…</summary>` so the answer's Markdown renders.
- **Code**: fenced `python` blocks that run as written against the course samples.

## Voice

- Plain, direct, second person. Say what to look at and why it matters.
- Every number in the text should come from the sample data or a cited source. If a figure shows it, say which.
- Band edges, filter settings and thresholds are conventions; say so when it matters.
- No filler intros. Start each module with what you will be able to do after it.
