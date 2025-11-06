FROM python:3.10-slim-bullseye

# Variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive \
    FRAPPE_USER=frappe \
    FRAPPE_PASSWORD=innexar_pass \
    FRAPPE_ADMIN_EMAIL=admin@innexar.com \
    FRAPPE_ADMIN_PASSWORD=innexar_admin \
    FRAPPE_SITE=innexar.local \
    SITE_NAME_PREFIX=innexar \
    BENCH_PATH=/home/frappe/bench-repo \
    BENCH_BRANCH=version-14 \
    BENCH_UPDATE_PACKAGES=true \
    INSTALL_APPS=erpnext \
    INSTALL_APPS_DEV=1 \
    INSTALL_APPS_WAIT=1

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-venv \
    python3-wheel \
    software-properties-common \
    mariadb-client \
    libmariadb-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libxslt1.1 \
    libxslt1-dev \
    libpq-dev \
    xz-utils \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Instalar o wkhtmltopdf manualmente
RUN apt-get update && \
    apt-get install -y --no-install-recommends xfonts-75dpi xfonts-base && \
    wget -O /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb && \
    dpkg -i /tmp/wkhtmltox.deb || apt-get install -yf && \
    rm -f /tmp/wkhtmltox.deb && \
    rm -rf /var/lib/apt/lists/*

# Configurar usuário e diretórios
RUN useradd -ms /bin/bash frappe && \
    mkdir -p /home/frappe/bench-repo && \
    chown -R frappe:frappe /home/frappe

# Instalar bench
RUN pip3 install --no-cache-dir frappe-bench

# Configurar o ambiente
USER frappe
WORKDIR /home/frappe

# Criar diretório para o código-fonte
RUN mkdir -p /home/frappe/erpnext

# Copiar o código-fonte do ERPNext para o diretório correto
COPY --chown=frappe:frappe . /home/frappe/erpnext/

# Inicializar o ambiente bench com o frappe
RUN bench init --skip-redis-config-generation --frappe-branch version-14 --frappe-path /home/frappe/erpnext bench-repo

# Navegar para o diretório do bench
WORKDIR /home/frappe/bench-repo

# Ativar o ambiente virtual e instalar o ERPNext
RUN . /home/frappe/bench-repo/env/bin/activate && \
    pip install --upgrade pip && \
    pip install -e /home/frappe/erpnext && \
    bench get-app erpnext /home/frappe/erpnext

# Copiar scripts de inicialização
COPY --chown=frappe:frappe ./docker/backend/entrypoint.sh /home/frappe/entrypoint.sh
RUN chmod +x /home/frappe/entrypoint.sh

# Expor portas
EXPOSE 8000 9000

# Definir diretório de trabalho
WORKDIR /home/frappe/bench-repo

# Comando de inicialização
ENTRYPOINT ["/home/frappe/entrypoint.sh"]
CMD ["start"]
