"""SourceWrite course-project demonstration. Run: streamlit run main.py"""
import json
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
/* Keep all answer-choice labels left aligned, including selected choices. */
.stButton > button {text-align:left!important;justify-content:flex-start!important}
.stButton > button p {text-align:left!important;width:100%!important}
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
      instruction_answer='', instruction_sent=[False]*3, instruction_positions=[0]*3, instruction_responses=[{} for _ in range(3)], completed=False, test_answers={})
    track('session_started')

def track(name,**details):
    log_event(st.session_state.pid,st.session_state.condition,name,**details)

def go(view):
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
    st.rerun()

def answer_key(item):
    if item['kind']=='sentence':return f"Sentence {item['correct_sentence']}"
    return f"Paragraph {item['correct_paragraph']}, Sentence {item['correct_sentence']}"

def selected_correct(item):
    s=st.session_state
    if item['kind']=='sentence':return s.selection==item['correct_sentence']
    return s.selection==item['correct_paragraph'] and s.sentence==item['correct_sentence']

def select_buttons(title,options,selected,key_prefix,disabled=False):
    st.markdown('**'+title+'**')
    for i,text in enumerate(options,1):
        label=f'{i}. {text}'
        if st.button(label,key=f'{key_prefix}_{i}',use_container_width=True,
                     type='primary' if selected==i else 'secondary', disabled=disabled):
            return i
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
    if st.button('Instruction',use_container_width=True,type='primary' if s.view=='instruction' else 'secondary',disabled=s.completed):go('instruction')
with cols[1]:
    if st.button('Practice Items',use_container_width=True,type='primary' if s.view=='practice' else 'secondary',disabled=not s.instruction_done[s.part] or s.completed):go('practice')
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
            st.subheader('Example: ' + step['title'])
            st.write(step['text'])
        elif kind == 'explanation':
            st.markdown('**Instructor explanation**')
            st.write(step['text'])
        elif kind == 'question':
            st.divider()
            st.markdown('**Question**')
            st.write(step['question'])
            if i < pos:
                saved = responses[i]
                st.markdown('**Your answer:** ' + saved['display'])
                st.markdown('**AI tutor:** ' + saved['reply'])
            elif i == pos:
                if i in responses:
                    saved = responses[i]
                    st.markdown('**Your answer:** ' + saved['display'])
                    st.markdown('**AI tutor:** ' + saved['reply'])
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
                        key = st.secrets.get('GROQ_API_KEY', '')
                        if not key:
                            st.error('GROQ_API_KEY is missing from Streamlit secrets.')
                            st.stop()
                        check = dict(step)
                        check['guidance'] = step.get('guidance','')
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
                        responses[i] = {'display':display,'reply':reply,'selection':choice,'reason':answer}
                        track('instruction_answer',part=s.part+1,step=i,answer=display)
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
    if not s.submitted:
        if s.condition in (3,4):
            s.reasoning=st.text_area('Why did you choose this answer?',value=s.reasoning,key=f'reason_{item["id"]}',height=110)
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
        st.subheader('Answer and feedback')
        st.markdown('**Your choice:** '+(f'Sentence {s.selection}' if item['kind']=='sentence' else f'Paragraph {s.selection}, Sentence {s.sentence}'))
        st.markdown('**Your answer:** '+('Correct' if selected_correct(item) else 'Incorrect'))
        st.markdown('**Correct answer:** '+answer_key(item))
        if s.condition in (2,3,4):
            st.markdown('**Reason:** '+item['reason'])
        if s.condition==4:
            st.markdown('**Feedback on your explanation:** '+s.get('personalized',''))
        if st.button('Next Item',type='primary',key=f'next_{item["id"]}'):
            next_item()

elif s.view=='test':
    st.title('Knowledge Test')
    st.write('Complete all questions, then click Submit at the bottom. No answers or feedback will be shown.')
    with st.form('knowledge_test_form'):
        for i,item in enumerate(COURSE['test'],1):
            st.subheader(f'Question {i}')
            st.write(item['question'])
            if item['kind']=='mc':
                s.test_answers[item['id']]=st.selectbox('Choose an answer', ['— Select —']+item['options'],key='test_'+item['id'])
            elif item['kind']=='sentence':
                for j,sentence in enumerate(item['sentences'],1):st.write(f'{j}. {sentence}')
                s.test_answers[item['id']]=st.selectbox('Main sentence',['— Select —']+list(range(1,len(item['sentences'])+1)),key='test_'+item['id'])
            else:
                for j,para in enumerate(item['paragraphs'],1):st.write(f'**Paragraph {j}.** {para}')
                para=st.selectbox('Main paragraph',['— Select —',1,2,3],key='test_para_'+item['id'])
                sentence=st.selectbox('Main sentence',['— Select —',1,2,3,4,5,6,7,8],key='test_sent_'+item['id'])
                s.test_answers[item['id']]={'paragraph':para,'sentence':sentence}
            st.divider()
        submitted=st.form_submit_button('Submit Knowledge Test',type='primary')
    if submitted:
        def complete(v):return all(x!='— Select —' for x in v.values()) if isinstance(v,dict) else v!='— Select —'
        if not all(complete(x) for x in s.test_answers.values()):
            st.warning('Please answer every question before submitting.')
        else:
            track('knowledge_test_submitted',answers=dict(s.test_answers))
            s.completed=True;track('module_completed');st.rerun()
