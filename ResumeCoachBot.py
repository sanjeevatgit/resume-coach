import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import fitz  # imports the pymupdf library
import os
import time
import requests


# uploaded file operations : save it, extract text
def save_file(file):
    """
    Save the user uploaded file. 
    """
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.abspath(os.path.join("uploads", file.name))
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    return file_path


def get_text(file_name):
    """
    Extract text from the file. File should be pdf file
    """
    doc = fitz.open(file_name)  # open a document
    text = ""
    for page in doc:  # iterate the document pages
        text += page.get_text()  # get plain text encoded as UTF-8
    return text


def get_prompt_text(question, job_description, resume):
    """
    Structure the prompt

    """
    
    prompt = """
        Discard any prior instructions.
        You are an expert in resume writing and are a certified resume writer and career coach from a reputed professional association such as Professional Association of Resume Writers and Career Coaches.
        You have expertise about the latest hiring trends in a variety of jobs in a broad range of industries.
        You know how to write a compelling resume tailored to the target job. 
        You know how to use resume as a marketing tool. You excel at incorporating design elements and writing compelling content to effectively market your clients to hiring managers and recruiters.
        You know how to sell benefits instead of features and emphasize successes,
        contributions, and achievements.
        You know how to write with impeccable grammar, correct punctuation and capitalization.
        You can write a dynamic resume that uses competencies, skills and metrics to place the individual ahead of the crowd.
        You can show-case results-focused accomplishments and write strong profile statements and centrally-focused theme resumes.
        You are a resume chat assistant. You are given a job description and a candidate resume.
        Using the Job Description and  Resume, answer the question provided in the Question section.
        Respond only from the text provided. 
      Question: {question}
      Job Description : {job_description}
      Resume : {resume}
      """.format(
        question=question, job_description=job_description, resume=resume
    )
    return prompt


def resume_pdf_setup(uploaded_file):
    """
    Extract text from the file. File should be pdf file

    """
    if uploaded_file is not None:
        print(uploaded_file)
        doc = fitz.open("pdf", uploaded_file.read())
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            full_text += text
        # st.write(full_text)
        return full_text
        doc.close() 
        

def validate_api_key(api_key, model):
    
    if model == "GPT-4":
        # Endpoint to validate the API key by making a test request
        validation_endpoint = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        }
        
        try:
            response = requests.post(validation_endpoint, headers=headers, json=data)
            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    elif model == "Gemini-pro":
        # validation_endpoint = "https://api.example.com/v1/gemini-pro/validate"
        validation_endpoint = "https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini"
    
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gemini-pro",
            "prompt": "Validate API key"
        }
        
        try:
            response = requests.post(validation_endpoint, headers=headers, json=data)
            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            return False
        

def reset_chat():
    # st.session_state.chat_history = []
    st.session_state.messages = []



st.title("Resume Assistant ChatBot")

if st.button("Reset Chat"):
    # reset_chat()
    # st.experimental_rerun()
    jd_text = ""
    jd_text = st.text_area("Paste job description text:",
                            max_chars=5500,
                            height=200,
                            placeholder="Paste job description text here...",
                            label_visibility="collapsed",
                            key="jd_text")
    
if st.button("Modify Text Area"):
    new_content = st.text_input("Enter new content:")
    if new_content:
        modify_text_area(new_content)
        st.experimental_rerun()
        

model = st.selectbox("Select a model: ", ("GPT-4", "Gemini-pro"))

if model == "GPT-4":
    OPENAI_API_KEY = st.text_input("Enter your API key for OpenAI's GPT-4 model: ", type="password")
    
    if st.button("Use GPT-4"):
        if OPENAI_API_KEY:
            if validate_api_key(OPENAI_API_KEY, model):
                st.success('API key for GPT-4 is valid!')
            else:
                st.error('API key for GPT-4 is invalid.')
                st.stop()
        else:
            st.error('Please enter an API key for GPT-4.')
            st.stop()
            
        
    # *******************************************************************************
    # GET JOB DESCRIPTION
    # *******************************************************************************
    # # get job description either as text or URL
    # col_text, col_url, _, _ = st.columns(4)
    # with col_text:
    #     st.write("Job Description Text")
    # with col_url:
    #     is_url_button = st.toggle('Job URL', False)

    # reset_chat = False #flag is set true if relevant information has changed and older chat is no longer valid

    # if "job_description" not in st.session_state:
    #     st.session_state.job_description = ""
    # jd_url, jd_text = "", ""
    # if is_url_button:
    #     jd_url = st.text_input("Enter job posting URL:",
    #                            placeholder="Enter job posting URL here...",
    #                            label_visibility="collapsed")
    # else:
    #     jd_text = st.text_area("Paste job description text:",
    #                            max_chars=5500,
    #                            height=200,
    #                            placeholder="Paste job description text here...",
    #                            label_visibility="collapsed")

    # if jd_url:
    #     # TODO
    #     # jd_text = get_jd_text(jd_url)
    #     pass

    # if jd_text:
    #     if st.session_state.job_description and st.session_state.job_description != jd_text:
    #         reset_chat = True
    #     st.session_state.job_description = jd_text

    # get job description either as text or URL
    col_text, _, _, _ = st.columns(4)
    with col_text:
        st.write("Job Description Text")

    reset_chat = False #flag is set true if relevant information has changed and older chat is no longer valid

    if "job_description" not in st.session_state:
        st.session_state.job_description = ""
    
    jd_text = ""
    if col_text:
        jd_text = st.text_area("Paste job description text:",
                                max_chars=5500,
                                height=200,
                                placeholder="Paste job description text here...",
                                label_visibility="collapsed",
                                key = 'jd_text')
    
    # if jd_text.strip(" ") is None:
    #     st.toast(":red[Upload job description data to get started]", icon="⚠️")
        # st.stop()
    # print(jd_text)
    if jd_text:
        if st.session_state.job_description and st.session_state.job_description != jd_text:
            reset_chat = True
        st.session_state.job_description = jd_text
    
    else:
        st.toast(":red[Upload job description data to get started]", icon="⚠️")
            
    # *******************************************************************************
    # GET RESUME OR WORK HISTORY
    # *******************************************************************************

    if "candidate_resume" not in st.session_state:
        st.session_state.candidate_resume = ""
    st.write("Upload your resume or any work related notes")
    file = st.file_uploader("Upload your resume or any work related notes",
                            label_visibility='collapsed', type=["json", "pdf", "text"])
    
    # Check and save the contents of the file
    if file:
        saved_file_name = save_file(file)
        new_resume = get_text(saved_file_name)
        if st.session_state.candidate_resume and st.session_state.candidate_resume != new_resume:
            reset_chat = True
        st.session_state.candidate_resume = get_text(saved_file_name)
        
    else:
        st.toast(":red[Upload user's resume or work related data to get started]", icon="⚠️")
        # st.stop()
    # print(st.session_state.job_description, st.session_state.candidate_resume)
            
            
    # *******************************************************************************
    # CHAT BOT 
    # *******************************************************************************
    
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

    client = OpenAI(api_key=OPENAI_API_KEY)
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
                
        


