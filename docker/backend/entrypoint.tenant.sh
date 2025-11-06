#!/bin/bash
# Não usar set -e para evitar loop de reinicialização
# set -e

# Configurar permissões do Docker socket se existir
if [ -e /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
    sudo usermod -aG docker frappe 2>/dev/null || true
fi

# Configuração do site
export SITE_NAME="${FRAPPE_SITE:-tenant.innexar.local}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
export DB_HOST="${DB_HOST:-db}"
export DB_PORT="${DB_PORT:-3306}"
export DB_ROOT_USER="${DB_ROOT_USER:-root}"
export MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root123}"

# Aguardar o MariaDB estar pronto
echo "Aguardando MariaDB..."
while ! mysql -h $DB_HOST -P $DB_PORT -u $DB_ROOT_USER -p$MYSQL_ROOT_PASSWORD -e "SELECT 1" >/dev/null 2>&1; do
    echo "MariaDB ainda não está pronto..."
    sleep 3
done

echo "MariaDB está pronto!"

cd /home/frappe/bench-repo

# Ativar ambiente virtual
if [ -f /home/frappe/bench-repo/env/bin/activate ]; then
    source /home/frappe/bench-repo/env/bin/activate
elif [ -f /home/frappe/venv/bin/activate ]; then
    source /home/frappe/venv/bin/activate
fi

# Garantir que estamos no diretório correto
export BENCH_PATH="/home/frappe/bench-repo"
export PATH="/home/frappe/bench-repo/env/bin:$PATH"

# Verificar se o site já existe
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Criando novo site: $SITE_NAME"
    
    # Criar banco de dados se não existir
    DB_NAME="${DB_NAME:-tenant_${SITE_NAME%%.*}}"
    echo "Criando banco de dados: $DB_NAME"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" || true
    
    # Criar site com opções corretas
    # Usar bench diretamente do PATH do ambiente virtual
    cd /home/frappe/bench-repo
    
    echo "Executando bench new-site com as seguintes opções:"
    echo "  Site: $SITE_NAME"
    echo "  DB Host: $DB_HOST"
    echo "  DB Port: $DB_PORT"
    echo "  DB Name: $DB_NAME"
    
    # Usar o caminho completo do bench para evitar problemas com PATH
    BENCH_CMD="/home/frappe/bench-repo/env/bin/bench"
    if [ ! -f "$BENCH_CMD" ]; then
        BENCH_CMD="bench"
    fi
    
    # Verificar e corrigir apps.txt - garantir que está correto (tanto na raiz quanto no site)
    echo "Verificando e corrigindo apps.txt..."
    
    # Criar apps.txt limpo na raiz do bench-repo
    if [ ! -f "/home/frappe/bench-repo/apps.txt" ] || grep -q "^-e" /home/frappe/bench-repo/apps.txt || ! grep -q "^frappe$" /home/frappe/bench-repo/apps.txt; then
        echo "Corrigindo apps.txt na raiz (removendo '-e' e garantindo conteúdo correto)..."
        cat > /home/frappe/bench-repo/apps.txt << EOF
