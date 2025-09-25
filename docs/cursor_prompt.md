READ THIS FIRST — Imitate the existing app exactly
- Treat `apps/multiwoz` in this GitHub repo as the canonical reference. Replicate its layout, UX, styling (ribbon header, buttons, chat bubbles), component names, and interaction flow as closely as possible.
- Do not invent a new UI pattern. Only change dataset wiring and dataset labels where necessary.

I need you to build Gradio Dataset Explorer App based on this dataset: 

Inputs I have provided for this run
- `DATASET_LINK`: Hugging Face id (e.g., `hf://namespace/name` or `namespace/name`), or an HTTPS URL to `.csv`/`.json`/`.jsonl`, or a local path.
- you decide on the `DATASET_SLUG` based on what's suitable based on the dataset: short folder name for the app under `apps/`.

Constraint
- Make the new app practically identical to `apps/multiwoz` in the repository https://github.com/J0YY/dataset-explorers in UI/UX and styling (ribbon header, Load & Search results as markdown, Dialogue/Item ID selector, View as Chat 💬, Random button). Only data loading changes.
- Assume the engineer will clone and read this repo; reference `apps/multiwoz/app.py` for concrete code structure and reuse it.

Goal: For target dataset link (the dataset i provideed; some may be raw JSON/CSV without any GitHub repo), create a self-contained Gradio app to browse, search/filter, and optionally view a single item as a chat when the schema is conversational.


### High-level checklist

1) Define `DATASET_SLUG` and `DATASET_LINK`
2) Create `apps/<DATASET_SLUG>/` by copying structure and styling from `apps/multiwoz/` (keep the same layout and CSS accents)
3) Implement loaders that abstract over `DATASET_LINK`: Hugging Face datasets (preferred) or CSV/JSON/JSONL files
4) Provide keyword search, item id/index selection (like Dialogue ID), random sampling, and chat rendering if conversational
5) Add a one-line helper script: `scripts/fetch_<DATASET_SLUG>.py` (no args) that prepares the dataset automatically for cloners
6) Add `requirements.txt` and a dataset-specific `README.md` that includes: `python3 scripts/fetch_<DATASET_SLUG>.py` and makes it explicit that the dataset is imported locally before launching
7) Launch locally and verify parity with `apps/multiwoz`
8) Commit only `apps/<DATASET_SLUG>/`, the new script under `scripts/`, and docs, then push

### Conventions

- Place each app at `apps/<dataset_slug>/` with `app.py` and `requirements.txt`
- Never commit large data files; prefer on-demand loading/streaming (Hugging Face `datasets` or HTTP)
- Use `gr.update(...)` for Dropdown updates
- If the dataset is huge, support sampling and pagination parameters
- Treat schemas as unknown; infer columns dynamically

### Source detection strategy

- If `dataset_source` starts with `hf://` or looks like `<namespace>/<name>`: use Hugging Face `datasets.load_dataset`
- If it ends with `.csv`, `.json`, or `.jsonl`: load via pandas or `json`/`jsonlines`
- If it’s a local directory: glob for CSV/JSON files

### App requirements (generic)

```bash
mkdir -p apps/<dataset_slug>
cat > apps/<dataset_slug>/requirements.txt <<EOF
gradio>=4.36.0
datasets>=3.0.0
pandas>=2.2.0
pyarrow>=15.0.0
jsonlines>=4.0.0
EOF
```

### Loader utilities (generic)

```python
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json, random
import pandas as pd
import gradio as gr

try:
    from datasets import load_dataset, get_dataset_config_names
except Exception:
    load_dataset = None
    get_dataset_config_names = None


def is_huggingface_id(src: str) -> bool:
    return src.startswith("hf://") or ("/" in src and not src.startswith("http"))


def normalize_hf_id(src: str) -> str:
    return src.replace("hf://", "").strip()


def load_hf_dataset(hf_id: str, config: Optional[str], split: str, streaming: bool = False):
    kwargs = {"split": split}
    if config:
        kwargs["name"] = config
    if streaming:
        kwargs["streaming"] = True
    return load_dataset(normalize_hf_id(hf_id), **kwargs)


def list_hf_configs(hf_id: str) -> List[str]:
    try:
        return get_dataset_config_names(normalize_hf_id(hf_id))
    except Exception:
        return []


def detect_columns(sample: Dict[str, Any]) -> List[str]:
    return list(sample.keys()) if isinstance(sample, dict) else []


def guess_conversation(sample: Dict[str, Any]) -> Dict[str, Any]:
    # Heuristics: common keys: messages, conversations, dialogue, turns
    for k in ["messages", "conversations", "conversation", "dialogue", "turns", "utterances"]:
        if k in sample and isinstance(sample[k], (list, tuple)):
            seq = sample[k]
            # try to detect role/content pairs
            # variants: {role, content} or {from, value} or pair lists
            return {"container_key": k}
    # OpenAI-style keys
    if "prompt" in sample and "response" in sample:
        return {"prompt_key": "prompt", "response_key": "response"}
    return {}
```

