from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

import gradio as gr
import pandas as pd

DATASET_LINK = "jihyoung/MiSC"

try:
    from datasets import load_dataset, get_dataset_config_names
except Exception:  # pragma: no cover - optional dependency at authoring time
    load_dataset = None
    get_dataset_config_names = None


def is_huggingface_id(src: str) -> bool:
    s = (src or "").strip()
    if s.startswith("hf://"):
        return True
    # Treat local/absolute/relative paths as NON-HF
    if s.startswith("/") or s.startswith("./") or s.startswith("../"):
        return False
    if Path(s).exists():
        return False
    # Plain namespace/name pattern counts as HF id
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", s))


def normalize_hf_id(src: str) -> str:
    return src.replace("hf://", "").strip()


def load_hf_dataset(hf_id: str, config: Optional[str], split: str, streaming: bool = False):
    if load_dataset is None:
        raise RuntimeError("datasets library not available")
    kwargs: Dict[str, Any] = {"split": split}
    if config:
        kwargs["name"] = config
    if streaming:
        kwargs["streaming"] = True
    return load_dataset(normalize_hf_id(hf_id), **kwargs)


def list_hf_configs(hf_id: str) -> List[str]:
    try:
        if get_dataset_config_names is None:
            return []
        return get_dataset_config_names(normalize_hf_id(hf_id))
    except Exception:
        return []


def guess_conversation(sample: Dict[str, Any]) -> Dict[str, Any]:
    # Try common container keys first
    for k in [
        "messages",
        "conversations",
        "conversation",
        "dialogue",
        "dialog",
        "turns",
        "utterances",
        "sessions",
    ]:
        if k in sample and isinstance(sample[k], (list, tuple)):
            return {"container_key": k}
    # Prompt/response pattern
    if "prompt" in sample and "response" in sample:
        return {"prompt_key": "prompt", "response_key": "response"}
    return {}


