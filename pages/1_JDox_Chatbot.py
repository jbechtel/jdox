import os
import s3fs
import streamlit as st
from llama_index import ServiceContext, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from llama_index.embeddings import HuggingFaceEmbedding
from helpers import format_response
from constants import TMP_DIR, S3_DIR

st.set_page_config(page_title="Chat with the JWST docs (JDox)", page_icon="🔭", layout="centered",
                   initial_sidebar_state="auto", menu_items=None)
st.title("Chat with the JWST docs (JDox) 🔭")


with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/jbechtel/jdox)"

openai_api_key = st.secrets.openai_key

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about JWST, and I'll find an answer in from JDox."}
    ]


@st.cache_resource(show_spinner=False)
def _embedder():
    return HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


if "embedder" not in st.session_state.keys():
    st.session_state.embedder = _embedder()


def _service_context(api_key):
    service_context = ServiceContext.from_defaults(
        llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=api_key),
        embed_model=st.session_state.embedder)
    return service_context


@st.cache_resource(show_spinner=False)
def _storage_context():
    if not os.path.exists(TMP_DIR):
        with st.spinner(text="Loading data from S3"):
            s3 = s3fs.S3FileSystem(
                key=st.secrets.aws_access_key,
                secret=st.secrets.aws_secret_access_key,
            )
            s3_storage_dir = st.secrets.s3_bucket + '/' + S3_DIR
            storage_context = StorageContext.from_defaults(persist_dir=s3_storage_dir, fs=s3)
            storage_context.persist(TMP_DIR)
    else:
        with st.spinner(text="Loading Index"):
            storage_context = StorageContext.from_defaults(persist_dir=TMP_DIR)

    return storage_context


if "storage_context" not in st.session_state.keys():
    st.session_state.storage_context = _storage_context()


def _load_index(api_key):
    service_context = _service_context(api_key)
    index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir=TMP_DIR),
        service_context=service_context
    )
    return index


if openai_api_key and "chat_engine" not in st.session_state.keys() and "keyed_index" not in st.session_state.keys():
    with st.spinner(text="Initializing JDox ChatBot"):
        st.session_state.keyed_index = _load_index(openai_api_key)
        st.session_state.chat_engine = st.session_state.keyed_index.as_chat_engine(chat_mode="condense_plus_context")
        st.session_state.openai_api_key = openai_api_key

if prompt := st.chat_input("Your question"):  # Prompt for user input and save to chat history
    if "openai_api_key" not in st.session_state.keys():
        st.info("Please add your OpenAI API key to continue.")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            formatted_response = format_response(response)
            st.write(formatted_response)
            message = {"role": "assistant", "content": formatted_response}
            st.session_state.messages.append(message)  # Add response to message history
