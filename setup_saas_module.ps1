# Script para configurar o módulo SaaS Management no ERPNext

# 1. Iniciar os containers
docker-compose up -d

# 2. Aguardar os serviços estarem prontos
Write-Host "Aguardando os serviços estarem prontos..."
Start-Sleep -Seconds 30

# 3. Verificar se o banco de dados está acessível
$dbCheck = docker exec -it innexar-backend bash -c "mysql -h db -u root -pinnexar_root_pass -e 'SELECT 1;' 2>&1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao conectar ao banco de dados. Verifique as credenciais e tente novamente."
    exit 1
}

# 4. Criar o banco de dados e o usuário se não existirem
docker exec -it innexar-backend bash -c "mysql -h db -u root -pinnexar_root_pass -e 'CREATE DATABASE IF NOT EXISTS innexar;'"
docker exec -it innexar-backend bash -c "mysql -h db -u root -pinnexar_root_pass -e \"CREATE USER IF NOT EXISTS 'innexar'@'%' IDENTIFIED BY 'innexar_pass';\""
docker exec -it innexar-backend bash -c "mysql -h db -u root -pinnexar_root_pass -e 'GRANT ALL PRIVILEGES ON innexar.* TO \"innexar\"@\"%\";'"
docker exec -it innexar-backend bash -c "mysql -h db -u root -pinnexar_root_pass -e 'FLUSH PRIVILEGES;'"

# 5. Criar diretório para o módulo
$moduleDir = "c:\Innexar-saas\innexar-platform\apps\saas_management"
if (-not (Test-Path $moduleDir)) {
    New-Item -ItemType Directory -Path $moduleDir -Force | Out-Null
}

# 6. Copiar os arquivos do módulo
$sourceDir = "c:\Innexar-saas\innexar-core\saas_management\*"
Copy-Item -Path $sourceDir -Destination $moduleDir -Recurse -Force

# 7. Instalar o módulo
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench --site innexar.local install-app saas_management"

# 8. Reconstruir os assets
docker exec -it innexar-backend bash -c "cd /home/frappe/bench-repo && bench --site innexar.local build"

# 9. Reiniciar os serviços
docker-compose restart

Write-Host "`nConfiguração concluída!"
Write-Host "Acesse o ERPNext em: http://localhost:8000"
Write-Host "Usuário: Administrator"
Write-Host "Senha: innexar_admin"
