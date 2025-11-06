#!/bin/bash
set -e

# Corrigir permissões do docker.sock se existir
if [ -S /var/run/docker.sock ]; then
    chmod 666 /var/run/docker.sock 2>/dev/null || true
    # Adicionar usuário frappe ao grupo docker se possível
    groupadd docker 2>/dev/null || true
    usermod -aG docker frappe 2>/dev/null || true
fi

# Configurar ambiente
cd /home/frappe/bench-repo

# Ativar o ambiente virtual
source /home/frappe/venv/bin/activate

# Configurar variáveis de ambiente
if [ -z "$DB_HOST" ]; then
    export DB_HOST="db"
fi

if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
    export MYSQL_ROOT_PASSWORD="innexar_root_pass"
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    export ADMIN_PASSWORD="innexar_admin"
fi

if [ -z "$FRAPPE_SITE" ]; then
    export FRAPPE_SITE="innexar.local"
fi

# Configurar o arquivo common_site_config.json
setup_common_site_config() {
    echo "Configurando common_site_config.json..."
    
    cat > /home/frappe/bench-repo/sites/common_site_config.json << EOF
{
    "db_host": "$DB_HOST",
    "db_name": "innexar",
    "db_password": "innexar_pass",
    "db_port": "3306",
    "db_type": "mariadb",
    "db_user": "innexar",
    "redis_cache": "redis://redis-cache:6379",
    "redis_queue": "redis://redis-queue:6379",
    "redis_socketio": "redis://redis-socketio:6379",
    "socketio_port": 9000,
    "auto_update_control_panel": false,
    "dns_multitenant": false,
    "file_watcher_port": 6787,
    "frappe_user": "frappe",
    "gunicorn_workers": 4,
    "webserver_port": 8000,
    "socketio_port": 9000,
    "restart_supervisor_on_update": false,
    "restart_systemd_on_update": false,
    "serve_default_site": true,
    "shallow_clone": true,
    "use_redis_auth": false,
    "developer_mode": 1
}
EOF
}

# Função para inicializar o site
init_site() {
    echo "Inicializando o site $FRAPPE_SITE..."
    
    # Verificar se o banco de dados está acessível
    echo "Verificando conexão com o banco de dados..."
    while ! mysqladmin ping -h"$DB_HOST" -u"root" -p"$MYSQL_ROOT_PASSWORD" --silent; do
        echo "Aguardando o banco de dados..."
        sleep 5
    done
    
    # Criar novo site se não existir
    if [ ! -f "sites/$FRAPPE_SITE/site_config.json" ]; then
        echo "Criando novo site: $FRAPPE_SITE"
        
        echo "Criando site..."
        bench new-site "$FRAPPE_SITE" \
            --db-host "$DB_HOST" \
            --db-name "innexar" \
            --db-password "innexar_pass" \
            --db-root-username "root" \
            --db-root-password "$MYSQL_ROOT_PASSWORD" \
            --admin-password "$ADMIN_PASSWORD" \
            --install-app erpnext \
            --verbose || echo "Aviso: O site pode já existir. Continuando..."
            
        # Instalar aplicativos personalizados (se houver)
        if [ -d "/home/frappe/erpnext-apps" ]; then
            for app in /home/frappe/erpnext-apps/*; do
                if [ -d "$app" ]; then
                    APP_NAME=$(basename "$app")
                    echo "Instalando aplicativo $APP_NAME..."
                    bench --site "$FRAPPE_SITE" install-app "$APP_NAME" || echo "Aviso: Falha ao instalar o aplicativo $APP_NAME"
                fi
            done
        fi
        
        echo "Site $FRAPPE_SITE criado com sucesso!"
    else
        echo "O site $FRAPPE_SITE já existe."
        
        # Atualizar configurações do site existente
        echo "Atualizando configurações do site existente..."
        bench --site "$FRAPPE_SITE" set-config db_host "$DB_HOST"
        bench --site "$FRAPPE_SITE" set-config db_name "innexar"
        bench --site "$FRAPPE_SITE" set-config db_password "innexar_pass"
        bench --site "$FRAPPE_SITE" set-config db_port "3306"
        bench --site "$FRAPPE_SITE" set-config db_type "mariadb"
        bench --site "$FRAPPE_SITE" set-config db_user "innexar"
        bench --site "$FRAPPE_SITE" set-config redis_cache "redis://redis-cache:6379"
        bench --site "$FRAPPE_SITE" set-config redis_queue "redis://redis-queue:6379"
        bench --site "$FRAPPE_SITE" set-config redis_socketio "redis://redis-socketio:6379"
        
        # Migrar o banco de dados se necessário
        echo "Executando migrações..."
        bench --site "$FRAPPE_SITE" migrate || echo "Aviso: Falha ao executar migrações"
    fi
}

# Configuração inicial
setup_common_site_config

# Inicializar o site
init_site

# Função para verificar se o banco de dados está pronto
db_ready() {
    mysqladmin ping -h"$DB_HOST" -u"root" -p"$MYSQL_ROOT_PASSWORD" --silent
}

# Esperar até que o banco de dados esteja pronto
echo "Aguardando o banco de dados estar pronto..."
until db_ready; do
    echo "Banco de dados não está acessível. Aguardando..."
    sleep 5
done

# Função para verificar se a tabela existe
table_exists() {
    mysql -h"$DB_HOST" -u"root" -p"$MYSQL_ROOT_PASSWORD" -e "USE innexar; SHOW TABLES LIKE '$1';" | grep -q "$1"
}

# Verificar se a tabela tabSingles existe
if ! table_exists "tabSingles"; then
    echo "Tabela tabSingles não encontrada. Executando migrações..."
    bench --site "$FRAPPE_SITE" migrate || echo "Aviso: Falha ao executar migrações"
    
    # Verificar novamente após a migração
    if ! table_exists "tabSingles"; then
        echo "Erro: Não foi possível criar a tabela tabSingles. Recriando o site..."
        bench drop-site "$FRAPPE_SITE" --db-root-username root --db-root-password "$MYSQL_ROOT_PASSWORD" --force
        bench new-site "$FRAPPE_SITE" \
            --db-host "$DB_HOST" \
            --db-name "innexar" \
            --db-password "innexar_pass" \
            --db-root-username "root" \
            --db-root-password "$MYSQL_ROOT_PASSWORD" \
            --admin-password "$ADMIN_PASSWORD" \
            --install-app erpnext \
            --verbose
    fi
fi

# Iniciar serviços
case "$1" in
    start)
        echo "Iniciando serviços..."
        # Iniciar o bench em background para evitar que o container morra
        bench start & 
        # Manter o container rodando
        tail -f /dev/null
        ;;
    *)
        exec "$@"
        ;;
esac
