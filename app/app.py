import os
import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain_community.vectorstores.pgvector import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()
CONNECTION_STRING = "postgresql+psycopg2://postgres:neki@db:5432/jackchain"



def ler_arquivos_pdf(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text() if page.extract_text() else ""
            # Remove NUL characters from the extracted text
            sanitized_text = page_text.replace("\x00", "")
            text += sanitized_text
    return text


def gerar_pedacos_texto(text):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", " "],
            chunk_size=500,
            chunk_overlap=80,
            length_function=len
        )

        chunks = text_splitter.split_text(text)
        return chunks
    except Exception as e:
        st.error(f"Error while splitting text: {str(e)}")
        return []


def armazenar_vetores(text_chunks):
    embeddings = OpenAIEmbeddings()
    # Here we assume text_chunks is not None since we've checked earlier.
    return PGVector.from_texts(texts=text_chunks, embedding=embeddings, connection_string=CONNECTION_STRING)


def chain_conversa(vectorstore):
    llm = ChatOpenAI()

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 1}),
        memory=memory
    )
    return conversation_chain

def pergunta_usuario(user_question):
    if st.session_state.conversation is not None:
        response = st.session_state.conversation.invoke({'question': user_question})
        st.session_state.chat_history = response['chat_history']
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
    else:
        st.error("A cadeia de conversa não foi inicializada. Por favor, carregue os PDFs primeiro.")

def main():

    st.set_page_config(page_title="NEKI PDFs", page_icon=":books::parrot:")
    st.write(css, unsafe_allow_html=True)

    st.sidebar.markdown(
    """
    ### Instruções de uso:
    1. Navegue e faça upload de seus PDFs na barra lateral.
    2. Clique no botão 'Carregar' para processar os PDFs.
    3. Faça perguntas sobre os PDFs na caixa de texto acima.
    """
    )

    # Ensure session state variables are initialized
    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    st.header("Converse com múltiplos PDFs :books: :parrot: 🤖")
    user_question = st.text_input("Faça perguntas sobre os PDFs carregados aqui:")
    if user_question:
        pergunta_usuario(user_question)

    with st.sidebar:
        st.subheader("Seus PDFs")
        pdf_docs = st.file_uploader("Coloque seus PDFs aqui e clique em 'Carregar'", type="pdf" , accept_multiple_files=True)
        if st.button("Carregar"):
            with st.spinner("Carregando PDFs..."):
                raw_text = ler_arquivos_pdf(pdf_docs)
                text_chunks = gerar_pedacos_texto(raw_text)
                vectorstore = armazenar_vetores(text_chunks)  # Only one variable here.

                # Initialize conversation in session state
                st.session_state.conversation = chain_conversa(vectorstore)
                st.success("Cadeia de conversa inicializada e dados salvos com sucesso!", icon="✅")

if __name__ == '__main__':
    # load_dotenv()
    # CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION_STRING")
    main()


