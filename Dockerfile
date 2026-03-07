FROM ubuntu:22.04 as builder

# Устанавливаем Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-21-jre-headless python3 pip graphviz graphviz-dev python3-dev build-essential wget unzip && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV LANG=C.UTF-8
ENV PATH=$JAVA_HOME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# --- Python зависимости ---
COPY requirements/base.txt /opt/structurizr_backend/requirements/base.txt
RUN pip install --no-cache-dir -r /opt/structurizr_backend/requirements/base.txt && \
    rm -rf /root/.cache/pip

# --- Скачиваем Structurizr CLI ---
RUN wget -O /tmp/structurizr.zip https://github.com/structurizr/cli/releases/download/v2025.11.09/structurizr-cli.zip && \
    unzip /tmp/structurizr.zip -d /usr/local/structurizr-cli/ && \
    rm /tmp/structurizr.zip && \
    chmod +x /usr/local/structurizr-cli/structurizr.sh

# --- Исходный код ---
COPY . /opt/structurizr_backend

WORKDIR /opt/structurizr_backend
CMD [ "python3", "/opt/structurizr_backend/src/main.py" ]