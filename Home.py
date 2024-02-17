import streamlit as st

st.set_page_config(page_title="Chat with the JWST docs (JDox)", page_icon="🔭", layout="centered", initial_sidebar_state="auto", menu_items=None)


with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/jbechtel/jdox)"

"# 🔭JDox Chatbot with LLamaIndex and Streamlit"

"""This project allows users to interact with the James Webb Space Telescope documentation (JDox) 
    with natural language. See JDox here [https://jwst-docs.stsci.edu/](https://jwst-docs.stsci.edu/)"""

"""
Currently, there are two tools available on the left side bar:

- **JDox Chatbot**: combines Chat-GPT and a vector index to help users answer questions with JDox.  
    Since it uses Chat-GPT, an OpenAI key is required. Enter it on the sidebar to use this tool. 

- **Index Retriever**: queries JDox with just the vector index and without an LLM. 
    Therefore, it doesn't require an API key.
"""