### UI design (works for any tabular/JSON-like dataset)

```python
def build_demo(dataset_source: str) -> gr.Blocks:
    # Pre-scan minimal metadata
    hf_configs = list_hf_configs(dataset_source) if is_hf_id(dataset_source) and get_dataset_config_names else []
    default_split = "train"

    css = """
    .ribbon {background: linear-gradient(90deg, #ffafbd, #ffc3a0); padding: 10px 16px; border-radius: 10px; display: inline-block;}
    .gradio-container .chatbot {--radius: 14px;}
    """
    with gr.Blocks(title="Dataset Explorer", css=css) as demo:
        gr.Markdown("## 🎀 Dataset Explorer\nBrowse, search, and preview items. ✨")

        with gr.Row():
            src = gr.Textbox(value=dataset_source, label="Dataset source (HF id or URL)")
            config = gr.Dropdown(choices=[""] + hf_configs, value=(hf_configs[0] if hf_configs else ""), label="HF config (optional)")
            split = gr.Dropdown(choices=["train","validation","test","unsupervised","all"], value=default_split, label="Split")

        with gr.Row():
            keyword = gr.Textbox(label="Keyword (optional)")
            limit = gr.Slider(1, 100, value=10, step=1, label="Max items")

        with gr.Row():
            load_btn = gr.Button("Load & Search")
            random_btn = gr.Button("Random Item")
        out = gr.Markdown()

        with gr.Row():
            item_id = gr.Textbox(label="Item id/index (optional)")
            chat_btn = gr.Button("View as Chat 💬")
        chat = gr.Chatbot(height=420, bubble_full_width=False)

        def fetch_slice(_src: str, _config: str, _split: str, _kw: str, _limit: int):
            try:
                # Load HF dataset or fallback to pandas
                if is_hf_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    rows = ds.select(range(min(_limit * 50, len(ds)))) if hasattr(ds, "select") else list(ds.take(_limit*50))
                else:
                    # Remote/local CSV/JSON
                    if _src.endswith(".csv"):
                        df = pd.read_csv(_src)
                        rows = df.to_dict(orient="records")
                    elif _src.endswith(".jsonl"):
                        rows = [json.loads(l) for l in Path(_src).read_text(encoding="utf-8").splitlines()]
                    else:
                        # JSON array
                        rows = json.loads(Path(_src).read_text(encoding="utf-8"))
                # Filter by keyword
                kw = (_kw or "").lower()
                out_rows = []
                for r in rows:
                    text = json.dumps(r).lower()
                    if kw and kw not in text:
                        continue
                    out_rows.append(r)
                    if len(out_rows) >= _limit:
                        break
                md = "\n\n---\n\n".join(["```json\n" + json.dumps(r, ensure_ascii=False, indent=2) + "\n```" for r in out_rows])
                return md or "No matches."
            except Exception as e:
                return f"Load error: {e}"

        def random_item(_src: str, _config: str, _split: str):
            try:
                if is_hf_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    idx = random.randint(0, len(ds)-1)
                    r = ds[int(idx)]
                else:
                    if _src.endswith(".csv"):
                        df = pd.read_csv(_src)
                        r = df.sample(1).to_dict(orient="records")[0]
                    elif _src.endswith(".jsonl"):
                        lines = Path(_src).read_text(encoding="utf-8").splitlines()
                        r = json.loads(random.choice(lines))
                    else:
                        arr = json.loads(Path(_src).read_text(encoding="utf-8"))
                        r = random.choice(arr)
                return "```json\n" + json.dumps(r, ensure_ascii=False, indent=2) + "\n```"
            except Exception as e:
                return f"Random error: {e}"

        def view_chat(_src: str, _config: str, _split: str, _id: str):
            try:
                if is_hf_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    sample = ds[0] if len(ds) > 0 else {}
                    meta = guess_conversation(sample)
                    # pick record by index if id is int; else attempt exact id match if column exists
                    rec = ds[int(_id)] if _id.isdigit() else next((r for r in ds if str(r.get("id","")) == _id), ds[0])
                else:
                    # For files, try index or id field
                    if _src.endswith(".csv"):
                        df = pd.read_csv(_src)
                        rec = df.iloc[int(_id)].to_dict() if _id.isdigit() else df.iloc[0].to_dict()
                        sample = rec
                    elif _src.endswith(".jsonl"):
                        lines = Path(_src).read_text(encoding="utf-8").splitlines()
                        rec = json.loads(lines[int(_id)]) if _id.isdigit() else json.loads(lines[0])
                        sample = rec
                    else:
                        arr = json.loads(Path(_src).read_text(encoding="utf-8"))
                        rec = arr[int(_id)] if _id.isdigit() else arr[0]
                        sample = rec
                    meta = guess_conversation(sample)

                history: List[Tuple[str,str]] = []
                if "container_key" in meta:
                    seq = rec.get(meta["container_key"], [])
                    for m in seq:
                        role = (m.get("role") or m.get("from") or m.get("speaker") or "").lower()
                        content = m.get("content") or m.get("value") or m.get("text") or ""
                        if role in ("user","human"):
                            history.append((content, ""))
                        elif role in ("assistant","system","gpt","bot"):
                            if not history:
                                history.append(("", content))
                            else:
                                u, _ = history[-1]
                                if _ == "":
                                    history[-1] = (u, content)
                                else:
                                    history.append(("", content))
                elif "prompt_key" in meta:
                    history.append((rec.get(meta["prompt_key"], ""), rec.get(meta["response_key"], "")))
                else:
                    # Fallback: single message view
                    history.append((json.dumps(rec)[:2000], ""))
                return history
            except Exception as e:
                return [(f"Chat error: {e}", "")]

        load_btn.click(fetch_slice, inputs=[src, config, split, keyword, limit], outputs=[out])
        random_btn.click(random_item, inputs=[src, config, split], outputs=[out])
        chat_btn.click(view_chat, inputs=[src, config, split, item_id], outputs=[chat])

    return demo
```

