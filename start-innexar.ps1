# Script para iniciar o ambiente Innexar

# 1. Parar e remover containers existentes
Write-Host "[1/6] Parando e removendo containers existentes..."
docker-compose down -v

# 2. Iniciar serviços essenciais
Write-Host "[2/6] Iniciando serviços essenciais (banco de dados e Redis)..."
docker-compose up -d db redis-cache redis-queue redis-socketio

# 3. Aguardar o banco de dados estar pronto
Write-Host "[3/6] Aguardando o banco de dados estar pronto..."
Start-Sleep -Seconds 30

# 4. Iniciar o backend
Write-Host "[4/6] Iniciando o backend..."
docker-compose up -d backend

# 5. Aguardar o backend estar pronto
Write-Host "[5/6] Aguardando o backend estar pronto..."
Start-Sleep -Seconds 30

# 6. Iniciar os demais serviços
Write-Host "[6/6] Iniciando todos os serviços..."
docker-compose up -d

# 7. Mostrar status dos containers
Write-Host "`nStatus dos containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 8. Mostrar informações de acesso
Write-Host "`nAcesso ao sistema:"
Write-Host "- URL: http://innexar.local:8000"
Write-Host "- Usuário: Administrator"
Write-Host "- Senha: innexar_admin"

Write-Host "`nSe a senha não funcionar, você pode redefini-la com o comando:"
Write-Host "docker exec -it innexar-backend bench --site innexar.local set-admin-password nova_senha"
