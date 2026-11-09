# Research Agent — Gemini free-tier edition

This version uses the Gemini Developer API via its REST interface, so it does not require the Anthropic API or the `anthropic` Python package.

## Setup (Windows)

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then paste it after `GEMINI_API_KEY=` in `.env`. Keep the key private. The default model is `gemini-2.5-flash`; availability and free-tier limits depend on Google's current account, region, and model policies. Do not enable paid billing if you want to stay on the free tier.

Run:

```cmd
python main.py
```

Try:

`Research Chandrayaan-3, calculate days since its launch (July 14, 2023), and save a report.`

Reports are saved in `notes/`. `.env` is excluded by `.gitignore`.
