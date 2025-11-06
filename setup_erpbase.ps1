# Script para configurar o ERP Base

# 1. Criar diretórios necessários
$erpbaseDir = "c:\Innexar-saas\innexar-platform\sites\erpbase"
$logsDir = "$erpbaseDir\logs"

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# 2. Iniciar os containers
Write-Host "Iniciando os containers..."
docker-compose up -d

# 3. Aguardar os serviços estarem prontos
Write-Host "Aguardando os serviços estarem prontos..."
Start-Sleep -Seconds 30

# 4. Verificar se o banco de dados está acessível
Write-Host "Verificando conexão com o banco de dados..."
$dbCheck = docker exec -it innexar-backend bash -c "mysql -h db -u root -perpbase_pass -e 'SELECT 1;' 2>&1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao conectar ao banco de dados. Verifique as credenciais e tente novamente."
    exit 1
}

# 5. Criar o banco de dados e o usuário
Write-Host "Configurando banco de dados..."
docker exec -it innexar-backend bash -c "mysql -h db -u root -perpbase_pass -e 'CREATE DATABASE IF NOT EXISTS erpbase;'"
docker exec -it innexar-backend bash -c "mysql -h db -u root -perpbase_pass -e \"CREATE USER IF NOT EXISTS 'erpbase_user'@'%' IDENTIFIED BY 'erpbase_pass';\""
docker exec -it innexar-backend bash -c "mysql -h db -u root -perpbase_pass -e 'GRANT ALL PRIVILEGES ON erpbase.* TO \"erpbase_user\"@\"%\";'"
docker exec -it innexar-backend bash -c "mysql -h db -u root -perpbase_pass -e 'FLUSH PRIVILEGES;'"

# 6. Inicializar o site
Write-Host "Inicializando o site erpbase.local..."
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench new-site erpbase.local --db-root-password erpbase_pass --admin-password erpbase_admin --mariadb-root-username root --mariadb-root-password erpbase_pass --install-app erpnext"

# 7. Configurar o domínio
Write-Host "Configurando domínio..."
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench --site erpbase.local add-to-hosts"

# 8. Instalar o módulo de gerenciamento
Write-Host "Instalando módulo de gerenciamento..."
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench --site erpbase.local install-app saas_management"

# 9. Reconstruir os assets
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench --site erpbase.local build"

# 10. Reiniciar os serviços
docker-compose restart

Write-Host "`nERP Base configurado com sucesso!"
Write-Host "Acesse: http://erpbase.local:8000"
Write-Host "Usuário: Administrator"
Write-Host "Senha: erpbase_admin"
