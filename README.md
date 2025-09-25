## Dataset Explorers Monorepo

Gradio apps for exploring datasets, one folder per dataset under `apps/`.

What’s here
- `apps/multiwoz/`: MultiWOZ 2.2 explorer (search, filters, and chat view)
- `docs/cursor_prompt.md`: step-by-step prompt to create another app identical in UI, changing only the dataset link

How to run an app
- See the app’s own README, e.g. `apps/multiwoz/README.md`.

Add a new app (one at a time)
1. Pick `DATASET_LINK` (HF id or CSV/JSON URL) and `DATASET_SLUG` (folder name)
2. Follow `docs/cursor_prompt.md` to copy the MultiWOZ UI and wire loaders to your link
3. Place code in `apps/<DATASET_SLUG>/` with `app.py`, `requirements.txt`, `README.md`
4. Commit only the `apps/<DATASET_SLUG>/` folder and push

Monorepo structure
```
apps/
  multiwoz/
    app.py
    requirements.txt
    README.md
docs/
  cursor_prompt.md
.gitignore
```

Pushing to GitHub (same repo)
```bash
git add apps/<DATASET_SLUG>
git commit -m "feat(apps/<DATASET_SLUG>): add Gradio explorer for <DATASET_LINK>"
git push
```

Note from the author
- Built with love for Socrates — my boyfriend and the love of my life 💖



