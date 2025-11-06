# Script de Inicialização do Ambiente de Desenvolvimento Innexar Platform

# Função para verificar e instalar dependências
function Install-RequiredSoftware {
    # Verificar se o Docker está instalado
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "Docker não encontrado. Por favor, instale o Docker Desktop para Windows." -ForegroundColor Red
        Write-Host "Baixe em: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }

    # Verificar se o Docker Compose está instalado
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Host "Docker Compose não encontrado. Instalando..." -ForegroundColor Yellow
        # O Docker Compose geralmente vem com o Docker Desktop para Windows
        # Se não estiver disponível, tente reinstalar o Docker Desktop
        Write-Host "Por favor, reinstale o Docker Desktop para garantir que o Docker Compose seja instalado corretamente." -ForegroundColor Red
        exit 1
    }

    # Verificar se o Git está instalado
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "Git não encontrado. Instalando..." -ForegroundColor Yellow
        winget install --id Git.Git -e --source winget
        Write-Host "Git instalado com sucesso!" -ForegroundColor Green
        Write-Host "Por favor, reinicie o terminal e execute este script novamente." -ForegroundColor Yellow
        exit 0
    }

    # Verificar se o Python 3.10+ está instalado
    $pythonVersion = python --version 2>&1
    if (-not ($pythonVersion -match "Python 3.1[0-9]" -or $pythonVersion -match "Python 3.2[0-9]")) {
        Write-Host "Python 3.10+ não encontrado. Instalando..." -ForegroundColor Yellow
        winget install --id Python.Python.3.10 --exact
        Write-Host "Python 3.10 instalado com sucesso!" -ForegroundColor Green
        Write-Host "Por favor, reinicie o terminal e execute este script novamente." -ForegroundColor Yellow
        exit 0
    }

    # Verificar se o Node.js está instalado
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "Node.js não encontrado. Instalando..." -ForegroundColor Yellow
        winget install OpenJS.NodeJS.LTS
        Write-Host "Node.js instalado com sucesso!" -ForegroundColor Green
        Write-Host "Por favor, reinicie o terminal e execute este script novamente." -ForegroundColor Yellow
        exit 0
    }

    # Verificar se o Yarn está instalado
    if (-not (Get-Command yarn -ErrorAction SilentlyContinue)) {
        Write-Host "Yarn não encontrado. Instalando..." -ForegroundColor Yellow
        npm install -g yarn
        Write-Host "Yarn instalado com sucesso!" -ForegroundColor Green
    }
}

# Verificar e instalar dependências
Write-Host "Verificando dependências..." -ForegroundColor Cyan
Install-RequiredSoftware

# Verificar se o Docker Compose está instalado
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose não encontrado. Por favor, instale o Docker Desktop para Windows." -ForegroundColor Red
    exit 1
}

# Verificar se o diretório do projeto está configurado corretamente
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Arquivo docker-compose.yml não encontrado. Certifique-se de que você está no diretório correto." -ForegroundColor Red
    exit 1
}

# Verificar se o diretório erpnext existe
if (-not (Test-Path "erpnext")) {
    Write-Host "Diretório 'erpnext' não encontrado. Clonando o repositório do ERPNext..." -ForegroundColor Yellow
    git clone --depth 1 --branch version-14 https://github.com/frappe/erpnext.git
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro ao clonar o repositório do ERPNext." -ForegroundColor Red
        exit 1
    }
}

# Criar diretórios necessários
$directories = @("sites", "apps", "logs/nginx")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Verificar se o arquivo de configuração do MariaDB existe
if (-not (Test-Path "config/mariadb.cnf")) {
    # Criar diretório de configuração se não existir
    if (-not (Test-Path "config")) {
        New-Item -ItemType Directory -Path "config" -Force | Out-Null
    }
    
    # Criar arquivo de configuração padrão para o MariaDB
    @"
[mysqld]
innodb-file-format=Barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
"@ | Out-File -FilePath "config/mariadb.cnf" -Encoding utf8
}

# Iniciar os containers Docker
Write-Host "Iniciando os containers Docker..." -ForegroundColor Cyan
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao iniciar os containers Docker. Verifique os logs para mais detalhes." -ForegroundColor Red
    exit 1
}

# Verificar se os containers estão em execução
$containers = @("innexar-db", "innexar-backend", "innexar-frontend", "innexar-worker", "innexar-scheduler")
$allContainersRunning = $true

foreach ($container in $containers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>&1
    
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($status)) {
        Write-Host "Container $container não está em execução." -ForegroundColor Red
        $allContainersRunning = $false
    } else {
        Write-Host "$container está $status" -ForegroundColor Green
    }
}

if (-not $allContainersRunning) {
    Write-Host "Alguns containers não estão em execução. Verifique os logs com 'docker-compose logs' para mais detalhes." -ForegroundColor Red
    exit 1
}

# Aguardar o banco de dados estar pronto
Write-Host "Aguardando o banco de dados ficar pronto..." -ForegroundColor Cyan
$dbReady = $false
$attempts = 0
$maxAttempts = 30

while (-not $dbReady -and $attempts -lt $maxAttempts) {
    $dbStatus = docker exec innexar-db mysqladmin ping -h localhost -u root -pinnexar_root_pass --silent 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $dbReady = $true
        Write-Host "Banco de dados pronto!" -ForegroundColor Green
    } else {
        $attempts++
        Write-Host "Aguardando banco de dados... ($attempts/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $dbReady) {
    Write-Host "Não foi possível conectar ao banco de dados. Verifique os logs com 'docker-compose logs db' para mais detalhes." -ForegroundColor Red
    exit 1
}

# Criar o site se não existir
$siteName = "innexar.local"
$sitePath = "sites/$siteName"

if (-not (Test-Path $sitePath)) {
    Write-Host "Criando site $siteName..." -ForegroundColor Cyan
    
    # Criar o site
    docker-compose exec -T backend bash -c "cd /home/frappe/bench-repo && bench new-site $siteName --db-name innexar --db-password innexar_pass --admin-password innexar_admin --mariadb-root-username root --mariadb-root-password innexar_root_pass --install-app erpnext"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro ao criar o site. Verifique os logs com 'docker-compose logs backend' para mais detalhes." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Site $siteName criado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "O site $siteName já existe. Iniciando..." -ForegroundColor Green
}

# Iniciar o servidor de desenvolvimento
Write-Host "Iniciando o servidor de desenvolvimento..." -ForegroundColor Cyan
Write-Host "Acesse: http://localhost:8000" -ForegroundColor Green
Write-Host "Usuário: Administrator" -ForegroundColor Green
Write-Host "Senha: innexar_admin" -ForegroundColor Green

# Mostrar logs em tempo real
docker-compose logs -f

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "  Ambiente de Desenvolvimento Innexar Platform" -ForegroundColor Green
Write-Host "  URL: http://localhost:8000" -ForegroundColor White
Write-Host "  Usuário: Administrator" -ForegroundColor White
Write-Host "  Senha: innexar_admin" -ForegroundColor White
Write-Host "`n  Comandos úteis:" -ForegroundColor Yellow
Write-Host "  - Visualizar logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  - Parar ambiente: docker-compose down" -ForegroundColor Gray
Write-Host "  - Acessar terminal: docker-compose exec backend bash" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Green

# Abrir o navegador
Start-Process "http://localhost:8000"
