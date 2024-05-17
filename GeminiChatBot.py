import bs4
from bs4 import BeautifulSoup
import requests
import streamlit as st
# from streamlit_chat import message
import io
import base64

import os
import dotenv
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
import pdf2image
from PIL import Image
import PyPDF2
import fitz
import time

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

def get_prompt_text(question, job_description, resume):
    # prompt = """
    #     You are a resume chat assistant. You are given a job description and a candidate resume.
    #     Using the Job Description and  Resume, answer the question provided in the Question section.
    #     Respond only from the text provided. Respond in not more than 3 short paragraphs.
    #   Question: {question}
    #   Job Description : {job_description}
    #   Resume : {resume}
    #   """.format(
    #     question=question, job_description=job_description, resume=resume
    # )
    
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

# model = genai.GenerativeModel('gemini-pro')
# chat = model.start_chat()

# def get_gemini_response(question):
#     response = chat.send_message(question, stream=True)
#     return response

st.set_page_config(
    page_title="Resume Assistant",
    )

try:
    col_jd, col_url,_,_ = st.columns(4)
    
    with col_jd:
        st.write("Job Description Text")
    
    file = st.file_uploader("Upload your resume in PDF format" , type=["pdf"])
    
    text = ""
    text = st.text_area("Paste job description text:", max_chars=5500, height=200, placeholder="Paste job description text here...", label_visibility="collapsed")
    
    # col_1, col_2 = st.columns(2)
    # with col_1:
    #     provider = st.selectbox("Select LLM provider([OpenAI](https://openai.com/blog/openai-api), [Gemini Pro](https://ai.google.dev/)):", ["gemini-pro", "gpt-4"])
    # with col_2:
    #     api_key = st.text_input("Enter API key:", type="password")
    
    col_1, _, _ = st.columns(3)
    with col_1:
        get_resume_button = st.button("Submit", key="get_resume", type="primary", use_container_width=True)
        
    if get_resume_button:
        if file is None:
            st.toast(":red[Upload user's resume or work related data to get started]", icon="⚠️")
            st.stop()
            
        if text.strip(" ") is None:
            st.toast(":red[Upload job description data to get started]", icon="⚠️")
            st.stop()
            
    if file is not None and text.strip(" ") is not None:
        
        st.write("Chat with Gemini")
        
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
                
            print(st.session_state.chat.history)
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

