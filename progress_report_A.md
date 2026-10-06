# Version 1 Progress Report A
The code was generated with ChatGPT using specific instructions for the system behavior. For example, I specified rules such as, “If the input includes ., ?, or !, treat it as a completed sentence and send it to the server.” I used ChatGPT mainly because I am not very familiar with JavaScript. However, I inspected the generated code line by line to make sure I understood the logic and that each part was necessary for the current version.

## description

Version 1 tests real-time writing capture and determines when a sentence should be sent to a future feedback system. The current prototype does not generate feedback. Its purpose is to test the browser-side writing and revision behavior first.

## What has been implemented

A local browser writing interface and Python logging server have been created.

For new writing, a sentence is sent when the writer enters sentence-ending punctuation (`.`, `?`, or `!`).

For revision, the system detects when the writer changes or deletes text in an already completed sentence. The system continues tracking edits to that sentence. When the writer begins editing a different sentence, the previous revision is considered finished and the latest version of that sentence is sent to the server.

All intermediate edits are also logged so that deletion and revision behavior can be reconstructed later.

If the session ends while a revision is active, the current revised sentence is sent before the session closes.

## Files

- `main.py` — local Python server.
- `static/index.html` — writing interface and JavaScript behavior detection.
- `sessions/` — Each session is saved as JSON.

## Run

From the project folder:

```bash
python3 main.py
```

Then open:

```text
http://localhost:8000
```

## Next step

The next step is to develop the feedback system that receives the selected sentence and produces source-aware feedback. Feedback highlighting and feedback-linked revision tracking can then be added on top of the current revision logic.
