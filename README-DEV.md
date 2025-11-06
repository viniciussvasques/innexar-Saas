# Configuração do Ambiente de Desenvolvimento Innexar Platform

Este guia explica como configurar o ambiente de desenvolvimento local para o ERPNext, que será a base da Innexar Platform.

## Pré-requisitos

- Windows 10/11
- Git
- Docker Desktop (composed habilitado)

Observação: Redis, banco de dados e serviços são provisionados via Docker Compose.

## Configuração do Ambiente

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/innexar/innexar-platform.git
   cd innexar-platform
   ```

2. **Subir os serviços com Docker Compose**
   Abra o PowerShell e execute:
   ```powershell
   docker compose up -d --build
   ```
   Isso irá subir:
   - Redis (cache, fila, socketio)
   - Banco de dados (MariaDB, configuração atual)
   - Backend Frappe/ERPNext
   - Nginx (porta 80/443)

3. **Verificar status**
   ```powershell
   docker compose ps
   ```

4. **Acessar o sistema**
   - Via Nginx: http://localhost
   - Backend direto: http://localhost:8000
   - Usuário: Administrator
   - Senha: definida pela variável de ambiente `ADMIN_PASSWORD` (padrão atual: `innexar_admin`)

## Estrutura do Projeto

- `/docker` - Dockerfiles e configs (backend, nginx)
- `/config` - Configurações (ex.: `mariadb.cnf`)
- `/sites` - Configs de site (ex.: `erpbase`)
- `/docs` - Documentação
- `docker-compose.yml` - Orquestração local

## Desenvolvimento

### Atualizar serviços e rebuild

```powershell
docker compose pull
docker compose build --no-cache
docker compose up -d
```

### Desenvolvimento de apps (opcional)

Para criar apps custom, utilize o ambiente do container backend via `docker compose exec` e os comandos `bench`. 

### Desenvolver e testar

1. Suba os serviços com `docker compose up -d`
2. Acesse em http://localhost (Nginx) ou http://localhost:8000 (backend)

## Solução de Problemas

### Erro de permissão
Se encontrar erros de permissão, tente executar o PowerShell como administrador.

### Problemas com dependências
Caso algum serviço falhe no build, rode:
```powershell
docker compose build --no-cache
docker compose up -d
docker compose logs -f backend
```

Observação: A stack atual utiliza MariaDB. O roadmap de produção prevê bancos PostgreSQL dedicados por tenant.

## Contribuição

1. Crie um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das alterações (`git commit -am 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.
