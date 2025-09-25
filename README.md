## Gradio Dataset Explorer Apps — MultiWOZ 2.2

This repo contains a Gradio app that lets you browse, search, and chat-view dialogues from the MultiWOZ 2.2 dataset cloned in this workspace. It also includes tooling and notes to replicate this pattern for additional datasets.

### What this app does

- Browse MultiWOZ 2.2 shards on disk (train/dev/test)
- Search/filter dialogues by domain and keyword
- Render a selected dialogue as a chat with a clean, cute UI
- Provide random sampling for quick spot checks

### Where things live

- App code: `gradio_app/app.py`
- App deps: `gradio_app/requirements.txt`
- App docs: `gradio_app/README.md`
- Cloned dataset: `multiwoz/`
  - MultiWOZ 2.2 JSON: `multiwoz/data/MultiWOZ_2.2/{train,dev,test}/dialogues_*.json`
  - Schema: `multiwoz/data/MultiWOZ_2.2/schema.json`
  - Legacy zips (1.0/2.1) extracted under `multiwoz/data/`
  - Preprocessed 2.0 artifacts (delex & splits): `multiwoz/data/{multi-woz,delex.json,train_dials.json,val_dials.json,test_dials.json}`

### Quickstart

1) Launch the Gradio app

```bash
cd /Users/joyyang/Projects/socrates/one/gradio_app
pip install -r requirements.txt
python app.py
```

2) Use the UI

- Split: choose `train`, `dev`, or `test`
- Shard file: select one of the `dialogues_XXX.json` files for that split
- Domain (optional): pick a domain (e.g., `train`, `hotel`, `restaurant`), or leave blank
- Keyword (optional): filter utterances text (case-insensitive)
- Max dialogues: how many results to render in the list view
- Load & Search: produces markdown transcript blocks with bolded USER/SYSTEM lines
- Dialogue ID: pick a `dialogue_id` from the selected shard
- View as Chat 💬: shows the selected dialogue in a chat-style view
- Random Dialogue: shows a random dialogue across a random split/shard

### What you should see

- Shard dropdown lists:
  - train: 17 shards (`dialogues_001.json` … `dialogues_017.json`)
  - dev: 2 shards (`dialogues_001.json`, `dialogues_002.json`)
  - test: 2 shards (`dialogues_001.json`, `dialogues_002.json`)
- Dialogue ID dropdown fills with many IDs (e.g., `PMUL2307.json`).
- “Load & Search” shows one or more dialogue blocks with:
  - Title line: the `dialogue_id`
  - Services line: comma-separated domains for that dialogue
  - Alternating bold labels: `USER:` and `SYSTEM:` + utterance
- “View as Chat 💬” shows alternating bubbles for user/assistant; if a conversation starts with the system or ends with an unmatched user, it is rendered gracefully.

### Dataset preparation (already done here)

These steps are recorded in case you need to reproduce locally.

```bash
cd /Users/joyyang/Projects/socrates/one/multiwoz
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
pip install --force-reinstall 'nltk==3.8.1'
python -m nltk.downloader -d ./nltk_data wordnet omw-1.4
python create_delex_data.py
python -c "import zipfile; zipfile.ZipFile('data/MultiWOZ_1.0.zip').extractall('data/MultiWOZ_1.0')"
python -c "import zipfile; zipfile.ZipFile('data/MultiWOZ_2.1.zip').extractall('data/MultiWOZ_2.1')"
```

Notes:
- The Gradio app only needs the MultiWOZ 2.2 JSON files; it does not require the legacy preprocessing to run.
- We pinned `nltk==3.8.1` to make WordNet downloads work smoothly.

### Troubleshooting

- Shard dropdown shows a single letter or errors with “too many values to unpack”: make sure you’re running the latest `gradio_app/app.py`. The app uses `gr.update(...)` to update dropdown choices/values safely.
- Gradio not installed: run `pip install -r gradio_app/requirements.txt` in your current environment.
- Empty results: try removing the domain/keyword filters or switch to another shard.

### Naming suggestions for a multi-app monorepo

Pick a name that communicates “dataset viewers” plus “Gradio”. A few ideas:

- `gradio-dataset-studio`
- `dataset-explorer-hub`
- `nlp-dataset-gallery`
- `dialogue-datasets-lab`
- `gradio-data-voyager`
- `socratic-dataset-apps`

Recommended layout when adding more apps:

```
apps/
  multiwoz/               # this app (or move from gradio_app/)
    app.py
    requirements.txt
    README.md
  <dataset-2>/
  <dataset-3>/
multiwoz/                 # cloned source repo(s)
<other-source-repos>/
docs/
  cursor_prompt.md
```

### Citations

- MultiWOZ repository and documentation: `https://github.com/budzianowski/multiwoz?tab=readme-ov-file#`


