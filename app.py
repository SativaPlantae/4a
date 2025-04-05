import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 🔐 Chave da OpenAI via variável de ambiente
openai_api_key = os.getenv("OPENAI_API_KEY")

# 🚀 Carrega e prepara o documento e a cadeia de QA
@st.cache_resource
def carregar_qa_chain():
    loader = PyPDFLoader("40.pdf")
    documentos = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(documentos)

    vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
Você é um assistente virtual treinado com base em um documento técnico de licenciamento ambiental. Seu estilo é natural, amigável e direto, como se estivesse conversando com alguém em um chat. 

Quando responder, use uma linguagem simples e acessível, como o ChatGPT faria. Seja claro, mas não precisa ser excessivamente formal. Evite repetir demais o conteúdo da pergunta.

Se a resposta não estiver presente no documento, diga algo como: "Hmm, isso não está muito claro por aqui, mas posso tentar ajudar com base no que tenho."

Se a pergunta estiver fora do escopo do documento, diga isso de forma simpática.

-------------------
{context}

Pergunta: {question}
Resposta:"""
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        max_tokens=500,
        openai_api_key=openai_api_key
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )

# ⚙️ Configuração da página
st.set_page_config(page_title="Chatbot da AD nº 43/2024", page_icon="🤖")
st.title("🤖 Chatbot da AD nº 43/2024")
st.markdown("Converse sobre o conteúdo da Autorização Direta 📄")

# 💬 Inicializa o histórico de conversa
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# 🔄 Exibe o histórico completo
for remetente, mensagem in st.session_state.mensagens:
    with st.chat_message("user" if remetente == "Você" else "assistant"):
        st.markdown(mensagem)

# 🧠 Campo de input estilo chat (sempre visível no final)
user_input = st.chat_input("Digite sua pergunta aqui...")

if user_input:
    # Adiciona pergunta ao histórico
    st.session_state.mensagens.append(("Você", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Consultando o documento..."):
        try:
            qa_chain = carregar_qa_chain()
            resposta = qa_chain.run(user_input)
        except Exception as e:
            resposta = f"⚠️ Ocorreu um erro: {e}"

    # Adiciona resposta ao histórico
    st.session_state.mensagens.append(("Chatbot", resposta))
    with st.chat_message("assistant"):
        st.markdown(resposta)
