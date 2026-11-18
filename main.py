"""SourceWrite course-project demonstration. Run: streamlit run main.py"""
import json
import re
import uuid
from pathlib import Path
import streamlit as st
from logger import log_event
from tutor import instructional_reply, personalized_feedback

st.set_page_config(page_title='SourceWrite ITS', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {background:#0e0e0e;color:#f3f3f3}
/* Extra clearance below Streamlit toolbar so navigation tabs remain visible. */
[data-testid="stMainBlockContainer"], .block-container {max-width:1060px!important;padding-top:7rem!important;padding-bottom:5rem!important}
h1,h2,h3,p,li,label {color:#f2f2f2!important}
.stButton>button {border-radius:5px;min-height:40px}
.stButton>button[kind="primary"] {background:#e6e6e6;color:#151515;border:0}
.stButton>button[kind="secondary"] {background:#222;color:#f0f0f0;border:1px solid #505050}
[data-testid="stProgressBar"] div[role="progressbar"]>div {background:#e5e5e5!important}
[data-testid="stTextArea"] textarea {background:#1d1d1d;color:#fff}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#353535}
hr {border-color:#333}
/* Scope alignment to the answer-choice containers, including selected buttons. */
[class*="st-key-choice_group_"] [data-testid="stButton"] button,
[class*="st-key-choice_group_"] .stButton button {
    display:flex!important;
    justify-content:flex-start!important;
    text-align:left!important;
    padding-left:16px!important;
}
[class*="st-key-choice_group_"] [data-testid="stMarkdownContainer"],
[class*="st-key-choice_group_"] button div,
[class*="st-key-choice_group_"] button p {
    text-align:left!important;
    justify-content:flex-start!important;
    width:100%!important;
    margin-left:0!important;
}
/* Navigation and Done/Next buttons retain their compact alignment. */
.stButton > button[kind="primary"] p {color:#111!important}
.stButton > button[kind="secondary"] p {color:#f0f0f0!important}
</style>''', unsafe_allow_html=True)
COURSE=json.loads((Path(__file__).parent/'modules'/'course.json').read_text(encoding='utf-8'))
PARTS=COURSE['parts']

def init(condition):
    st.session_state.update(pid=str(uuid.uuid4()), condition=condition, started=True,
      part=0, view='instruction', instruction_done=[False]*3, practice_indices=[0]*3,
      submitted=False, selection=None, sentence=None, reasoning='', instruction_reply=None,
      instruction_answer='', instruction_sent=[False]*3, instruction_positions=[0]*3, instruction_responses=[{} for _ in range(3)], completed=False, test_answers={}, test_started=False)
    track('session_started')

def track(name,**details):
    log_event(st.session_state.pid,st.session_state.condition,name,**details)

def go(view):
    if st.session_state.get('test_started') and view != 'test':
        return
    if view == 'test':
        st.session_state.test_started = True
    st.session_state.view=view
    st.rerun()

def next_item():
    s=st.session_state
    s.practice_indices[s.part]+=1
    s.submitted=False;s.selection=None;s.sentence=None;s.reasoning='';s.personalized='' 
    track('next_item',part=s.part+1, index=s.practice_indices[s.part])
    if s.practice_indices[s.part]>=len(PARTS[s.part]['practice']):
        if s.part<2:
            s.part+=1;s.view='instruction'
        else:
            s.view='test'
            s.test_started=True
    st.rerun()

def answer_key(item):
    if item['kind']=='sentence':return f"Sentence {item['correct_sentence']}"
    return f"Paragraph {item['correct_paragraph']}, Sentence {item['correct_sentence']}"

def selected_correct(item):
    s=st.session_state
    if item['kind']=='sentence':return s.selection==item['correct_sentence']
    return s.selection==item['correct_paragraph'] and s.sentence==item['correct_sentence']

def select_buttons(title, options, selected, key_prefix, disabled=False):
    st.markdown('**' + title + '**')
    clicked = None
    # Always create every button, even when one is clicked.
    # Returning inside this loop caused later choices to disappear.
    # Keyed container gives answer choices a stable, targeted CSS selector.
    with st.container(key=f'choice_group_{key_prefix}'):
        for i, text in enumerate(options, 1):
            # The button already supplies the number; remove redundant A/B labels
            # from the Part 2 tornado comparisons.
            display_text = str(text)
            if st.session_state.part == 1 and key_prefix.startswith('instruction_'):
                display_text = re.sub(r'^Option\s+[AB]\.\s*', '', display_text, flags=re.I)
            if st.button(
                f'{i}. {display_text}',
                key=f'{key_prefix}_{i}',
                use_container_width=True,
                type='primary' if selected == i else 'secondary',
                disabled=disabled,
            ):
                clicked = i
    if clicked is not None and clicked != selected:
        # Streamlit reruns the whole page on the next interaction; every choice
        # remains in the tree because we rendered the full loop above.
        return clicked
    return selected

def get_sentences(text):
    import re
    return [x.strip() for x in re.split(r'(?<=[.!?])\s+(?=[A-Z“])',text) if x.strip()]

if not st.session_state.get('started'):
    st.title('SourceWrite')
    st.subheader('Core Intention and the Deletion Test')
    st.write('Learn to identify a text’s main sentence and paragraph through three instructional parts, practice activities, and a final knowledge test.')
    condition=st.selectbox('Demonstration condition', [1,2,3,4], format_func=lambda x:{1:'C1 · Answer only',2:'C2 · Answer + reason',3:'C3 · Explain your choice + answer and reason',4:'C4 · Explain your choice + personalized feedback'}[x])
    if st.button('Start',type='primary'):
        init(condition);st.rerun()
    st.stop()

s=st.session_state
practice_done=sum(min(s.practice_indices[i],len(PARTS[i]['practice'])) for i in range(3))
instruction_done=sum(s.instruction_done)
total=3+sum(len(p['practice']) for p in PARTS)+1
completed=instruction_done+practice_done+int(s.completed)
part=PARTS[min(s.part,2)]
test_unlocked=s.practice_indices[2]>=len(PARTS[2]['practice'])

cols=st.columns([1.15,1.4,1.3,3.0],vertical_alignment='center')
with cols[0]:
    if st.button('Instruction',use_container_width=True,type='primary' if s.view=='instruction' else 'secondary',disabled=s.completed or s.test_started):go('instruction')
with cols[1]:
    if st.button('Practice Items',use_container_width=True,type='primary' if s.view=='practice' else 'secondary',disabled=not s.instruction_done[s.part] or s.completed or s.test_started):go('practice')
with cols[2]:
    if st.button('Knowledge Test' if test_unlocked else '🔒 Knowledge Test',use_container_width=True,type='primary' if s.view=='test' else 'secondary',disabled=not test_unlocked or s.completed):go('test')
with cols[3]:st.caption(f'Condition {s.condition}  ·  Course demonstration')
st.divider()
if s.completed:
    st.title('Thank you for completing the module!')
    st.write('You have completed all three parts and submitted the Knowledge Test.')
    st.stop()

if s.view=='test':
    st.caption('Knowledge Test · All questions')
elif s.view=='instruction':
    st.caption(f'Part {s.part+1} of 3 · Instruction')
else:
    st.caption(f'Part {s.part+1} of 3 · Practice item {min(s.practice_indices[s.part]+1,len(part["practice"]))} of {len(part["practice"])}')
st.progress(completed/total,text=f'Course progress · {completed} of {total} activities completed')

if s.view=='instruction':
    st.title(f'Part {s.part+1}. {part["title"]}')
    st.caption('Read the lesson and respond to the original questions in the instructor document. You can return here from Practice Items.')
    steps = part['instruction_steps']
    pos = s.instruction_positions[s.part]
    # Automatically reveal consecutive reading/explanation steps.
    # Stop only when the next original instructor question requires a response.
    while pos < len(steps) and steps[pos]['type'] != 'question':
        pos += 1
    s.instruction_positions[s.part] = pos
    responses = s.instruction_responses[s.part]
    # Render all completed lesson steps; retain the learner's choices and tutor replies.
    question_index = 0
    for i, step in enumerate(steps):
        if i > pos:
            break
        kind = step['type']
        if kind == 'text':
            st.write(step['text'])
        elif kind == 'example':
            # In Part 3, show the example title once and label each paragraph below it.
            high_school_prefix = 'High School Start Times — Paragraph '
            if s.part == 2 and step['title'].startswith(high_school_prefix):
                paragraph_number = step['title'][len(high_school_prefix):]
                if paragraph_number == '1':
                    st.subheader('Example: High School Start Times')
                st.markdown(f'**Paragraph {paragraph_number}**')
                st.write(step['text'])
            else:
                st.subheader('Example: ' + step['title'])
            if s.part == 1 and step['title'] == 'Tornado Warning':
                # Preserve the four original numbered sentences as separate lines.
                tornado_sentences = [
                    'This is a tornado warning.',
                    'Conditions outside have become dangerous.',
                    'Seek shelter in a sturdy building immediately.',
                    'Do not stop to take any belongings with you.',
                ]
                for number, sentence in enumerate(tornado_sentences, 1):
                    st.markdown(f'**({number})** {sentence}')
            elif not (s.part == 2 and step['title'].startswith(high_school_prefix)):
                st.write(step['text'])
        elif kind == 'explanation':
            st.markdown('**Instructor explanation**')
            st.write(step['text'])
        elif kind == 'question':
            st.divider()
            st.markdown('**Question**')
            st.write(step['question'])
            if i < pos or (i == pos and i in responses):
                saved = responses[i]
                input_type = step['input_type']
                if input_type in ('sentence_reason', 'choice', 'yes_no'):
                    options = step.get('options', ['Yes', 'No'])
                    select_buttons('Your selection', options, saved.get('selection'),
                                   f'instruction_review_{s.part}_{i}', disabled=True)
                if input_type in ('text', 'sentence_reason'):
                    st.text_area(
                        'Why? Explain your answer' if input_type == 'sentence_reason' else 'Your answer',
                        value=saved.get('reason', ''),
                        key=f'instruction_review_text_{s.part}_{i}',
                        height=110, disabled=True
                    )
                correct_choice = step.get('correct_selection')
                if correct_choice is not None:
                    st.markdown('**Your answer:** ' +
                                ('Correct' if saved.get('selection') == correct_choice else 'Incorrect'))
                    options = step.get('options', ['Yes', 'No'])
                    st.markdown('**Correct choice:** ' + options[correct_choice - 1])
                st.markdown('**Instructor explanation:** ' + step.get('expected_answer', ''))
                if saved.get('used_llm', False):
                    st.markdown('**AI tutor feedback:** ' + saved['reply'])
                if i == pos:
                    if st.button('Continue', type='primary', key=f'instruction_continue_{s.part}_{i}'):
                        next_pos = i + 1
                        while next_pos < len(steps) and steps[next_pos]['type'] != 'question':
                            next_pos += 1
                        s.instruction_positions[s.part] = next_pos
                        st.rerun()
            else:
                choice = None
                if step['input_type'] in ('sentence_reason', 'choice', 'yes_no'):
                    opts = step.get('options', ['Yes', 'No'])
                    choice = select_buttons('Select your answer', opts,
                        s.get(f'instruction_choice_{s.part}_{i}'),
                        f'instruction_option_{s.part}_{i}')
                    s[f'instruction_choice_{s.part}_{i}'] = choice
                answer = ''
                if step['input_type'] in ('text', 'sentence_reason'):
                    answer = st.text_area('Why? Explain your answer' if step['input_type']=='sentence_reason' else 'Your answer',
                        key=f'instruction_text_{s.part}_{i}', height=110)
                ready = (choice is not None if step['input_type'] in ('choice','yes_no') else
                         bool(answer.strip()) if step['input_type']=='text' else
                         choice is not None and bool(answer.strip()))
                if st.button('Done', type='primary', disabled=not ready,
                             key=f'instruction_done_{s.part}_{i}'):
                    opts = step.get('options', ['Yes','No'])
                    selected_label = opts[choice-1] if choice is not None else ''
                    display = (f'{selected_label} — {answer}' if choice is not None and answer.strip()
                               else selected_label or answer)
                    # Only typed instructional answers require the LLM.
                    # Choice-only questions use the instructor's predetermined key.
                    needs_llm = step['input_type'] in ('text', 'sentence_reason')
                    if needs_llm:
                        key = st.secrets.get('GROQ_API_KEY', '')
                        if not key:
                            st.error('GROQ_API_KEY is missing from Streamlit secrets.')
                            st.stop()
                        check = dict(step)
                        check['guidance'] = step.get('guidance', '')
                        check['expected_answer'] = step['expected_answer']
                        check['selected_choice'] = selected_label
                        check['correct_selection'] = step.get('correct_selection')
                        with st.spinner('Tutor responding...'):
                            try:
                                reply = instructional_reply(key, part, check, display)
                            except Exception as exc:
                                st.error(f'Tutor unavailable: {type(exc).__name__}: {exc}')
                                st.stop()
                        if not reply.strip():
                            st.error('Tutor returned an empty response. Please try again.')
                            st.stop()
                    else:
                        reply = ''
                    responses[i] = {'display':display,'reply':reply,'selection':choice,'reason':answer,'used_llm':needs_llm}
                    track('instruction_answer',part=s.part+1,step=i,answer=display)
                    if needs_llm:
                        track('instruction_feedback',part=s.part+1,step=i,response=reply)
                    st.rerun()
            question_index += 1
    if pos >= len(steps):
        st.divider()
        st.markdown(f'**AI Tutor:** You have completed Part {s.part+1} instruction. Go to Practice Items and complete the activities. You can return here to reread the instruction and tutor conversations.')
        if st.button('Go to Practice Items', type='primary'):
            if not s.instruction_done[s.part]:
                s.instruction_done[s.part] = True
                track('instruction_completed', part=s.part+1)
            go('practice')

elif s.view=='practice':
    index=s.practice_indices[s.part]
    if index>=len(part['practice']):
        st.success('You completed this part’s practice items.')
        if s.part<2 and st.button('Continue to next instruction',type='primary'):
            s.part+=1;go('instruction')
        elif test_unlocked and st.button('Go to Knowledge Test',type='primary'):go('test')
        st.stop()
    item=part['practice'][index]
    st.title(f'Part {s.part+1} · Practice {index+1} of {len(part["practice"])}')
    st.caption('Select an answer. Click Done to reveal the answer or feedback. Then click Next Item. You cannot go back to previous practice items.')
    if item['kind']=='sentence':
        st.write('Select the sentence that best communicates the author’s core intention.')
        chosen=select_buttons('Select one sentence',item['sentences'],s.selection,item['id'],disabled=s.submitted)
        s.selection=chosen
    else:
        st.write('First select the main paragraph. Then select its main sentence.')
        chosen=select_buttons('Select the main paragraph',item['paragraphs'],s.selection,item['id']+'_para',disabled=s.submitted)
        if chosen!=s.selection:s.sentence=None
        s.selection=chosen
        if chosen is not None:
            sentences=get_sentences(item['paragraphs'][chosen-1])
            s.sentence=select_buttons('Select the main sentence in that paragraph',sentences,s.sentence,item['id']+'_sent',disabled=s.submitted)
    if s.condition in (3,4):
        if s.submitted:
            st.text_area('Why did you choose this answer?', value=s.reasoning,
                         key=f'reason_review_{item["id"]}', height=110, disabled=True)
        else:
            s.reasoning=st.text_area('Why did you choose this answer?',
                                     key=f'reason_{item["id"]}',height=110)
    if not s.submitted:
        ready=s.selection is not None and (item['kind']=='sentence' or s.sentence is not None) and (s.condition not in (3,4) or bool(s.reasoning.strip()))
        if st.button('Done',type='primary',disabled=not ready,key=f'done_{item["id"]}'):
            correct=selected_correct(item)
            track('practice_answer',part=s.part+1,item=item['id'],selection=s.selection,sentence=s.sentence,reasoning=s.reasoning,correct=correct)
            if s.condition==4:
                key=st.secrets.get('GROQ_API_KEY','')
                if not key:st.error('GROQ_API_KEY is required for C4.');st.stop()
                try:
                    with st.spinner('Tutor generating feedback...'):
                        s.personalized=personalized_feedback(key,item,{'paragraph':s.selection,'sentence':s.sentence},s.reasoning,answer_key(item),correct,part)
                except Exception as exc:
                    st.error(f'Feedback unavailable: {exc}');st.stop()
            s.submitted=True
            track('practice_feedback_ready',item=item['id'])
            st.rerun()
    else:
        st.divider()
        correct = selected_correct(item)
        correct_label = answer_key(item)
        # Present one clear, condition-specific response. Streamlit's native
        # success/error containers provide accessible green/red visual cues.
        if correct:
            message = "**Correct!**"
        else:
            message = f"**Incorrect.** The correct answer is **{correct_label}**."

        if s.condition in (2, 3, 4):
            reason = str(item.get('reason', '')).strip()
            if reason:
                message += f"\n\n{reason}"
        if s.condition == 4:
            feedback = str(s.get('personalized', '')).strip()
            if feedback:
                message += f"\n\n**Feedback on your explanation:** {feedback}"

        if correct:
            st.success(message, icon="✅")
        else:
            st.error(message, icon="❌")
        if st.button('Next Item',type='primary',key=f'next_{item["id"]}'):
            next_item()

elif s.view=='test':
    # Entering the test is irreversible: earlier tabs remain locked.
    s.test_started = True
    st.title('Knowledge Test')
    st.write('Answer all questions and click Submit Knowledge Test at the bottom. You cannot return to Instruction or Practice Items. No feedback will be shown.')

    # Native Streamlit buttons cannot be placed in a st.form. Keep the answers
    # in session state so all questions remain visible and editable on reruns.
    for i, item in enumerate(COURSE['test'], 1):
        item_id = item['id']
        st.subheader(f'Question {i}')
        st.write(item['question'])
        saved = s.test_answers.get(item_id)

        if item['kind'] == 'mc':
            selected = select_buttons('Select one answer', item['options'],
                                      saved if isinstance(saved, int) else None,
                                      f'test_mc_{item_id}')
            if selected is not None:
                s.test_answers[item_id] = selected

        elif item['kind'] == 'sentence':
            selected = select_buttons('Select the main sentence', item['sentences'],
                                      saved if isinstance(saved, int) else None,
                                      f'test_sentence_{item_id}')
            if selected is not None:
                s.test_answers[item_id] = selected

        elif item['kind'] == 'paragraph':
            paragraphs = item['paragraphs']
            current = saved if isinstance(saved, dict) else {}
            current_paragraph = current.get('paragraph')
            current_sentence = current.get('sentence')
            chosen_paragraph = select_buttons('Select the main paragraph', paragraphs,
                                               current_paragraph,
                                               f'test_paragraph_{item_id}')
            if chosen_paragraph != current_paragraph:
                current_sentence = None
            if chosen_paragraph is not None:
                sentences = get_sentences(paragraphs[chosen_paragraph - 1])
                chosen_sentence = select_buttons('Select the main sentence in that paragraph',
                                                  sentences, current_sentence,
                                                  f'test_paragraph_sentence_{item_id}')
            else:
                chosen_sentence = None
            s.test_answers[item_id] = {'paragraph': chosen_paragraph,
                                       'sentence': chosen_sentence}

        elif item['kind'] == 'text':
            s.test_answers[item_id] = st.text_area('Type your answer',
                                                   value=saved if isinstance(saved, str) else '',
                                                   key=f'test_text_{item_id}')
        st.divider()

    def answered(item):
        value = s.test_answers.get(item['id'])
        if item['kind'] == 'paragraph':
            return isinstance(value, dict) and value.get('paragraph') is not None and value.get('sentence') is not None
        if item['kind'] == 'text':
            return isinstance(value, str) and bool(value.strip())
        return isinstance(value, int) and value >= 1

    unanswered = [i for i, item in enumerate(COURSE['test'], 1) if not answered(item)]
    if st.button('Submit Knowledge Test', type='primary', key='submit_knowledge_test'):
        if unanswered:
            st.warning('Please complete every question before submitting: ' +
                       ', '.join(f'Question {i}' for i in unanswered))
        else:
            track('knowledge_test_submitted', answers=dict(s.test_answers))
            s.completed = True
            track('module_completed')
            st.rerun()
