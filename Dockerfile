FROM harbor.vimpelcom.ru/common/vimpelcom/ubuntu@sha256:0aaa99fe4d44ee6bd9c5dc2493135a184328f446908c0baae08e2435e7be2327 as builder

COPY --from=harbor.vimpelcom.ru/dockerhub/library/openjdk@sha256:d68a5da9fbf588cb2a406617d15ea5c4725e8ef49cedb159b9672e211e7c8827 /usr/local/openjdk-21 /usr/local/openjdk-21
ENV JAVA_HOME=/usr/local/openjdk-21
ENV LANG=C.UTF-8
ENV PATH=/usr/local/openjdk-21/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN update-alternatives --install /usr/bin/java java /usr/local/openjdk-21/bin/java 1

# Устанавливаем wget и unzip (нужны для скачивания Structurizr)
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 pip graphviz graphviz-dev python3-dev build-essential wget unzip && \
    rm -rf /var/lib/apt/lists/*

# --- Python зависимости (слой кэшируется при неизменных requirements) ---
COPY requirements/base.txt /opt/structurizr_backend/requirements/base.txt
RUN python3 -m pip config --user set global.index https://nexus.vimpelcom.ru/repository/proxy__pypi__group/pypi/ && \
    python3 -m pip config --user set global.index-url https://nexus.vimpelcom.ru/repository/proxy__pypi__group/simple/ && \
    python3 -m pip config --user set global.trusted-host nexus.vimpelcom.ru && \
    python3 -m pip install --no-cache-dir -r /opt/structurizr_backend/requirements/base.txt && \
    rm -rf /root/.cache/pip && \
    rm -rf /usr/local/lib/python3.10/dist-packages/__pycache__

# --- Скачиваем Structurizr CLI с GitHub (новая строка вместо COPY build) ---
RUN wget -O /tmp/structurizr.zip https://github.com/structurizr/cli/releases/download/v2025.11.09/structurizr-cli.zip && \
    unzip /tmp/structurizr.zip -d /usr/local/structurizr-cli/ && \
    rm /tmp/structurizr.zip && \
    chmod +x /usr/local/structurizr-cli/structurizr.sh

# --- Certs ---
COPY certs /opt/structurizr_backend/certs
COPY certs/*.crt /usr/local/share/ca-certificates
RUN keytool -importcert -file /opt/structurizr_backend/certs/Vimpelcom_InternalCA_G2.crt -alias Vimpelcom_InternalCA_G2 -storepass changeit -noprompt -trustcacerts -cacerts && \
    keytool -importcert -file /opt/structurizr_backend/certs/Vimpelcom_InternalCA_G3.crt -alias Vimpelcom_InternalCA_G3 -storepass changeit -noprompt -trustcacerts -cacerts && \
    keytool -importcert -file /opt/structurizr_backend/certs/Vimpelcom_RootCA_G2.crt -alias Vimpelcom_RootCA_G2 -storepass changeit -noprompt -trustcacerts -cacerts && \
    keytool -importcert -file /opt/structurizr_backend/certs/apps.yd-m6-kt22.vimpelcom.ru.crt -alias apps.yd-m6-kt22.vimpelcom.ru -storepass changeit -noprompt -trustcacerts -cacerts && \
    keytool -importcert -file /opt/structurizr_backend/certs/vega.vimpelcom.ru.crt -alias vega.vimpelcom.ru -storepass changeit -noprompt -trustcacerts -cacerts && \
    update-ca-certificates

# --- Исходный код (последний слой — изменения кода не инвалидируют pip) ---
COPY . /opt/structurizr_backend

USER root
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /opt/structurizr_backend
CMD [ "python3", "/opt/structurizr_backend/src/main.py" ]