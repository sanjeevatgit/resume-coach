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
        # doc.close() 
        

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
    # for key in st.session_state.keys():
    #     # if key != "jd_text" or key != "text" or key != "file":
    #         print(key)
    #         del st.session_state[key]
    
        # print("session variable content after deletion")
        # print(st.session_state)
    st.session_state["job_description"] = ""
    st.session_state["candidate_resume"] = ""
    if "jd_text" in st.session_state:
        st.session_state["jd_text"] = ""
    if "text" in st.session_state:
        st.session_state["text"] = ""
    if "file" in st.session_state:
        st.session_state["file"] = None
    if 'messages' in st.session_state:
        st.session_state.messages = []
    if 'gemini_messages' in st.session_state:
        st.session_state.gemini_messages = []
    if 'gemini_history' in st.session_state:
        st.session_state.gemini_history = []
    


st.title("Resume Assistant ChatBot")

reset = st.button("Reset Chat")
if reset:
    reset_chat()
    # st.session_state["jd_text"] = ""
    st.experimental_rerun()
    
        

model = st.selectbox("Select a model: ", ("GPT-4", "Gemini-pro"))

if model == "GPT-4":
    OPENAI_API_KEY = st.text_input("Enter your API key for OpenAI's GPT-4 model: ", type="password")
    
    useGPT = st.button("Use GPT-4")
    if useGPT:
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

    # get job description either as text or URL
    col_text, _, _, _ = st.columns(4)
    with col_text:
        st.write("Job Description Text")

    reset_chat = False #flag is set true if relevant information has changed and older chat is no longer valid

    if "job_description" not in st.session_state:
        st.session_state.job_description = ""
    
    jd_text = ""
    if col_text:
        placeholder = st.empty()
        jd_text = placeholder.text_area("Paste job description text:",
                                max_chars=5500,
                                height=200,
                                placeholder="Paste job description text here...",
                                label_visibility="collapsed",
                                key = 'jd_text')
        
   
    if jd_text:
        if st.session_state.job_description and st.session_state.job_description != jd_text:
            reset_chat = True
        st.session_state.job_description = jd_text
    
    elif not jd_text and useGPT:
        st.toast(":red[Upload job description data to get started]", icon="⚠️")
            
    # *******************************************************************************
    # GET RESUME OR WORK HISTORY
    # *******************************************************************************

    if "candidate_resume" not in st.session_state:
        st.session_state.candidate_resume = ""
    st.write("Upload your resume or any work related notes")
    file = st.file_uploader("Upload your resume or any work related notes",
                            label_visibility='collapsed', type=["json", "pdf", "text"],
                            key="resume")
    print(file)
    st.session_state.file = file
    
    # Check and save the contents of the file
    if file:
        saved_file_name = save_file(file)
        new_resume = get_text(saved_file_name)
        if st.session_state.candidate_resume and st.session_state.candidate_resume != new_resume:
            reset_chat = True
        st.session_state.candidate_resume = get_text(saved_file_name)
        
    elif not file and useGPT:
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
    # if 'messages' not in st.session_state:
        st.session_state.messages = []

    if st.session_state.messages == []:
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
    
    useGemini = st.button("Use Gemini-pro")
    if useGemini:
        if GOOGLE_API_KEY:
            if validate_api_key(GOOGLE_API_KEY, model):
                st.success('API key for Gemini-pro is valid!')
            else:
                st.error('API key for Gemini-pro is invalid.')
                st.stop()
                
    MODEL_ROLE = 'ai'
    AI_AVATAR_ICON = '✨'

    try:
        col_jd, _,_,_ = st.columns(4)
        
        with col_jd:
            st.write("Job Description Text")
        
        text = ""
        text = st.text_area("Paste job description text:",
                               max_chars=5500,
                               height=200,
                               placeholder="Paste job description text here...",
                               label_visibility="collapsed",
                               key = "text")
        # print(text)
        
        if 'job_description' not in st.session_state:
            st.session_state.job_description = ""
            
        if text:
            st.session_state.job_description = text
        
        elif not text and useGemini:
            st.toast(":red[Upload job description data to get started]", icon="⚠️")
        
        if "candidate_resume" not in st.session_state:
            st.session_state.candidate_resume = ""
        st.write("Upload your resume or any work related notes")
    
        file = st.file_uploader("Upload your resume in PDF format" , type=["pdf"], key="gResume")
        
        if file:
            st.session_state.candidate_resume = resume_pdf_setup(file)
            
        elif not file and useGemini:
            st.toast(":red[Upload user's resume or work related data to get started]", icon="⚠️")
            
            
            # st.write("Chat with Gemini")
            
        if 'gemini_messages' not in st.session_state: 
            st.session_state.gemini_messages = []
        if 'gemini_history' not in st.session_state:
            st.session_state.gemini_history = []
        
        
        st.session_state.model = genai.GenerativeModel('gemini-pro')
        st.session_state.chat = st.session_state.model.start_chat(history=st.session_state.gemini_history,)
        
        if st.session_state.gemini_messages is not None:
            for message in st.session_state.gemini_messages:
                with st.chat_message(
                        name=message['role'],
                        avatar=message.get('avatar'),
                ):
                    st.markdown(message['content'])
                
                
        if user_prompt := st.chat_input("Your question here: "):
            with st.chat_message('user'):
                st.markdown(user_prompt)
            st.session_state.gemini_messages.append(
                dict(
                    role='user',
                    content=user_prompt,
                    )
                )
            
            # prompt = get_prompt_text(user_prompt, job_description=text, resume=resume_pdf_setup(file))
            prompt = get_prompt_text(user_prompt, job_description=text, resume=st.session_state.candidate_resume)
            
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
            st.session_state.gemini_messages.append(
                dict(
                    role=MODEL_ROLE,
                    content=st.session_state.chat.history[-1].parts[0].text,
                    avatar=AI_AVATAR_ICON,
                    )
                )
            st.session_state.gemini_history = st.session_state.chat.history
            # for k in st.session_state.keys():
            #     print(k)
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.markdown("<h3 style='text-align: center;'>Please try again!</h3>", unsafe_allow_html=True)
        st.stop()


            
            
            
            
            
            

































