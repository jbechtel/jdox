import os
import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.query_engine import CitationQueryEngine
import openai
from llama_index import SimpleDirectoryReader
from llama_index import download_loader
from site_loader import WholeSiteReader

STORAGE_DIR = './storage'
JDOX_STORAGE_DIR = './storage-jdox'
JDOX_STORAGE_DIR = './storage-jdox-pdfs'

service_context = ServiceContext.from_defaults(
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1, ),
    embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"))


def load_data():
    reader = SimpleDirectoryReader(input_dir="./jdox_data", recursive=True, )
    docs = reader.load_data()
    index = VectorStoreIndex.from_documents(docs, service_context=service_context)
    index.storage_context.persist("./jdox_storage")
    return index

def load_website(depth=2):
    # WholeSiteReader = download_loader("WholeSiteReader")
    # Initialize the scraper with a prefix URL and maximum depth
    print(f"depth = {depth}")
    scraper = WholeSiteReader(
        prefix='https://jwst-docs.stsci.edu/',  # Example prefix
        max_depth=depth
    )

    stems_to_skip = ['https://jwst-docs.stsci.edu/display/Latest/',
                     'https://jwst-docs.stsci.edu/label/'
                     ]
    # Start scraping from a base URL
    documents = scraper.load_data(base_url='https://jwst-docs.stsci.edu/',
                                  stems_to_skip=stems_to_skip)  # Example base URL
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(f'./storage-jdox-site-depth{depth}')
    return index

_ = load_website(1)
# _ = load_data()