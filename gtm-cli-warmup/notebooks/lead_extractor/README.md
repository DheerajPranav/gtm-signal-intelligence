# Lead Extractor (Day 2)

Structured lead extraction from unstructured text, with per-field **confidence** and **evidence**.

- `synthetic_inputs.py` — 6 synthetic sources (3 LinkedIn *About* blurbs, 2 email signatures, 1 conference bio) + gold labels.
- `lead_extractor.ipynb` — human-readable demo: extract each sample, show value/confidence/evidence, score enum accuracy vs gold, report cost.
- Model + schema live in `../../src/gtm_cli_warmup/lead.py`.

## Run

```bash
# from the gtm-cli-warmup repo root
.venv/bin/python -m pytest tests/test_lead.py -q     # deterministic proof (no API key needed)

# live demo (needs a real key):
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
.venv/bin/jupyter lab notebooks/lead_extractor/lead_extractor.ipynb   # or: jupyter nbconvert --execute
```

Without a key the notebook still executes end-to-end via a clearly-labelled fixture — it never fabricates
model output. The real correctness gate is `tests/test_lead.py`.
