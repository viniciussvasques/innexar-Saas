# Módulo de Gerenciamento SaaS para ERPNext

Este módulo adiciona recursos de multi-tenancy ao ERPNext, permitindo a criação e gerenciamento de múltiplos tenants com containers dedicados.

## Recursos Principais

- Criação e gerenciamento de planos SaaS personalizáveis
- Provisionamento automático de containers Docker para cada tenant
- Controle de recursos por plano (CPU, memória, armazenamento)
- Gerenciamento de usuários e permissões
- Monitoramento de uso de recursos
- APIs para integração com outros sistemas

## Requisitos

- ERPNext 14.x ou superior
- Docker e Docker Compose instalados no servidor
- Acesso root/sudo ao servidor
- Python 3.7+

## Instalação

1. Copie a pasta `saas_management` para o diretório `apps` do seu ambiente ERPNext
2. Execute o comando para instalar o módulo:
   ```bash
   bench --site your-site.local install-app saas_management
   ```
3. Execute as migrações do banco de dados:
   ```bash
   bench --site your-site.local migrate
   ```
4. Reinicie o servidor ERPNext:
   ```bash
   bench restart
   ```

## Configuração

1. Acesse o ERPNext como administrador
2. Vá para `Configurações > Módulos > SaaS Management`
3. Configure as opções globais do módulo
4. Crie seus planos de assinatura

## Uso Básico

### Criando um Plano

1. Vá para `SaaS Management > Planos > Novo`
2. Preencha os detalhes do plano (nome, código, preço, etc.)
3. Defina os limites de recursos (usuários, armazenamento, etc.)
4. Salve o plano

### Criando um Tenant

1. Vá para `SaaS Management > Tenants > Novo`
2. Preencha os detalhes do cliente
3. Selecione um plano
4. Clique em "Salvar" para criar o tenant
5. Clique em "Criar Container" para provisionar o ambiente

### Gerenciando Containers

- **Iniciar**: Inicia o container do tenant
- **Parar**: Para o container do tenant
- **Reiniciar**: Reinicia o container
- **Excluir**: Remove o container e os dados associados

## API

O módulo inclui endpoints RESTful para integração com outros sistemas:

### Criar um Tenant

```
POST /api/method/saas_management.api.create_tenant
```

**Parâmetros:**
```json
{
    "subdomain": "meutenant",
    "plan": "BASIC",
    "admin_email": "admin@example.com",
    "admin_password": "senha_segura",
    "company_name": "Minha Empresa"
}
```

### Obter Status de um Tenant

```
GET /api/method/saas_management.api.get_tenant_status?tenant=meutenant
```

## Personalização

### Adicionando Novos Módulos

1. Adicione um novo campo booleano no DocType `SAAS Plan`
2. Atualize o método `get_plan_config` em `saas_plan.py`
3. Atualize a lógica de provisionamento em `saas_tenant.py`

### Personalizando Recursos

Você pode modificar os recursos padrão editando os planos existentes ou criando novos planos com configurações personalizadas.

## Solução de Problemas

### Erro ao Criar Container

- Verifique se o Docker está em execução
- Verifique as permissões do usuário
- Verifique os logs do Docker para mais detalhes

### Acesso ao Tenant Falhando

- Verifique se o container está em execução
- Verifique as configurações de rede e portas
- Verifique os logs do container

## Suporte

Para suporte, entre em contato com a equipe de desenvolvimento em suporte@innexar.com.br

## Licença

MIT