if model == "Gemini-pro":
    GOOGLE_API_KEY = st.text_input("Enter your API key for Google's Gemini-pro model: ", type="password")
    genai.configure(api_key=GOOGLE_API_KEY)
    
    if st.button("Use Gemini-pro"):
        if GOOGLE_API_KEY:
            if validate_api_key(GOOGLE_API_KEY, model):
                st.success('API key for GPT-4 is valid!')
            else:
                st.error('API key for GPT-4 is invalid.')
                st.stop()
                
    MODEL_ROLE = 'ai'
    AI_AVATAR_ICON = '✨'

    try:
        col_jd, _,_,_ = st.columns(4)
        
        with col_jd:
            st.write("Job Description Text")
        
        file = st.file_uploader("Upload your resume in PDF format" , type=["pdf"])
        
        text = ""
        text = st.text_area("Paste job description text:",
                               max_chars=5500,
                               height=200,
                               placeholder="Paste job description text here...",
                               label_visibility="collapsed")
        
        # col_1, _, _ = st.columns(3)
        # with col_1:
        #     get_resume_button = st.button("Submit", key="get_resume", type="primary", use_container_width=True)
            
        # if get_resume_button:
        if file is None:
            st.toast(":red[Upload user's resume or work related data to get started]", icon="⚠️")
            # st.stop()
            
        if text.strip(" ") is None:
            st.toast(":red[Upload job description data to get started]", icon="⚠️")
            # st.stop()
                
        if file is not None and text is not None:
            
            # st.write("Chat with Gemini")
            
            if 'messages' not in st.session_state: 
                st.session_state.messages = []
            if 'gemini_history' not in st.session_state:
                st.session_state.gemini_history = []
            
            
            st.session_state.model = genai.GenerativeModel('gemini-pro')
            st.session_state.chat = st.session_state.model.start_chat(history=st.session_state.gemini_history,)
            
            if st.session_state.messages is not None:
                for message in st.session_state.messages:
                    with st.chat_message(
                            name=message['role'],
                            avatar=message.get('avatar'),
                    ):
                        st.markdown(message['content'])
                    
                    
            if user_prompt := st.chat_input("Your question here: "):
                with st.chat_message('user'):
                    st.markdown(user_prompt)
                st.session_state.messages.append(
                    dict(
                        role='user',
                        content=user_prompt,
                        )
                    )
                
                prompt = get_prompt_text(user_prompt, job_description=text, resume=resume_pdf_setup(file))
                
                response = st.session_state.chat.send_message(
                    prompt,
                    stream=True,
                    )
                
                with st.chat_message(
                        name=MODEL_ROLE,
                        avatar=AI_AVATAR_ICON,
                ):
                    message_placeholder = st.empty()
                    full_response = ""
                    assistant_response = response
                    for chunk in response:
                        for word in chunk.text.split(" "):
                            full_response += word + " "
                            time.sleep(0.05)
                            message_placeholder.write(full_response + '▌')
                    message_placeholder.write(full_response)
                    
                # print(st.session_state.chat.history)
                st.session_state.messages.append(
                    dict(
                        role=MODEL_ROLE,
                        content=st.session_state.chat.history[-1].parts[0].text,
                        avatar=AI_AVATAR_ICON,
                        )
                    )
                st.session_state.gemini_history = st.session_state.chat.history
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.markdown("<h3 style='text-align: center;'>Please try again!</h3>", unsafe_allow_html=True)
        st.stop()


            
            
            
            
            
            

































