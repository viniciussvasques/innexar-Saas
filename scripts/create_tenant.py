#!/usr/bin/env python3
"""
Script para criação automática de tenants no ambiente Innexar ERP Cloud.

Uso:
    python create_tenant.py --subdomain nome-cliente --plano basico
"""

import argparse
import docker
import requests
import json
import os
from pathlib import Path

# Configurações
BACKEND_CONTAINER_NAME = "innexar-backend"
CORE_IMAGE_NAME = os.environ.get("INNEXAR_CORE_IMAGE", "innexar-platform-backend")
ADMIN_SITE = "innexar.local"
MYSQL_ROOT_PASSWORD = os.environ.get("MYSQL_ROOT_PASSWORD", "innexar_root_pass")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "innexar_admin")

class TenantManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        
    def create_tenant(self, subdomain: str, plan: str, admin_password: str | None = None):
        """Cria um novo tenant iniciando um container dedicado a partir da imagem core."""
        try:
            site = f"{subdomain}.innexar.com"
            db_name = f"tenant_{subdomain}"
            admin_pwd = admin_password or DEFAULT_ADMIN_PASSWORD

            print(f"Criando tenant (container): {site} (DB: {db_name}, Plano: {plan})")

            port = self._get_available_port()
            env_vars = {
                'FRAPPE_SITE': site,
                'SITE_NAME': site,
                'ADMIN_PASSWORD': admin_pwd,
                'DB_HOST': 'db',
                'DB_PORT': '3306',
                'DB_ROOT_USER': 'root',
                'MYSQL_ROOT_PASSWORD': MYSQL_ROOT_PASSWORD,
                'DB_NAME': db_name,
                'INSTALL_APPS': 'erpnext',
                'INSTALL_APPS_DEV': '1',
                'INSTALL_APPS_WAIT': '1',
            }

            container = self.docker_client.containers.run(
                CORE_IMAGE_NAME,
                name=f"erpnext-{subdomain}",
                ports={'8000/tcp': port},
                environment=env_vars,
                network=DOCKER_NETWORK,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )

            # 3) Configurar DNS (Cloudflare)
            self._configure_dns(subdomain)

            # 4) Configurar módulos conforme o plano (placeholder)
            self._configure_plan(site=site, plan=plan)

            return {
                "status": "success",
                "subdomain": site,
                "admin_url": f"http://{site}",
                "container": container.name,
                "port": port,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_backend(self):
        return self.docker_client.containers.get(BACKEND_CONTAINER_NAME)
    
    def _get_available_port(self) -> int:
        # range simples; ideal mover para config
        for port in range(8100, 8400):
            try:
                in_use = any(
                    port in (p.get('HostPort') and int(p['HostPort']) for p in (mp.values() for mp in c.attrs.get('NetworkSettings', {}).get('Ports', {}).values()) if p)
                    for c in self.docker_client.containers.list()
                )
            except Exception:
                in_use = False
            if not in_use:
                return port
        raise RuntimeError("Sem portas livres no range 8100-8399")

    def _bench_install_app(self, site: str, app: str):
        backend = self._get_backend()
        cmd = ["bash", "-lc", f"bench --site {site} install-app {app}"]
        print(f"[bench] install-app {app} on {site}")
        rc, out = backend.exec_run(cmd, demux=True)
        if rc != 0:
            stdout, stderr = out if isinstance(out, tuple) else (out, b"")
            raise RuntimeError(f"bench install-app {app} failed: {stderr.decode(errors='ignore')}")
        return True
    
    def _configure_dns(self, subdomain):
        """Configura o DNS no Cloudflare (implementação simplificada)."""
        # TODO: Implementar integração com API do Cloudflare
        print(f"Configurando DNS para: {subdomain}.innexar.com")

    def _configure_plan(self, site: str, plan: str):
        """Instala apps/módulos conforme o plano (nível de app)."""
        plan = plan.lower()
        # ERPNext já instalado; outras apps podem ser adicionadas aqui quando existirem
        # Exemplo: website/ecommerce para enterprise
        if plan == "enterprise":
            try:
                self._bench_install_app(site=site, app="payments")
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description='Criação de tenant no Innexar ERP Cloud')
    parser.add_argument('--subdomain', required=True, help='Subdomínio do cliente')
    parser.add_argument('--plano', required=True, choices=['basico', 'profissional', 'enterprise'], 
                       help='Plano contratado')
    parser.add_argument('--admin-password', required=False, help='Senha do usuário Administrator do novo site')
    
    args = parser.parse_args()
    
    manager = TenantManager()
    result = manager.create_tenant(args.subdomain, args.plano, admin_password=args.admin_password)
    
    print("\nResultado:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
