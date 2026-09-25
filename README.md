# TowerVision AI

Private repository. Only invited collaborators can clone, push, and pull.

## Repository layout

```
tower-vision-ai/
├── backend/            # API server (placeholder - to be built)
├── frontend/           # Web app (placeholder - to be built)
├── ml/
│   └── dataset/        # Dataset inspection, repair, validation scripts
├── scripts/            # Utility scripts (e.g. audit_dataset.py)
├── data/               # LOCAL ONLY - never committed (see Data policy)
├── dataset/            # Local report outputs (ignored by git)
├── docs/               # Documentation
├── models/             # Model weights (ignored by git)
├── outputs/            # Generated outputs (ignored by git)
├── tests/              # Tests
├── requirements.txt    # Python dependencies
└── .gitignore
```

## First-time setup

Requires Git and Python 3.10+.

```powershell
git clone https://github.com/Gnani66/tower-vision-ai.git
cd tower-vision-ai

python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Verify the environment:

```powershell
python -c "import fastapi, cv2, pandas, ultralytics; print('environment ok')"
```

## Data policy

`data/` is about 4 GB (raw images, benchmark images, train/val/test splits) and is
**intentionally excluded from git**. After cloning you will not have it.

- Never force-add files under `data/` (`git add -f data/...`).
- Rebuild dataset artifacts locally with the scripts in `ml/dataset/`, for example:

```powershell
python ml\dataset\inspect_images.py
python ml\dataset\repair_boundary_annotations.py
python ml\dataset\validate_annotations.py
python ml\dataset\create_dataset_split.py
```

- Share large data with teammates through Drive/another file host, not through git.
- If you add files larger than ~50 MB, keep them out of the repo.

## Backend

`backend/` is an empty placeholder on purpose. Put your FastAPI app there
(`requirements.txt` already includes `fastapi` and `uvicorn`), and document how to
run it in this README once it exists.

## Frontend

`frontend/` is an empty placeholder on purpose. Choose the stack, add the project
files, and document install/run commands here:

```powershell
# example - replace once the stack is chosen
cd frontend
npm install
npm run dev
```

## Git workflow (team)

The repository is private. Only collaborators listed under
**GitHub → Settings → Collaborators** can push and pull.

Always work on a branch, never directly on `main`:

```powershell
git pull origin main                 # start from latest
git checkout -b feature/your-name    # e.g. feature/anita-login

# ... make changes ...

git add <files you changed>
git commit -m "short description of the change"
git push -u origin feature/your-name
```

Then open a Pull Request on GitHub and get it reviewed before merging into `main`.

Keep commits clean:

- Never commit `.venv/`, `data/`, `*.env`, model weights, or editor settings.
- Check `git status` and `git diff` before every commit.
- Pull before starting work and resolve conflicts immediately.

### Adding a collaborator

Owner: **GitHub → repo → Settings → Collaborators → Add people**, then accept the
invitation on the collaborator's side.

## Reports

Script outputs (CSV/JSON reports, contact sheets) are written under `data/reports/`
and are not committed. Share them separately if a teammate needs them.
