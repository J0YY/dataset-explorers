## MiSC Dataset Explorer (Gradio)

- Dataset: `jihyoung/MiSC` on Hugging Face. See the dataset card: [`https://huggingface.co/datasets/jihyoung/MiSC`](https://huggingface.co/datasets/jihyoung/MiSC)
- Purpose: browse, keyword-search, and preview items; render a single item as a chat when the schema is conversational.

### Features

- Ribbon-styled UI, parity with `apps/multiwoz` (header, layout, buttons).
- Source dropdown supports:
  - Hugging Face id (e.g., `jihyoung/MiSC`)
  - Discovered local files under `data/misc/*.jsonl|*.json|*.csv`
  - Custom values (type/paste any URL or path)
- HF config dropdown auto-refreshes for HF ids (disabled for files).
- Keyword search across entire records or a single field.
- Max items slider to limit number of records displayed.
- Random Item sampling.
- Item id/index selector to open a specific record in Chat.
- Chat view 💬 for MiSC sessions: aligns `*_session_dialogue` with speakers and renders alternating bubbles.
- Collapsible Search Results with a sticky “Collapse/Expand Results” button.

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r apps/misc/requirements.txt
```

### Fetch data (one-liner)

```bash
python3 scripts/fetch_misc.py
```

What it does:
- Tries to cache HF splits via `datasets.load_dataset` (ignores builder errors).
- Always downloads raw JSONL files via Hugging Face Hub to `data/misc/{train,val,test}.jsonl`.

### Run the app

```bash
python3 apps/misc/app.py
```

### Using the app

- Dataset source: choose `jihyoung/MiSC` or a local file like `data/misc/train.jsonl`.
- HF config (optional): only shows for HF ids (MiSC has none; it will be empty).
- Split: `train`, `validation`, `test` (for HF ids only; ignored for files).
- Keyword: text to search for.
- Search field: optional key/column to restrict matching (blank = search entire record).
- Max items: number of records shown in Search Results.
- Load & Search: displays matched items as JSON markdown.
- Random Item: shows a single random item.
- Item id/index: integer index or exact `id` if present; then click “View as Chat 💬”.

### MiSC chat mapping

From each record, the app:
- Uses `main_speaker` if present; otherwise the first entry of `speaker_list` as the user.
- Detects all keys containing `"dialogue"` (e.g., `first_session_dialogue`).
- For arrays like `[[speakers...],[utterances...]]`, zips them to turns.
- Renders the main speaker as the user bubble and other speakers as assistant bubbles.
- Falls back to generic rendering if a record has a novel shape.

### Troubleshooting

- “Load error: … path … not found”: ensure the path exists; run the fetch script to create `data/misc/*.jsonl`.
- HF config shows a lone check: the dropdown is disabled for files; switch source to an HF id.
- Max items limits records, not turns inside a single record.

### License & citation

- Dataset license/citation: see the dataset card: [`https://huggingface.co/datasets/jihyoung/MiSC`](https://huggingface.co/datasets/jihyoung/MiSC)


