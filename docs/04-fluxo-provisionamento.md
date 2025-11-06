# Fluxo de Provisionamento de Instâncias

1. Cliente escolhe plano no site Innexar
2. Pagamento processado via Stripe (EUA) ou PagSeguro (Brasil)
3. Execução do script de criação de tenant:
   - Criação do container ERPNext
   - Criação de database MariaDB dedicado
   - Geração de subdomínio (cliente.innexar.com)
   - Configuração inicial (módulos por plano, branding, admin)
   - E-mail de boas-vindas com credenciais
4. Instância ativa e pronta para uso
5. Painel admin controla renovações, logs e métricas

Observações técnicas:

- DNS via Cloudflare API
- Proxy reverso NGINX/Traefik com wildcard
- Webhooks de pagamento para ativação/suspensão automática

