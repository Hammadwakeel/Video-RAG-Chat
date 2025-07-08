import os
from google import genai
from google.genai import types
from .auth import settings
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate


def init_google_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    return genai.Client(api_key=api_key)


def get_llm():
    api_key = os.getenv("CHATGROQ_API_KEY")
    if not api_key:
        raise ValueError("CHATGROQ_API_KEY not set")
    return ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0, max_tokens=1024, api_key=api_key)


def get_embeddings():
    return HuggingFaceEmbeddings(model_name="BAAI/bge-small-en", model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})

# reuse prompt template
prompt_template = """
You are an assistant specialized in solving quizzes. Your goal is to provide accurate, concise, and contextually relevant answers.
Use the following retrieved context to answer the user's question.
If the context lacks sufficient information, respond with "I don't know." Do not make up answers or provide unverified information.

Guidelines:
1. Extract key information from the context to form a coherent response.
2. Maintain a clear and professional tone.
3. If the question requires clarification, specify it politely.

Retrieved context:
{context}

User's question:
{question}

Your response:
"""

# Create a prompt template to pass the context and user input to the chain
user_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", prompt_template),
        ("human", "{question}"),
    ]
)


def create_chain(retriever):
    return ConversationalRetrievalChain.from_llm(
        llm=get_llm(),
        retriever=retriever,
        return_source_documents=True,
        chain_type='stuff',
        combine_docs_chain_kwargs={"prompt": user_prompt},
        verbose=False,
    )