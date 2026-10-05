# Version 1 Progress Report A

## description

Version 1 tests real-time writing capture and determines when a sentence should be sent to a future feedback system. The current prototype does not generate feedback. Its purpose is to test the browser-side writing and revision behavior first.

## What has been implemented

A local browser writing interface and Python logging server have been created.

For new writing, a sentence is sent when the writer enters sentence-ending punctuation (`.`, `?`, or `!`).

For revision, the system detects when the writer changes or deletes text in an already completed sentence. The system continues tracking edits to that sentence. When the writer begins editing a different sentence, the previous revision is considered finished and the latest version of that sentence is sent to the server.

All intermediate edits are also logged so that deletion and revision behavior can be reconstructed later.

If the session ends while a revision is active, the current revised sentence is sent before the session closes.


## Next step

The next step is to develop the feedback system that receives the selected sentence and produces source-aware feedback. Feedback highlighting and feedback-linked revision tracking can then be added on top of the current revision logic.
