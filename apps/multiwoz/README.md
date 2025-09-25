## MultiWOZ 2.2 Gradio Explorer

This app lets you browse, search, and chat-view dialogues from the MultiWOZ 2.2 dataset.

### What this app does

- Browse MultiWOZ 2.2 shards on disk (train/dev/test)
- Search/filter dialogues by domain and keyword
- Render a selected dialogue as a chat with a clean, cute UI
- Provide random sampling for quick spot checks

### Where things live

- App code: `apps/multiwoz/app.py`
- App deps: `apps/multiwoz/requirements.txt`
- App docs: `apps/multiwoz/README.md`
- Cloned dataset: `multiwoz/`
  - MultiWOZ 2.2 JSON: `multiwoz/data/MultiWOZ_2.2/{train,dev,test}/dialogues_*.json`
  - Schema: `multiwoz/data/MultiWOZ_2.2/schema.json`
  - Legacy zips (1.0/2.1) extracted under `multiwoz/data/`
  - Preprocessed 2.0 artifacts (delex & splits): `multiwoz/data/{multi-woz,delex.json,train_dials.json,val_dials.json,test_dials.json}`

### Setup & Run

```bash
cd /Users/joyyang/Projects/socrates/one/apps/multiwoz
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
# Fetch dataset (one-time, automatic clone of the official source)
python ../scripts/../scripts/fetch_multiwoz.py
python app.py
```

This will start a local Gradio server and print a local URL you can open in your browser.

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

### Notes

- The original `multiwoz` repo targets legacy Python 2 for model training; this app is Python 3 and only visualizes the modern 2.2 JSON. No training or old dependencies are required.