def build_demo(dataset_source: str) -> gr.Blocks:
    def list_local_sources() -> List[str]:
        candidates: List[str] = []
        base = Path(__file__).resolve().parents[2] / "data" / "misc"
        if base.exists():
            for ext in ("*.jsonl", "*.json", "*.csv"):
                candidates.extend([str(p) for p in sorted(base.glob(ext))])
        return candidates

    hf_configs = (
        list_hf_configs(dataset_source)
        if is_huggingface_id(dataset_source) and get_dataset_config_names
        else []
    )
    source_choices = [dataset_source] + list_local_sources()
    default_split = "train"

    css = """
    .ribbon {background: linear-gradient(90deg, #ffafbd, #ffc3a0); padding: 10px 16px; border-radius: 10px; display: inline-block;}
    .gradio-container .chatbot {--radius: 14px;}
    #collapse-btn { position: sticky; top: 6px; z-index: 20; align-self: flex-end; }
    #results-acc > summary { position: sticky; top: 0; z-index: 10; background: var(--panel-background-fill); }
    """
    with gr.Blocks(title="Dataset Explorer", css=css) as demo:
        gr.Markdown("## 🎀 Dataset Explorer\nBrowse, search, and preview items. ✨")

        with gr.Row():
            src = gr.Dropdown(
                choices=source_choices,
                value=source_choices[0] if source_choices else dataset_source,
                label="Dataset source (HF id, URL, or local path)",
                allow_custom_value=True,
            )
            config = gr.Dropdown(
                choices=[""] + hf_configs,
                value=(hf_configs[0] if hf_configs else ""),
                label="HF config (optional)",
            )
            split = gr.Dropdown(
                choices=["train", "validation", "test", "unsupervised", "all"],
                value=default_split,
                label="Split",
            )

        with gr.Row():
            keyword = gr.Textbox(label="Keyword (optional)")
            limit = gr.Slider(1, 100, value=10, step=1, label="Max items")
        with gr.Row():
            search_field = gr.Dropdown(choices=[""], value="", label="Search field (optional)", allow_custom_value=True)

        with gr.Row():
            load_btn = gr.Button("Load & Search")
            random_btn = gr.Button("Random Item")
        results_open = gr.State(True)
        collapse_btn = gr.Button("Collapse Results", elem_id="collapse-btn", variant="secondary")
        with gr.Accordion("Search Results", open=True, elem_id="results-acc") as acc:
            out = gr.Markdown()

        with gr.Row():
            item_id = gr.Textbox(label="Item id/index (optional)")
            chat_btn = gr.Button("View as Chat 💬")
        chat = gr.Chatbot(height=420, type="tuples")

        def detect_fields_from_sample(sample: Dict[str, Any]) -> List[str]:
            try:
                return list(sample.keys())
            except Exception:
                return []

        def get_first_record(_src: str, _config: str, _split: str) -> Dict[str, Any]:
            if is_huggingface_id(_src) and load_dataset:
                try:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    return ds[0] if len(ds) > 0 else {}
                except Exception:
                    return {}
            # files
            try:
                if _src.endswith(".csv"):
                    df = pd.read_csv(_src, nrows=1)
                    return df.iloc[0].to_dict() if not df.empty else {}
                if _src.endswith(".jsonl"):
                    first = next((l for l in Path(_src).read_text(encoding="utf-8").splitlines() if l.strip()), None)
                    return json.loads(first) if first else {}
                # json array
                arr = json.loads(Path(_src).read_text(encoding="utf-8"))
                return arr[0] if isinstance(arr, list) and arr else (arr if isinstance(arr, dict) else {})
            except Exception:
                return {}

        def on_src_change(_src: str, _config: str, _split: str):
            # Refresh config list for HF ids; disable for files
            if is_huggingface_id(_src) and get_dataset_config_names:
                cfgs = list_hf_configs(_src)
                sample = get_first_record(_src, (cfgs[0] if cfgs else _config), _split)
                fields = detect_fields_from_sample(sample)
                return (
                    gr.update(choices=[""] + cfgs, value=(cfgs[0] if cfgs else ""), interactive=True),
                    gr.update(choices=[""] + fields, value="")
                )
            else:
                sample = get_first_record(_src, _config, _split)
                fields = detect_fields_from_sample(sample)
                return (
                    gr.update(choices=[""], value="", interactive=False),
                    gr.update(choices=[""] + fields, value="")
                )

        def fetch_slice(_src: str, _config: str, _split: str, _kw: str, _limit: int, _field: str):
            try:
                # Load HF dataset or fallback to local/remote files
                if is_huggingface_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    if hasattr(ds, "select"):
                        head_n = min(_limit * 50, len(ds)) if len(ds) else _limit * 50
                        rows = ds.select(range(head_n))
                        rows = [rows[i] for i in range(min(head_n, len(rows)))]
                    else:
                        rows = list(ds.take(_limit * 50))
                else:
                    if _src.endswith(".csv"):
                        df = pd.read_csv(_src)
                        rows = df.to_dict(orient="records")
                    elif _src.endswith(".jsonl"):
                        rows = [
                            json.loads(l)
                            for l in Path(_src).read_text(encoding="utf-8").splitlines()
                        ]
                    else:
                        rows = json.loads(Path(_src).read_text(encoding="utf-8"))

                kw = (_kw or "").lower()
                out_rows: List[Dict[str, Any]] = []
                for r in rows:
                    if _field and isinstance(r, dict) and _field in r:
                        text = json.dumps(r.get(_field), ensure_ascii=False).lower()
                    else:
                        text = json.dumps(r, ensure_ascii=False).lower()
                    if kw and kw not in text:
                        continue
                    out_rows.append(r)
                    if len(out_rows) >= _limit:
                        break
                md = "\n\n---\n\n".join(
                    ["```json\n" + json.dumps(r, ensure_ascii=False, indent=2) + "\n```" for r in out_rows]
                )
                return md or "No matches.", gr.update(open=True), gr.update(value="Collapse Results"), True
            except Exception as e:  # pragma: no cover - runtime UX
                return f"Load error: {e}", gr.update(), gr.update(), True

        def random_item(_src: str, _config: str, _split: str):
            try:
                if is_huggingface_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    if len(ds) == 0:
                        return "No data."
                    idx = random.randint(0, len(ds) - 1)
                    r = ds[int(idx)]
                else:
                    if _src.endswith(".csv"):
                        df = pd.read_csv(_src)
                        if df.empty:
                            return "No data."
                        r = df.sample(1).to_dict(orient="records")[0]
                    elif _src.endswith(".jsonl"):
                        lines = Path(_src).read_text(encoding="utf-8").splitlines()
                        if not lines:
                            return "No data."
                        r = json.loads(random.choice(lines))
                    else:
                        arr = json.loads(Path(_src).read_text(encoding="utf-8"))
                        if not arr:
                            return "No data."
                        r = random.choice(arr)
                return "```json\n" + json.dumps(r, ensure_ascii=False, indent=2) + "\n```", gr.update(open=True), gr.update(value="Collapse Results"), True
            except Exception as e:  # pragma: no cover - runtime UX
                return f"Random error: {e}", gr.update(), gr.update(), True

        def _parse_misc_chat(rec: Dict[str, Any]) -> List[Tuple[str, str]]:
            # MiSC-specific heuristic: combine all *_session_dialogue turns
            # Format observed: "first_session_dialogue": [[speaker_names...], [utterances...]]
            main_speaker = rec.get("main_speaker")
            if not main_speaker:
                sl = rec.get("speaker_list")
                if isinstance(sl, list) and sl:
                    main_speaker = sl[0]

            def session_keys() -> List[str]:
                keys = [k for k in rec.keys() if isinstance(rec.get(k), list) and "dialogue" in k.lower()]
                # stable natural order: first, second, third... fallback to alpha
                order = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}
                def key_rank(k: str) -> int:
                    for name, idx in order.items():
                        if name in k.lower():
                            return idx
                    return 999
                return sorted(keys, key=lambda k: (key_rank(k), k))

            history: List[Tuple[str, str]] = []
            for k in session_keys():
                sess = rec.get(k)
                if not isinstance(sess, list):
                    continue
                # Case A: [[speakers...], [utterances...]]
                if len(sess) == 2 and all(isinstance(x, list) for x in sess):
                    speakers_seq, utt_seq = sess[0], sess[1]
                    for spk, utt in zip(speakers_seq, utt_seq):
                        text = utt if isinstance(utt, str) else json.dumps(utt, ensure_ascii=False)
                        spk_name = str(spk)
                        if main_speaker and spk_name == main_speaker:
                            history.append((text, ""))
                        else:
                            if not history:
                                history.append(("", text))
                            else:
                                u, a = history[-1]
                                history[-1] = (u, text) if a == "" else history[-1]
                                if a != "":
                                    history.append(("", text))
                # Case B: list of {speaker, text}
                elif all(isinstance(x, dict) for x in sess):
                    for m in sess:
                        spk_name = str(m.get("speaker") or m.get("role") or m.get("from") or "")
                        text = m.get("text") or m.get("content") or m.get("value") or ""
                        if main_speaker and spk_name == main_speaker:
                            history.append((text, ""))
                        else:
                            if not history:
                                history.append(("", text))
                            else:
                                u, a = history[-1]
                                history[-1] = (u, text) if a == "" else history[-1]
                                if a != "":
                                    history.append(("", text))
                # else: ignore unknown shapes
            return history

        def view_chat(_src: str, _config: str, _split: str, _id: str):
            try:
                if is_huggingface_id(_src) and load_dataset:
                    ds = load_hf_dataset(_src, _config or None, _split, streaming=False)
                    sample = ds[0] if len(ds) > 0 else {}
                    meta = guess_conversation(sample if isinstance(sample, dict) else {})
                    if _id and _id.isdigit():
                        rec = ds[int(_id)]
                    elif _id:
                        rec = next((r for r in ds if str(r.get("id", "")) == _id), ds[0])
                    else:
                        rec = ds[0] if len(ds) > 0 else {}
                else:
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
                    meta = guess_conversation(sample if isinstance(sample, dict) else {})

                history: List[Tuple[str, str]] = []
                # Try MiSC-specific parsing first
                misc_hist = _parse_misc_chat(rec if isinstance(rec, dict) else {})
                if misc_hist:
                    return misc_hist
                if "container_key" in meta:
                    seq = rec.get(meta["container_key"], []) if isinstance(rec, dict) else []
                    for m in seq:
                        if not isinstance(m, dict):
                            # Fallback for raw strings
                            history.append((str(m), ""))
                            continue
                        role = (m.get("role") or m.get("from") or m.get("speaker") or "").lower()
                        content = (
                            m.get("content")
                            or m.get("value")
                            or m.get("text")
                            or m.get("utterance")
                            or ""
                        )
                        if role in ("user", "human"):
                            history.append((content, ""))
                        elif role in ("assistant", "system", "gpt", "bot"):
                            if not history:
                                history.append(("", content))
                            else:
                                user_text, assistant_text = history[-1]
                                if assistant_text == "":
                                    history[-1] = (user_text, content)
                                else:
                                    history.append(("", content))
                        else:
                            # Unknown role: treat as user to keep sequence moving
                            history.append((content, ""))
                elif "prompt_key" in meta:
                    history.append((rec.get(meta["prompt_key"], ""), rec.get(meta["response_key"], "")))
                else:
                    history.append((json.dumps(rec, ensure_ascii=False)[:2000], ""))
                return history
            except Exception as e:  # pragma: no cover - runtime UX
                return [(f"Chat error: {e}", "")]

        def toggle_results(open_state: bool):
            new_open = not bool(open_state)
            return new_open, gr.update(open=new_open), gr.update(value=("Collapse Results" if new_open else "Expand Results"))

        src.change(on_src_change, inputs=[src, config, split], outputs=[config, search_field])
        load_btn.click(
            fetch_slice,
            inputs=[src, config, split, keyword, limit, search_field],
            outputs=[out, acc, collapse_btn, results_open],
        )
        random_btn.click(
            random_item,
            inputs=[src, config, split],
            outputs=[out, acc, collapse_btn, results_open],
        )
        collapse_btn.click(
            toggle_results,
            inputs=[results_open],
            outputs=[results_open, acc, collapse_btn],
        )
        chat_btn.click(view_chat, inputs=[src, config, split, item_id], outputs=[chat])

    return demo


if __name__ == "__main__":
    demo = build_demo(DATASET_LINK)
    demo.queue().launch()


