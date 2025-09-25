## Apps folder

This monorepo hosts multiple Gradio dataset explorer apps under `apps/<dataset_slug>/`.

Conventions
- Each app folder contains at minimum:
  - `app.py`: the Gradio UI and dataset loaders
  - `requirements.txt`: app-specific dependencies
  - `README.md`: short run instructions and what to expect
- Keep dataset sources and large artifacts out of git. Use runtime download/streaming.

Adding a new app
1. Create `apps/<dataset_slug>/`
2. Add `requirements.txt` and `app.py`
3. Document run steps in `README.md`
4. Test locally (`python app.py`)
5. Commit and push


