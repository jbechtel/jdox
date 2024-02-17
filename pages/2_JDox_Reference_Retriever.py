import os
import s3fs
import streamlit as st
from llama_index import ServiceContext, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from llama_index.embeddings import HuggingFaceEmbedding
from constants import TMP_DIR, S3_DIR

st.set_page_config(page_title="Query the JWST docs (JDox)", page_icon="🔭", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Query the JWST docs (JDox) 🔭")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/jbechtel/jdox)"


if "retriever_messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.retriever_messages = [
        {"role": "assistant", "content": "Ask me a question about JWST, and I'll point you to the right URLs!"}
    ]


@st.cache_resource(show_spinner=False)
def _embedder():
    return HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


if "embedder" not in st.session_state.keys():
    st.session_state.embedder = _embedder()


def _service_context():
    service_context = ServiceContext.from_defaults(
        llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
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


def _load_index():
    service_context = _service_context()
    index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir=TMP_DIR),
        service_context=service_context
    )
    return index


if "retriever_engine" not in st.session_state.keys() and "index" not in st.session_state.keys():
    with st.spinner(text="Initializing Retriever"):
        st.session_state.index = _load_index()
        st.session_state.retriever_engine = st.session_state.index.as_retriever(similarity_top_k=3)


if prompt := st.chat_input("Your question"):  # Prompt for user input and save to chat history
    st.session_state.retriever_messages.append({"role": "user", "content": prompt})

for message in st.session_state.retriever_messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "collapsed" in message.keys():
            with st.expander("Click here to see the relevant text."):
                with st.container(height=200):
                    st.markdown(message['collapsed'])


def format_response(resp):
    f = "Below are the most relevant references.\n"
    for i, source in enumerate(resp):
        f += f"\n [{i + 1}] {resp[i].metadata['URL']}\n"

    e = ""
    for i, source in enumerate(resp):
        e += f"\n [{i + 1}] {resp[i].metadata['URL']}"
        t = resp[i].get_text().replace('\n', '\n>')
        e += f"""\n> {t}\n\n"""

    return f, e


# If last message is not from assistant, generate a new response
if st.session_state.retriever_messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.retriever_engine.retrieve(prompt)
            formatted_response, collapsed = format_response(response)
            st.markdown(formatted_response)
            with st.expander("Click here to see the relevant text."):
                with st.container(height=200):
                    st.markdown(collapsed)
            message = {"role": "assistant", "content": formatted_response, "collapsed": collapsed}
            st.session_state.retriever_messages.append(message) # Add response to message history

