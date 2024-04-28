FROM postgres:13
# Install necessary packages for building pgvector and handling zip files
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    libc-dev \
    postgresql-server-dev-13 \
    unzip  # This line adds the unzip utility

# Download and install pgvector
ADD https://github.com/pgvector/pgvector/archive/refs/heads/master.zip /master.zip
RUN unzip master.zip && cd pgvector-master && make && make install && cd .. && rm -rf pgvector-master master.zip

# Copy initialization script
COPY ./init-db.sql /docker-entrypoint-initdb.d/init-db.sql
