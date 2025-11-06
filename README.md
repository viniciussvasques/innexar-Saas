<div align="center">
    <h1>Innexar Platform</h1>
    <p align="center">
        <p>ERP personalizado baseado no ERPNext para a Innexar</p>
    </p>

![Innexar Platform](https://via.placeholder.com/600x200.png?text=Innexar+Platform)

</div>

## 🚀 Visão Geral
A Innexar Platform é uma solução ERP personalizada baseada no ERPNext, desenvolvida para atender às necessidades específicas da Innexar e seus clientes.

## 🛠️ Primeiros Passos

### ✅ Pré-requisitos
- Docker Desktop para Windows
- Git
- PowerShell 5.1 ou superior

### 🚀 Iniciando o Ambiente

1. **Clonar o repositório** (se ainda não tiver feito):
   ```powershell
   git clone https://github.com/Innexar/innexar-platform.git
   cd innexar-platform
   ```

2. **Iniciar o ambiente** (pode demorar na primeira execução):
   ```powershell
   .\start-dev.ps1
   ```
   > Nota: Na primeira execução, o script irá:
   > 1. Verificar e instalar dependências
   > 2. Baixar as imagens Docker necessárias
   > 3. Configurar o banco de dados
   > 4. Iniciar todos os serviços

3. **Acessar o sistema**:
   - URL: http://localhost:8000
   - Usuário: Administrator
   - Senha: innexar_admin

## 🏗️ Estrutura do Projeto

```
innexar-platform/
├── apps/                    # Aplicativos personalizados
├── config/                 # Configurações do ambiente
│   └── mariadb.cnf         # Configuração do MariaDB
├── docker/                 # Configurações Docker
│   ├── backend/           # Configurações do backend
│   └── nginx/             # Configurações do Nginx
├── logs/                  # Logs da aplicação
├── sites/                 # Sites e arquivos de configuração
├── docker-compose.yml     # Configuração do Docker Compose
└── start-dev.ps1         # Script de inicialização
```

## 🛠️ Comandos Úteis

- **Reiniciar containers**:
  ```powershell
  docker-compose restart
  ```

- **Visualizar logs**:
  ```powershell
  docker-compose logs -f
  ```

- **Acessar terminal do container backend**:
  ```powershell
  docker-compose exec backend bash
  ```

- **Criar backup**:
  ```powershell
  docker-compose exec backend bench --site innexar.local backup
  ```

- **Atualizar aplicativos**:
  ```powershell
  docker-compose exec backend bench --site innexar.local migrate
  ```

## 🔄 Desenvolvimento

### Criar um novo aplicativo
```powershell
docker-compose exec backend bench new-app innexar_novo_app
```

### Instalar um aplicativo
```powershell
docker-compose exec backend bench --site innexar.local install-app innexar_novo_app
```

## 📄 Licença
Proprietário - Todos os direitos reservados © 2025 Innexar Platform

### Containerized Installation

Use docker to deploy ERPNext in production or for development of [Frappe](https://github.com/frappe/frappe) apps. See https://github.com/frappe/frappe_docker for more details.

### Manual Install

The Easy Way: our install script for bench will install all dependencies (e.g. MariaDB). See https://github.com/frappe/bench for more details.

New passwords will be created for the ERPNext "Administrator" user, the MariaDB root user, and the frappe user (the script displays the passwords and saves them to ~/frappe_passwords.txt).


## Learning and community

1. [Frappe School](https://frappe.school) - Learn Frappe Framework and ERPNext from the various courses by the maintainers or from the community.
2. [Official documentation](https://docs.erpnext.com/) - Extensive documentation for ERPNext.
3. [Discussion Forum](https://discuss.erpnext.com/) - Engage with community of ERPNext users and service providers.
4. [Telegram Group](https://t.me/erpnexthelp) - Get instant help from huge community of users.


## Contributing

1. [Issue Guidelines](https://github.com/frappe/erpnext/wiki/Issue-Guidelines)
1. [Report Security Vulnerabilities](https://erpnext.com/security)
1. [Pull Request Requirements](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)
1. [Translations](https://translate.erpnext.com)


## License

GNU/General Public License (see [license.txt](license.txt))

The ERPNext code is licensed as GNU General Public License (v3) and the Documentation is licensed as Creative Commons (CC-BY-SA-3.0) and the copyright is owned by Frappe Technologies Pvt Ltd (Frappe) and Contributors.

By contributing to ERPNext, you agree that your contributions will be licensed under its GNU General Public License (v3).

## Logo and Trademark Policy

Please read our [Logo and Trademark Policy](TRADEMARK_POLICY.md).
