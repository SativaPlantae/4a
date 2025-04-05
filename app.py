import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# 🔐 Pega a chave da OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

# 🔄 Carrega o documento e monta a base vetorial
@st.cache_resource
def carregar_chain_com_memoria():
    loader = PyPDFLoader("40.pdf")
    documentos = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(documentos)

    vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    prompt_template = PromptTemplate(
        input_variables=["chat_history", "context", "question"],
        template="""
Você é um assistente virtual treinado com base em um documento técnico de licenciamento ambiental. Seu estilo é natural, amigável e direto, como se estivesse conversando com alguém em um chat.

Use as mensagens anteriores (chat_history) e o contexto extraído do documento para responder com clareza, mantendo uma linguagem simples e objetiva.

Se a resposta não estiver clara no documento, diga algo como: "Hmm, isso não está muito claro por aqui, mas posso tentar ajudar com base no que tenho."

-------------------
Histórico do Chat:
{chat_history}

Contexto:
{context}

Pergunta: {question}
Resposta:"""
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.5, openai_api_key=openai_api_key),
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt_template}
    )

    return chain

# ⚙️ Configuração do app
st.set_page_config(page_title="Chatbot da AD nº 43/2024", page_icon="🤖")
st.title("🤖 Chatbot da AD nº 43/2024")
st.markdown("Converse sobre o conteúdo da Autorização Direta 📄")

# Inicializa o histórico visual (interface)
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Inicializa a cadeia com memória (uma vez por sessão)
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = carregar_chain_com_memoria()

# Exibe o histórico de forma visual no estilo de chat
for remetente, mensagem in st.session_state.mensagens:
    with st.chat_message("user" if remetente == "Você" else "assistant"):
        st.markdown(mensagem)

# Campo de input sempre no final
user_input = st.chat_input("Digite sua pergunta aqui...")

if user_input:
    # Exibe a pergunta no chat
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.mensagens.append(("Você", user_input))

    # Gera resposta com memória
    with st.spinner("Consultando o documento..."):
        try:
            resposta = st.session_state.qa_chain.run(user_input)
        except Exception as e:
            resposta = f"⚠️ Ocorreu um erro: {e}"

    # Exibe e salva resposta
    with st.chat_message("assistant"):
        st.markdown(resposta)
    st.session_state.mensagens.append(("Chatbot", resposta))
