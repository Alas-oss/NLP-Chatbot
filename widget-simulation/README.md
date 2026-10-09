# Widget simulation

A front-end-only mockup of the proposed e,bedded chatbot widget, for this project. **Scripted demo: has no backends, no API keys, no network calls.** 

## Structure

```
sidget-simulation/
├── index.html    — page structure and content (the mock King's page + the widget markup)
├── styles.css     — all visual design (colours, type, layout, the widget's look)
└── script.js      — all behaviour (the scripted Q&A logic, open/close, DOM wiring)
```

Design, structure and behaviour are kept in separate files, on purpose, so each can be read, reviewed or changed independently of the others.

## Running it

No build step. Either:
- open `index.html` directly in a browser, or
- serve this folder with GitHub Pages (or any static file server)

## Keeping it in sync with the real pipeline

The scripted answers, refusal message, blocked message, and smalltalk handling in `script.js` are written by hand to match the real wording used by the actual chatbot (`config.REFUSAL_MESSAGE`, `config.BLOCKED_MESSAGE`, `src/citations.py`, `src/guards.py`). If that wording changes in the main project, update `SCRIPTED_ANSWERS` and the message constants at the top of `script.js` to match.