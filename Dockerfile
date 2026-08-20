ARG RUN_IMAGE=ubuntu:22.04
FROM ${RUN_IMAGE} as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates-java && \
    apt-get install -y --no-install-recommends openjdk-21-jre-headless python3 pip graphviz graphviz-dev python3-dev build-essential && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*


COPY --chmod=644 certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV LANG=C.UTF-8
ENV PATH=$JAVA_HOME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

ARG PIP_INDEX_URL=''
ENV PIP_INDEX_URL=$PIP_INDEX_URL
ARG PIP_TRUSTED_HOST=''
ENV PIP_TRUSTED_HOST=$PIP_TRUSTED_HOST
COPY requirements/base.txt /opt/structurizr_backend/requirements/base.txt
RUN python3 -m pip install --no-cache-dir -r /opt/structurizr_backend/requirements/base.txt && \
    rm -rf /root/.cache/pip && \
    rm -rf /usr/local/lib/python3.10/dist-packages/__pycache__

ARG STRUCTURIZR_CLI_DISTR=https://github.com/structurizr/cli/releases/download/v2025.11.09/structurizr-cli.zip
RUN apt-get update && apt-get install -y --no-install-recommends wget unzip && \
    wget -O /tmp/structurizr.zip ${STRUCTURIZR_CLI_DISTR} && \
    unzip /tmp/structurizr.zip -d /usr/local/structurizr-cli/ && \
    rm /tmp/structurizr.zip && \
    apt-get purge -y wget unzip && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*  && \
    chmod +x /usr/local/structurizr-cli/structurizr.sh

COPY . /opt/structurizr_backend

USER root
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /opt/structurizr_backend
CMD [ "python3", "/opt/structurizr_backend/src/main.py" ]
