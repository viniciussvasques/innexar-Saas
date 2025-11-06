# Arquitetura Técnica

Componentes principais:

- Servidor principal (Base Admin) para clientes, planos, billing e suporte
- Containers Docker por tenant (ERPNext/Frappe dedicados)
- Banco por tenant em MariaDB (conforme stack ERPNext atual)
- Proxy reverso NGINX/Traefik gerenciando subdomínios
- DNS automático via Cloudflare API
- Integrações de pagamento: Stripe e PagSeguro
- Scripts de automação em Python (criar/pausar/excluir tenants)

Visão de alto nível:

```
Cliente → Proxy (NGINX/Traefik) → Container ERPNext → MariaDB (database do tenant)
                                      ↑
                        Base Admin / API (gestão e billing)
```

Isolamento por tenant:

- Container dedicado para processo ERPNext
- Database PostgreSQL dedicado por cliente
- Subdomínio exclusivo (ex.: cliente.innexar.com)

Orquestração:

- Docker Compose no início; Kubernetes numa fase posterior
- Cloudflare para DNS e TLS (wildcard + automação)

Segurança e rede:

- TLS obrigatório (Cloudflare/Origin)
- db_filter por subdomínio/site
- Usuários e permissões segregados por database
- Backups diários por tenant

