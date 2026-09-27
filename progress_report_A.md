# Version 1 progress report A

I have a first version of my synthesis writing feedback project. It loads two fictional sources about AI monitoring in schools and collects writing one sentence at a time. The focus at this stage is the program flow and feedback timing, rather than feedback accuracy.

The current version runs in the terminal and saves writing, feedback, and revisions as JSON. Demo mode uses predefined feedback. Connecting and testing a free LLM API is still a TODO.
How to test
1. Run python3 main.py in the project folder.
2. When asked to choose demo or api, type demo.
3. Enter: The pilot included 1,200 students. The program will display simulated feedback correcting the number to 120.
4. Type REVISE 1, then enter: The pilot included 120 students.
5. Type DONE to finish the idea, then END to finish the session.
6. Check the JSON file in sessions/ for the writing, feedback, and before/after revision.
Next steps
I plan to build a webpage using HTML, CSS, JavaScript, and Flask. Immediate feedback will highlight the relevant text and have Ignore / Revise buttons. Students can revise directly by deleting and replacing words. The system will record their button choices and actual text changes.
I will also connect a free LLM API and add delayed feedback when the student finishes an idea.

