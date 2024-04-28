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

# Garantindo a conexão com o banco de dados
load_dotenv()
CONNECTION_STRING = "postgresql+psycopg2://postgres:neki@db:5432/jackchain"



def ler_arquivos_pdf(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        #Le o pdf e depois le cada pagina do pdf
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text() if page.extract_text() else ""
            # Removendo alguns nulos em casos de pdfs mal formatados
            sanitized_text = page_text.replace("\x00", "")
            text += sanitized_text
    return text


def gerar_pedacos_texto(text):
    # Separa o texto em pedaços menores para facilitar a busca
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", " "],
            chunk_size=500,
            chunk_overlap=80,
            length_function=len
        )

        chunks = text_splitter.split_text(text)
        return chunks
    # Tratamento de exceções para o caso de erro ao dividir o texto
    except Exception as e:
        st.error(f"Error while splitting text: {str(e)}")
        return []


def armazenar_vetores(text_chunks):
    embeddings = OpenAIEmbeddings()
    # Armazena os vetores no banco de dados
    return PGVector.from_texts(texts=text_chunks, embedding=embeddings, connection_string=CONNECTION_STRING)


def chain_conversa(vectorstore):
    llm = ChatOpenAI()

    # Inicializa a cadeia de conversa com o modelo de linguagem e o vetorstore criado anteriormente e um memory para armazenar o histórico de conversas
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
    # Verifica se a cadeia de conversa foi inicializada e responde a pergunta do usuário
    if st.session_state.conversation is not None:
        response = st.session_state.conversation.invoke({'question': user_question})
        st.session_state.chat_history = response['chat_history']
        # Exibe o histórico de conversas na tela do usuário com o bot e o usuário
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
    else:
        # Exibe uma mensagem de erro caso a cadeia de conversa não tenha sido inicializada.
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
    4. O bot só irá responder após os PDFs serem carregados, não é possível fazer perguntas antes disso.
    """
    )

    # Inicializa as variáveis de sessão para armazenar a conversa e o histórico de conversas
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
                # Lê o texto dos PDFs
                raw_text = ler_arquivos_pdf(pdf_docs)

                # Separa o texto em pedaços menores para facilitar a busca
                text_chunks = gerar_pedacos_texto(raw_text)

                # Armazena os vetores no banco de dados
                vectorstore = armazenar_vetores(text_chunks)  

                # Inicializa a cadeia de conversa com o vetorstore criado anteriormente
                st.session_state.conversation = chain_conversa(vectorstore)
                st.success("Cadeia de conversa inicializada e dados salvos com sucesso!", icon="✅")

if __name__ == '__main__':
    # load_dotenv()
    # CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION_STRING")
    main()


