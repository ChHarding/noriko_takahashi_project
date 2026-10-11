# HTML
Website development (simple design)
Report A focused on the backend system (how to save logs), and Report B focused on the interface.
I think the next #TODO is to develop the actual instructional content.
I also need to change when the logs are sent to the feedback system. I no longer need conditions for when to send the logs. Instead, all logs will be sent at once when users finish an item (i.e., when they click "Done").

# ITS Module 1 UI framework
Open `index.html` in a browser. No installation required for this UI-only scaffold.
The black 60:40 interface and preview navigation are implemented. Instructional content, item selection, sentence highlighting, rule-based feedback, experimental condition assignment, Python endpoints, logging, and knowledge-check scoring are **TODO** items, not working features.

## Planned backend
- `GET /api/module/1`: supply public instructional and assessment item content (no answer keys).
- `POST /api/feedback`: evaluate a submitted practice answer and return item-specific feedback at the appropriate release time.
- Backend-controlled experimental assignment, response logging, and independent knowledge-check scoring.

`// TODO:` comments in `index.html` mark implementation points.
