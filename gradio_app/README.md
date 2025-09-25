## MultiWOZ 2.2 Gradio Explorer

This lightweight Gradio app lets you browse and search MultiWOZ 2.2 dialogues that were cloned alongside this workspace.

### Prerequisites

- Python 3.9+ recommended
- The dataset exists at `../multiwoz/data/MultiWOZ_2.2/`

### Setup

```bash
cd /Users/joyyang/Projects/socrates/one/gradio_app
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

This will start a local Gradio server and print a local URL you can open in your browser.

### Notes

- The original `multiwoz` repo targets legacy Python 2 for model training; this app is Python 3 and only visualizes the modern 2.2 JSON data shipped inside the repo. No training or old dependencies are required.


