import os
import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.query_engine import CitationQueryEngine
from llama_index import download_loader
import openai
from llama_index import SimpleDirectoryReader
import s3fs

openai.api_key = st.secrets.openai_key

# STORAGE_DIR = './storage'
# STORAGE_DIR = './storage-jdox'
STORAGE_DIR = './jdox_storage'
STORAGE_DIR = './storage-jdox-site-depth1'

service_context = ServiceContext.from_defaults(
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1, ),
    embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"))


def load_data():
    # with st.spinner(text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."):
    reader = SimpleDirectoryReader(input_dir="./data", recursive=True, )
    docs = reader.load_data()
    index = VectorStoreIndex.from_documents(docs, service_context=service_context)
    index.storage_context.persist(STORAGE_DIR)
    return index


def load_website():
    WholeSiteReader = download_loader("WholeSiteReader")
    # Initialize the scraper with a prefix URL and maximum depth
    scraper = WholeSiteReader(
        prefix='https://jwst-docs.stsci.edu/',  # Example prefix
        max_depth=10
    )

    # Start scraping from a base URL
    documents = scraper.load_data(base_url='https://jwst-docs.stsci.edu/')  # Example base URL
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(STORAGE_DIR)
    return index


def load_index():
    if not os.path.exists(STORAGE_DIR):
        with st.spinner(text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."):
            index = load_data()
    else:
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
    return index


def move_index():
    index = load_index()
    s3 = s3fs.S3FileSystem(
        key=st.secrets.aws_access_key,
        secret=st.secrets.aws_secret_access_key,
    )
    s3_storage_dir = st.secrets.s3_bucket + '/jdox-storage'
    index.storage_context.persist(persist_dir=s3_storage_dir, fs=s3)
    # load index from s3
    index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir=s3_storage_dir, fs=s3),
    )

move_index()
# index = load_index()
# query_engine = CitationQueryEngine.from_args(
#     index,
#     similarity_top_k=3,
#     # here we can control how granular citation sources are, the default is 512
#     citation_chunk_size=512,
# )
#     # st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)
#
# messages = []
#
# prompt = "How do I submit a JWST proposal? "
# messages.append({"role": "user", "content": prompt})
#
#
# response = query_engine.query(prompt)
#
# print(response.response)
#
#
# def format_response(response):
#     r = response.response
#     r += "\n\nReferences\n"
#     for i, source in enumerate(response.source_nodes):
#         r += f"""\n {i+1}. "{source.metadata['file_name']}". Page {source.metadata['page_label']}"""
#
#     return r
#
#
# print(format_response(response))
#
#
# print(0)
