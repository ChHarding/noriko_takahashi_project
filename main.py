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
.block-container {max-width:1060px;padding-top:2rem;padding-bottom:5rem}
h1,h2,h3,p,li,label {color:#f2f2f2!important}
.stButton>button {border-radius:5px;min-height:40px}
.stButton>button[kind="primary"] {background:#e6e6e6;color:#151515;border:0}
.stButton>button[kind="secondary"] {background:#222;color:#f0f0f0;border:1px solid #505050}
[data-testid="stProgressBar"] div[role="progressbar"]>div {background:#e5e5e5!important}
[data-testid="stTextArea"] textarea {background:#1d1d1d;color:#fff}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#353535}
hr {border-color:#333}
div.stButton > button[kind="primary"] {background-color: #FFFFFF !important;color: #111111 !important;border: 1px solid #FFFFFF !important;}
div.stButton > button[kind="primary"]:hover,
div.stButton > button[kind="primary"]:focus {background-color: #E5E5E5 !important;color: #111111 !important;border-color: #E5E5E5 !important;}
div.stButton > button[kind="primary"] p {color: #111111 !important;}
div.stButton > button[kind="primary"]:disabled {background-color: #555555 !important;color: #BBBBBB !important;border-color: #555555 !important;}
[data-testid="stMainBlockContainer"] {padding-top: 7rem !important;
</style>''', unsafe_allow_html=True)
COURSE=json.loads((Path(__file__).parent/'modules'/'course.json').read_text(encoding='utf-8'))
PARTS=COURSE['parts']

def init(condition):
    st.session_state.update(pid=str(uuid.uuid4()), condition=condition, started=True,
      part=0, view='instruction', instruction_positions=[0, 0, 0], instruction_responses=[[], [], []], 
      instruction_waiting=[False, False, False],instruction_done=[False]*3, practice_indices=[0]*3,
      submitted=False, selection=None, sentence=None, reasoning='', instruction_reply=None,
      instruction_answer='', instruction_sent=[False]*3, completed=False, test_answers={})
    track('session_started')

def track(name,**details):
    log_event(st.session_state.pid,st.session_state.condition,name,**details)

def go(view):
    st.session_state.view=view
    st.rerun()

def next_item():
    s=st.session_state
    s.practice_indices[s.part]+=1
    s.submitted=False;s.selection=None;s.sentence=None;s.reasoning=''
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

def select_buttons(title,options,selected,key_prefix):
    st.markdown('**'+title+'**')
    for i,text in enumerate(options,1):
        label=f'{i}. {text}'
        if st.button(label,key=f'{key_prefix}_{i}',use_container_width=True,
                     type='primary' if selected==i else 'secondary'):
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


if s.view == 'instruction':
    st.title(f'Part {s.part+1}. {part["title"]}')

    st.write(
        "Read the instruction and answer the tutor's questions. "
        "You can return here from Practice Items to review."
    )

    checks = part.get("instruction_checks", [])
    position = s.instruction_positions[s.part]
    responses = s.instruction_responses[s.part]

    # Display instructional text progressively.
    visible_paragraphs = len(part["instruction"])

    if position < len(checks):
        visible_paragraphs = checks[position]["after_paragraph"] + 1

    for i, paragraph in enumerate(
        part["instruction"][:visible_paragraphs]
    ):
        if paragraph:
            st.write(paragraph)

        # Show previously completed conversations.
        for j, check in enumerate(checks[:position]):
            if check["after_paragraph"] == i:
                st.markdown("**AI Tutor:** " + check["question"])
                st.markdown("**Your answer:** " + responses[j]["answer"])
                st.markdown("**Tutor response:** " + responses[j]["reply"])
                st.divider()

    # Current conversational checkpoint.
    if position < len(checks):
        check = checks[position]

        st.divider()
        st.markdown("**AI Tutor**")
        st.write(check["question"])

        if not s.instruction_waiting[s.part]:
            answer = st.text_area(
                "Your answer",
                key=f"instruction_answer_{s.part}_{position}",
                height=110
            )

            if st.button(
                "Done",
                type="primary",
                disabled=not answer.strip(),
                key=f"check_done_{s.part}_{position}"
            ):
                key = st.secrets.get("GROQ_API_KEY", "")

                if not key:
                    st.error("GROQ_API_KEY is missing.")
                    st.stop()

                try:
                    with st.spinner("Tutor responding..."):
                        reply = instructional_reply(
                            key, part, check, answer
                        )
                except Exception as exc:
                    st.error(f"Tutor unavailable: {exc}")
                    st.stop()

                responses.append({
                    "answer": answer,
                    "reply": reply
                })

                track(
                    "instruction_conversation",
                    part=s.part+1,
                    checkpoint=position+1,
                    question=check["question"],
                    answer=answer,
                    reply=reply
                )

                s.instruction_waiting[s.part] = True
                st.rerun()

        else:
            st.markdown("**Your answer:** " + responses[position]["answer"])
            st.markdown("**Tutor response:** " + responses[position]["reply"])

            if st.button(
                "Continue",
                type="primary",
                key=f"check_continue_{s.part}_{position}"
            ):
                s.instruction_positions[s.part] += 1
                s.instruction_waiting[s.part] = False
                st.rerun()

    # All checkpoints completed.
    else:
        # Display the worked examples.
        for example in part["example"]:
            st.subheader("Worked example · " + example["title"])
            st.write(example["text"])
            st.markdown("**Answer:** " + example["answer"])
            st.write(example["explanation"])

        st.divider()

        if not s.instruction_done[s.part]:
            st.markdown("**AI Tutor**")
            st.write(
                f"You've completed Part {s.part+1} instruction! "
                "Now go to Practice Items and complete the activities. "
                "You can return to this instruction whenever needed."
            )

            if st.button("Go to Practice Items", type="primary"):
                s.instruction_done[s.part] = True
                track("instruction_completed", part=s.part+1)
                go("practice")

        else:
            st.write(
                "You have completed this instruction. "
                "You can review it or return to Practice Items."
            )

            if st.button("Return to Practice Items", type="primary"):
                go("practice")


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
        chosen=select_buttons('Select one sentence',item['sentences'],s.selection,item['id']) if not s.submitted else s.selection
        s.selection=chosen
    else:
        st.write('First select the main paragraph. Then select its main sentence.')
        chosen=select_buttons('Select the main paragraph',item['paragraphs'],s.selection,item['id']+'_para') if not s.submitted else s.selection
        if chosen!=s.selection:s.sentence=None
        s.selection=chosen
        if chosen is not None:
            sentences=get_sentences(item['paragraphs'][chosen-1])
            if not s.submitted:s.sentence=select_buttons('Select the main sentence in that paragraph',sentences,s.sentence,item['id']+'_sent')
            else:st.write(f'Selected sentence: {s.sentence}')
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
                        s.personalized=personalized_feedback(key,item,{'paragraph':s.selection,'sentence':s.sentence},s.reasoning,answer_key(item),correct)
                except Exception as exc:
                    st.error(f'Feedback unavailable: {exc}');st.stop()
            s.submitted=True
            track('practice_feedback_ready',item=item['id'],condition=s.condition)
            st.rerun()
    else:
        st.divider()
        st.subheader('Answer and feedback')
        st.markdown('**Correct answer:** '+answer_key(item))
        if s.condition in (2,3,4):st.write(item['reason'])
        if s.condition==4:st.markdown('**Feedback on your explanation:** '+s.get('personalized',''))
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
