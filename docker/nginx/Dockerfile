FROM nginx:1.21

# Instalar dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar configurações personalizadas do Nginx
COPY ./docker/nginx/conf.d /etc/nginx/conf.d

# Criar diretórios necessários
RUN mkdir -p /var/www/html/sites /var/log/nginx /var/cache/nginx \
    && chown -R www-data:www-data /var/www/html /var/log/nginx /var/cache/nginx /var/run \
    && chmod -R 755 /var/www/html

# Expor portas
EXPOSE 80 443 9000

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
