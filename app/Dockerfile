FROM continuumio/miniconda3:4.10.3

# Instalar ferramentas necessárias (exemplo)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev

WORKDIR /app

COPY environment.yml /app/environment.yml

RUN conda env create -f environment.yml

COPY . /app

EXPOSE 8501

ENTRYPOINT ["conda", "run", "-n", "myenv", "--no-capture-output"]
CMD ["streamlit", "run", "app.py"]
