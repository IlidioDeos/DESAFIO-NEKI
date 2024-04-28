FROM postgres:13
# Instala as dependências necessárias para compilar o pgvector
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    libc-dev \
    postgresql-server-dev-13 \
    unzip  # This line adds the unzip utility

# Faz o download do código fonte do pgvector e compila
ADD https://github.com/pgvector/pgvector/archive/refs/heads/master.zip /master.zip
RUN unzip master.zip && cd pgvector-master && make && make install && cd .. && rm -rf pgvector-master master.zip

# Copia o arquivo de inicialização do banco de dados
COPY ./init-db.sql /docker-entrypoint-initdb.d/init-db.sql
