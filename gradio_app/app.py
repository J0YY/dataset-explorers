import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gradio as gr


def get_data_root() -> Path:
	current_file_path: Path = Path(__file__).resolve()
	workspace_root: Path = current_file_path.parents[1]
	return workspace_root / "multiwoz" / "data" / "MultiWOZ_2.2"


DATA_ROOT: Path = get_data_root()
SCHEMA_PATH: Path = DATA_ROOT / "schema.json"


def read_json(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as f:
		return json.load(f)


def load_services_from_schema(schema_path: Path) -> List[str]:
	schema: List[Dict] = read_json(schema_path)
	return [service["service_name"] for service in schema]


def list_shards(split: str) -> List[Path]:
	split_dir: Path = DATA_ROOT / split
	shards: List[Path] = sorted(split_dir.glob("dialogues_*.json"))
	return shards


def load_dialogues_from_shard(shard_path: Path) -> List[Dict]:
	data: List[Dict] = read_json(shard_path)
	return data


def list_dialogue_ids_from_shard(shard_path: Path) -> List[str]:
	data: List[Dict] = load_dialogues_from_shard(shard_path)
	return [d.get("dialogue_id", "<unknown>") for d in data]


def format_dialogue_markdown(dialogue: Dict) -> str:
	dialogue_id: str = dialogue.get("dialogue_id", "<unknown>")
	services: List[str] = dialogue.get("services", [])
	turns: List[Dict] = dialogue.get("turns", [])

	lines: List[str] = []
	lines.append(f"### {dialogue_id}")
	if services:
		lines.append(f"Services: {', '.join(services)}")
	lines.append("")
	for turn in turns:
		speaker: str = turn.get("speaker", "?")
		utterance: str = turn.get("utterance", "")
		lines.append(f"**{speaker}**: {utterance}")
	return "\n".join(lines)


def filter_dialogues(
	dialogues: List[Dict],
	service_filter: Optional[str],
	keyword: Optional[str],
	limit: int,
) -> Tuple[List[Dict], List[str]]:
	service_filter_lower: Optional[str] = service_filter.lower() if service_filter else None
	keyword_lower: Optional[str] = keyword.lower() if keyword else None

	filtered: List[Dict] = []
	for dlg in dialogues:
		services: List[str] = [s.lower() for s in dlg.get("services", [])]
		if service_filter_lower and service_filter_lower not in services:
			continue
		if keyword_lower:
			text_joined: str = "\n".join(
				turn.get("utterance", "") for turn in dlg.get("turns", [])
			).lower()
			if keyword_lower not in text_joined:
				continue
		filtered.append(dlg)
		if len(filtered) >= limit:
			break

	markdown_chunks: List[str] = [format_dialogue_markdown(d) for d in filtered]
	return filtered, markdown_chunks


def ui_update_shards(split: str) -> Tuple[List[str], str]:
	shards: List[Path] = list_shards(split)
	choices: List[str] = [p.name for p in shards]
	default_choice: str = choices[0] if choices else ""
	return choices, default_choice


def ui_load_and_search(
	split: str,
	shard_filename: str,
	service_filter: Optional[str],
	keyword: Optional[str],
	limit: int,
) -> str:
	if not split:
		return "Please select a split."
	available_shards: List[Path] = list_shards(split)
	if not available_shards:
		return f"No shards found for split '{split}'."

	if shard_filename:
		shard_path_candidates: List[Path] = [
			p for p in available_shards if p.name == shard_filename
		]
		shard_path: Path = shard_path_candidates[0] if shard_path_candidates else available_shards[0]
	else:
		shard_path = available_shards[0]

	try:
		dialogues: List[Dict] = load_dialogues_from_shard(shard_path)
	except Exception as e:
		return f"Failed to load shard {shard_path.name}: {e}"

	_, markdown_chunks = filter_dialogues(dialogues, service_filter, keyword, limit)
	if not markdown_chunks:
		return "No matching dialogues. Try a different shard, domain, or keyword."
	return "\n\n---\n\n".join(markdown_chunks)


def ui_random_dialogue() -> str:
	split_choice: str = random.choice(["train", "dev", "test"])
	shards: List[Path] = list_shards(split_choice)
	if not shards:
		return "No shards available."
	shard_path: Path = random.choice(shards)
	try:
		dialogues: List[Dict] = load_dialogues_from_shard(shard_path)
	except Exception as e:
		return f"Failed to load shard {shard_path.name}: {e}"
	if not dialogues:
		return "Shard has no dialogues."
	dialogue: Dict = random.choice(dialogues)
	return format_dialogue_markdown(dialogue)


def ui_update_dialogue_ids(split: str, shard_filename: str) -> Tuple[List[str], str]:
	if not split:
		return [], ""
	available_shards: List[Path] = list_shards(split)
	if not available_shards:
		return [], ""
	if shard_filename:
		candidates: List[Path] = [p for p in available_shards if p.name == shard_filename]
		shard_path: Path = candidates[0] if candidates else available_shards[0]
	else:
		shard_path = available_shards[0]
	ids: List[str] = list_dialogue_ids_from_shard(shard_path)
	default_id: str = ids[0] if ids else ""
	return ids, default_id


def ui_view_dialogue_as_chat(split: str, shard_filename: str, dialogue_id: str) -> List[Tuple[str, str]]:
	if not split:
		return []
	available_shards: List[Path] = list_shards(split)
	if not available_shards:
		return []
	if shard_filename:
		candidates: List[Path] = [p for p in available_shards if p.name == shard_filename]
		shard_path: Path = candidates[0] if candidates else available_shards[0]
	else:
		shard_path = available_shards[0]
	try:
		dialogues: List[Dict] = load_dialogues_from_shard(shard_path)
	except Exception:
		return []
	selected: Optional[Dict] = None
	for d in dialogues:
		if d.get("dialogue_id") == dialogue_id:
			selected = d
			break
	if not selected:
		return []
	turns: List[Dict] = selected.get("turns", [])
	# Build list of (user, system) pairs for Chatbot
	history: List[Tuple[str, str]] = []
	current_user: Optional[str] = None
	for t in turns:
		speaker: str = t.get("speaker", "")
		utt: str = t.get("utterance", "")
		if speaker.upper() == "USER":
			# Flush prior user if unmatched
			if current_user is not None:
				history.append((current_user, ""))
			current_user = utt
		elif speaker.upper() == "SYSTEM":
			if current_user is None:
				# If system speaks first, show as assistant-only bubble
				history.append(("", utt))
			else:
				history.append((current_user, utt))
				current_user = None
		else:
			# Unknown speaker: append as assistant bubble
			history.append(("", utt))
	# Trailing user message without system reply
	if current_user is not None:
		history.append((current_user, ""))
	return history


def build_demo() -> gr.Blocks:
	services: List[str] = load_services_from_schema(SCHEMA_PATH)
	# Pre-compute initial shard list for the default split to avoid invalid state
	_initial_choices, _initial_default = ui_update_shards("train")
	# Cute CSS accents and bubble styling
	cute_css = """
	.ribbon {position: relative; background: linear-gradient(90deg, #ffafbd, #ffc3a0); color: #222; padding: 10px 16px; border-radius: 10px; display: inline-block;}
	.ribbon::after {content: ""; position: absolute; right: -12px; top: 50%; transform: translateY(-50%); width: 0; height: 0; border-top: 12px solid transparent; border-bottom: 12px solid transparent; border-left: 12px solid #ffc3a0;}
	.gradio-container .chatbot {--radius: 14px;}
	.gradio-container .message.user {background: #e9f5ff;}
	.gradio-container .message.bot {background: #fef3ff;}
	"""
	with gr.Blocks(title="MultiWOZ 2.2 Explorer", css=cute_css) as demo:
		gr.Markdown(
			"""
			## 🎀 MultiWOZ 2.2 Explorer
			Browse and search dialogues from the MultiWOZ dataset. ✨
			"""
		)

		with gr.Row():
			split = gr.Dropdown(
				label="Split",
				choices=["train", "dev", "test"],
				value="train",
			)
			shard = gr.Dropdown(
				label="Shard file (dialogues_XXX.json)",
				choices=_initial_choices,
				value=_initial_default,
			)

		with gr.Row():
			service = gr.Dropdown(
				label="Domain (optional)",
				choices=[""] + services,
				value="",
			)
			keyword = gr.Textbox(label="Keyword (optional)")
			limit = gr.Slider(
				label="Max dialogues",
				minimum=1,
				maximum=50,
				value=5,
				step=1,
			)

		with gr.Row():
			load_btn = gr.Button("Load & Search")
			random_btn = gr.Button("Random Dialogue")

		output = gr.Markdown()

		# Dialogue picker + Chat view
		with gr.Row():
			dialogue_id = gr.Dropdown(label="Dialogue ID (optional)")
			view_btn = gr.Button("View as Chat 💬")

		chat = gr.Chatbot(label="Conversation", height=420, bubble_full_width=False)

		def _on_split_change(selected_split: str):
			choices, default_choice = ui_update_shards(selected_split)
			# Use gr.update to safely update choices/value for existing component
			return gr.update(choices=choices, value=default_choice)

		split.change(_on_split_change, inputs=[split], outputs=[shard])

		def _on_shard_change(selected_split: str, shard_name: str):
			ids, default_id = ui_update_dialogue_ids(selected_split, shard_name)
			return gr.update(choices=ids, value=default_id)

		# Update dialogue-id dropdown whenever split or shard changes
		shard.change(_on_shard_change, inputs=[split, shard], outputs=[dialogue_id])
		split.change(_on_shard_change, inputs=[split, shard], outputs=[dialogue_id])

		load_btn.click(
			ui_load_and_search,
			inputs=[split, shard, service, keyword, limit],
			outputs=[output],
		)
		random_btn.click(ui_random_dialogue, inputs=None, outputs=[output])

		view_btn.click(
			ui_view_dialogue_as_chat,
			inputs=[split, shard, dialogue_id],
			outputs=[chat],
		)

		# No manual mutation needed; shard is initialized above and updated via change handler

	return demo


if __name__ == "__main__":
	demo = build_demo()
	demo.launch()