### Per-dataset README template

Include:
- Dataset link and short description
- How data is loaded (HF id or URL) and any auth requirements
- How to run the app and what users should see (splits present, typical columns, sample item count)
- Any dataset-specific filters or mappings you added to the UI

### Monorepo layout

```
apps/
  <dataset-1>/
    app.py
    requirements.txt
    README.md
  <dataset-2>/
  ...
.gitignore   # excludes data caches and docs
```

Recommended `.gitignore` additions for data caches:

```
# HF cache
~/.cache/huggingface/
**/datasets/**
.cache/

Also anchor ignores for any top-level dataset clones to avoid excluding app folders of the same name. For example:

```
# Anchor to repo root so apps/multiwoz is tracked, but /multiwoz at root is ignored
/multiwoz/
```
```

### Final verification checklist

- App launches without errors
- Search returns items with/without keyword
- If conversational, Chat view renders sensible bubbles
- Random sampling works
- Large datasets: app remains responsive (consider streaming/pagination if needed)

### Notes carried over from MultiWOZ work

- Use `gr.update(...)` when mutating Dropdowns
- Prefer reading only the selected slice/shard/page, not entire corpora
- Keep datasets out of git; rely on runtime download/streaming


### GitHub push instructions (same monorepo)

Target repo: `https://github.com/J0YY/dataset-explorers.git` (branch: `main`).

1) Ensure `.gitignore` excludes `docs/`, dataset clones, venvs, and caches (already set at repo root).
2) Stage and commit only the new app folder:

```bash
cd /Users/joyyang/Projects/socrates/one
git add apps/<DATASET_SLUG>
git commit -m "feat(apps/<DATASET_SLUG>): add Gradio explorer for <DATASET_LINK>"
git push
```

If the remote is not configured (first time on a new machine):

```bash
git remote add origin https://github.com/J0YY/dataset-explorers.git
git push -u origin main
```

3) Verify on GitHub that `apps/<DATASET_SLUG>/` appears with `app.py`, `requirements.txt`, and `README.md`.

### Helper fetch script template

Create `scripts/fetch_<DATASET_SLUG>.py` (no arguments). It should fetch from the canonical source automatically so users only run one command. Choose one of the branches below.

1) Hugging Face dataset (preferred): pre-populate local cache

```python
#!/usr/bin/env python3
from datasets import load_dataset

HF_ID = "<DATASET_LINK>"  # e.g., "namespace/name" or "hf://namespace/name"
SPLITS = ["train", "validation", "test"]  # include those that exist

def main():
    hf_id = HF_ID.replace("hf://", "")
    for split in SPLITS:
        try:
            ds = load_dataset(hf_id, split=split)
            # Touch a few rows to force materialization into the cache
            _ = ds.select(range(min(100, len(ds))))
            print(f"Cached split: {split} (rows={len(ds)})")
        except Exception as e:
            print(f"Skip split {split}: {e}")

if __name__ == "__main__":
    main()
```

2) Git repo or direct file URL: clone or download to a known top-level directory

```python
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
import urllib.request

REPO_OR_FILE = "<DATASET_LINK>"  # e.g., https://...git or https://.../data.jsonl
TARGET_DIR = Path(__file__).resolve().parents[1] / "<top_level_data_dir>"

def run(cmd):
    print("$", " ".join(cmd)); return subprocess.call(cmd)

def main():
    if REPO_OR_FILE.endswith(".git"):
        if TARGET_DIR.exists():
            run(["git", "-C", str(TARGET_DIR), "pull", "--ff-only"]) or sys.exit(0)
        else:
            sys.exit(run(["git", "clone", REPO_OR_FILE, str(TARGET_DIR)]))
    else:
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        out = TARGET_DIR / Path(REPO_OR_FILE).name
        urllib.request.urlretrieve(REPO_OR_FILE, out)
        print("Downloaded:", out)

if __name__ == "__main__":
    main()
```

In the app README, include this one-liner before `python app.py`:

```bash
python3 scripts/fetch_<DATASET_SLUG>.py
```