frappe
erpnext
innexar_core
EOF
        echo "apps.txt corrigido na raiz. Conteúdo:"
        cat /home/frappe/bench-repo/apps.txt
    else
        # Garantir que innexar_core está presente na raiz
        if ! grep -q "^innexar_core$" /home/frappe/bench-repo/apps.txt; then
            echo "innexar_core" >> /home/frappe/bench-repo/apps.txt
            echo "innexar_core adicionado ao apps.txt na raiz"
        fi
    fi
    
    # Também garantir que apps.txt do site está correto (se o site já existir)
    if [ -d "sites/$SITE_NAME" ]; then
        SITE_APPS_TXT="sites/$SITE_NAME/apps.txt"
        if [ ! -f "$SITE_APPS_TXT" ] || ! grep -q "^innexar_core$" "$SITE_APPS_TXT" 2>/dev/null; then
            echo "Garantindo que innexar_core está no apps.txt do site..."
            # Copia o apps.txt da raiz para o site
            cp /home/frappe/bench-repo/apps.txt "$SITE_APPS_TXT" 2>/dev/null || {
                # Se não existir, cria
                cat > "$SITE_APPS_TXT" << EOF
frappe
erpnext
innexar_core
EOF
            }
            echo "apps.txt do site atualizado. Conteúdo:"
            cat "$SITE_APPS_TXT"
        fi
    fi
    
    # Criar site sem instalar apps primeiro (para evitar problemas)
    if ! "$BENCH_CMD" new-site "$SITE_NAME" \
        --db-host "$DB_HOST" \
        --db-port "$DB_PORT" \
        --db-name "$DB_NAME" \
        --db-root-username "$DB_ROOT_USER" \
        --db-root-password "$MYSQL_ROOT_PASSWORD" \
        --admin-password "$ADMIN_PASSWORD" \
        --no-mariadb-socket \
        --force 2>&1; then
        echo "Erro ao criar site. Verificando se já existe..."
        if [ -d "sites/$SITE_NAME" ]; then
            echo "Site $SITE_NAME já existe, continuando..."
        else
            echo "Falha ao criar site! Container continuará em modo de espera."
            # Não fazer exit 1 para evitar loop de reinicialização
            # Em vez disso, manter container rodando para debug
            tail -f /dev/null
        fi
    else
        echo "Site $SITE_NAME criado com sucesso!"
    fi
    
    # Instalar apps se não foram instalados durante a criação
    if ! "$BENCH_CMD" --site "$SITE_NAME" list-apps 2>/dev/null | grep -q "erpnext"; then
        echo "Instalando ERPNext..."
        "$BENCH_CMD" --site "$SITE_NAME" install-app erpnext || echo "Aviso: Falha ao instalar erpnext"
    fi
    
    if ! "$BENCH_CMD" --site "$SITE_NAME" list-apps 2>/dev/null | grep -q "innexar_core"; then
        echo "Instalando Innexar Core..."
        "$BENCH_CMD" --site "$SITE_NAME" install-app innexar_core || echo "Aviso: Falha ao instalar innexar_core"
    fi
    
    # Configurar site
    "$BENCH_CMD" --site "$SITE_NAME" set-config developer_mode 1
else
    echo "Site $SITE_NAME já existe"
fi

# Verificar se o site foi criado antes de continuar
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "ERRO: Site $SITE_NAME não foi criado. Container entrará em modo de espera para debug."
    echo "Execute 'docker exec -it <container> bash' para investigar o problema."
    tail -f /dev/null
    exit 0
fi

# Configurar site padrão
"$BENCH_CMD" use "$SITE_NAME" || {
    echo "ERRO: Não foi possível usar o site $SITE_NAME"
    tail -f /dev/null
    exit 0
}

# Compilar assets se necessário
if [ ! -d "sites/assets" ] || [ -z "$(ls -A sites/assets 2>/dev/null)" ]; then
    echo "Compilando assets..."
    "$BENCH_CMD" build || echo "Aviso: Falha ao compilar assets"
fi

# Executar comando
case "$1" in
    "start")
        echo "Iniciando servidor Frappe..."
        # Configurar site antes de iniciar
        export FRAPPE_SITE="$SITE_NAME"
        cd /home/frappe/bench-repo
        "$BENCH_CMD" use "$SITE_NAME"
        # bench serve aceita apenas --port (escuta em 0.0.0.0 por padrão em container)
        "$BENCH_CMD" serve --port 8000 || {
            echo "ERRO: Falha ao iniciar servidor. Container entrará em modo de espera."
            tail -f /dev/null
        }
        ;;
    "worker")
        echo "Iniciando worker..."
        "$BENCH_CMD" worker || {
            echo "ERRO: Falha ao iniciar worker. Container entrará em modo de espera."
            tail -f /dev/null
        }
        ;;
    "schedule")
        echo "Iniciando scheduler..."
        "$BENCH_CMD" schedule || {
            echo "ERRO: Falha ao iniciar scheduler. Container entrará em modo de espera."
            tail -f /dev/null
        }
        ;;
    "watch")
        echo "Iniciando watch..."
        "$BENCH_CMD" watch || {
            echo "ERRO: Falha ao iniciar watch. Container entrará em modo de espera."
            tail -f /dev/null
        }
        ;;
    *)
        exec "$@"
        ;;
esac
