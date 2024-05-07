"""
**************************************************************************
web app that takes as input:
1) accepts job description and
2) candidate's resume
And outputs: Report on
1) what matches
2) what is missing
**************************************************************************
"""

import streamlit as st
from openai import OpenAI
import fitz  # imports the pymupdf library
import os

# import rcllm # resume coach llm. Module that interacts with LLMs


st.title("Resume Coach")

# *******************************************************************************
# GET JOB DESCRIPTION
# *******************************************************************************

# TODO Can we get user input in chat messages?

# get job description either as text or URL
col_text, col_url, _, _ = st.columns(4)
with col_text:
    st.write("Job Description Text")
with col_url:
    is_url_button = st.toggle('Job URL', False)

reset_chat = False #flag is set true if relevant information has changed and older chat is no longer valid

if "job_description" not in st.session_state:
    st.session_state.job_description = ""
jd_url, jd_text = "", ""
if is_url_button:
    jd_url = st.text_input("Enter job posting URL:",
                           placeholder="Enter job posting URL here...",
                           label_visibility="collapsed")
else:
    jd_text = st.text_area("Paste job description text:",
                           max_chars=5500,
                           height=200,
                           placeholder="Paste job description text here...",
                           label_visibility="collapsed")

if jd_url:
    # TODO
    # jd_text = get_jd_text(jd_url)
    pass

if jd_text:
    if st.session_state.job_description and st.session_state.job_description != jd_text:
        reset_chat = True
    st.session_state.job_description = jd_text
    # st.write(jd_text)

# *******************************************************************************
# GET RESUME OR WORK HISTORY
# *******************************************************************************

if "candidate_resume" not in st.session_state:
    st.session_state.candidate_resume = ""
st.write("Upload your resume or any work related notes")
file = st.file_uploader("Upload your resume or any work related notes",
                        label_visibility='collapsed', type=["json", "pdf", "text"])


# uploaded file operations : save it, extract text
def save_file(file):
    """
    Save the user uploaded file. TODO: save it with session id and user login
    """
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.abspath(os.path.join("uploads", file.name))
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    # st.write(file_path)
    return file_path


def get_text(file_name):
    """
    extract text from the file. File could be pdf file
    """
    doc = fitz.open(file_name)  # open a document
    text = ""
    for page in doc:  # iterate the document pages
        text += page.get_text()  # get plain text encoded as UTF-8
    return text


# Check and save the contents of the file
if file:
    # st.write(f"{file.name} {file.type} {file.size}")
    saved_file_name = save_file(file)
    new_resume = get_text(saved_file_name)
    if st.session_state.candidate_resume and st.session_state.candidate_resume != new_resume:
        reset_chat = True
    st.session_state.candidate_resume = get_text(saved_file_name)
    # st.write(st.session_state.candidate_resume)

# *******************************************************************************
# CHAT BOT 
# *******************************************************************************
# TODO
# One can add file upload inside chatUI using discussion here:
# https://discuss.streamlit.io/t/how-do-i-replicate-chatgpt-file-upload-option-ui/51781/6  

# create prompt
prompt = ""
with open("rc_persona.txt", "r") as f:
    prompt = f.read()
prompt += "You are provided target job description here: "
prompt += st.session_state["job_description"]
prompt += "And clients resume is here: "
prompt += st.session_state["candidate_resume"]
prompt += "Answer the questions based on the resume and job description provided. Be brief and to the point."

# initialize chat history
if "messages" not in st.session_state or reset_chat == True:
    st.session_state.messages = []

if not st.session_state.messages:
    st.session_state.messages.append({"role": "user", "content": prompt})
else:
    st.session_state.messages[0] = {"role": "user", "content": prompt}

# display previous messages if the app is rerun 
for i, message in enumerate(st.session_state.messages):
    if i == 0:  # lets not show the prompt, only use interaction
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if user_question := st.chat_input("Ask me anything about your resume"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]}
                      for m in st.session_state.messages],
            stream=True)
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
