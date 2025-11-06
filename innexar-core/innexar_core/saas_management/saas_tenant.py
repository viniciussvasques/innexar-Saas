# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import docker
import json
import random
import string
import time
import os
from datetime import datetime
from .utils.bench_exec import bench_new_site, bench_install_app
from .utils.bench_exec import run_bench

BACKEND_CONTAINER_NAME = os.environ.get("BACKEND_CONTAINER_NAME", "innexar-backend")
CORE_IMAGE_NAME = os.environ.get("INNEXAR_CORE_IMAGE", "innexar-platform-backend")
MYSQL_ROOT_PASSWORD = os.environ.get("MYSQL_ROOT_PASSWORD", "innexar_root_pass")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "innexar_admin")


class SAASTenant(Document):
    def validate(self):
        self.validate_subdomain()
        self.validate_plan()
    
    def validate_subdomain(self):
        # Remove caracteres inválidos do subdomínio
        import re
        self.subdomain = re.sub(r'[^a-z0-9-]', '', self.subdomain.lower())
        
        # Verifica se o subdomínio já existe
        if frappe.db.exists("SAAS Tenant", {"subdomain": self.subdomain, "name": ["!=", self.name]}):
            frappe.throw(f"O subdomínio {self.subdomain} já está em uso. Por favor, escolha outro.")
    
    def validate_plan(self):
        if not frappe.db.exists("SAAS Plan", self.plan):
            frappe.throw("O plano selecionado não existe.")
    
    def before_save(self):
        if not self.admin_password:
            self.admin_password = self.generate_password()
    
    def after_insert(self):
        # Cria container dedicado por tenant
        self.create_container()
    
    def on_trash(self):
        # Remove o container se existir
        if self.container_id:
            self.delete_container()
    
    def generate_password(self, length=12):
        """Gera uma senha aleatória"""
        chars = string.ascii_letters + string.digits + '!@#$%^&*()'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def create_container(self):
        """Cria um container Docker dedicado para o tenant e provisiona o site."""
        try:
            client = docker.from_env()
            plan = frappe.get_doc("SAAS Plan", self.plan)
            site = self._build_site_fqdn()
            db_name = f"tenant_{self.subdomain}"
            admin_password = self.admin_password or DEFAULT_ADMIN_PASSWORD

            # escolher porta disponível
            port = self.get_available_port()

            env_vars = {
                'FRAPPE_SITE': site,
                'SITE_NAME': site,
                'ADMIN_PASSWORD': admin_password,
                'DB_HOST': 'db',
                'DB_PORT': '3306',
                'DB_ROOT_USER': 'root',
                'MYSQL_ROOT_PASSWORD': MYSQL_ROOT_PASSWORD,
                'DB_NAME': db_name,
                'INSTALL_APPS': 'erpnext',
                'INSTALL_APPS_DEV': '1',
                'INSTALL_APPS_WAIT': '1',
            }

            container_name = f"innexar-{self.subdomain}"
            container = client.containers.run(
                CORE_IMAGE_NAME,
                name=container_name,
                ports={'8000/tcp': port},
                environment=env_vars,
                detach=True,
                restart_policy={"Name": "always"},
                network='innexar-network',
            )

            # pós-setup: aplicar apps adicionais e brand/idiomas via backend compartilhado
            self._apply_plan_apps(site)
            self._apply_brand_and_languages(site)

            # Atualiza status
            self.container_id = container.id
            self.container_name = container_name
            self.container_port = port
            self.container_status = 'running'
            self.state = 'active'
            self.access_url = f"http://{site}"
            self.save()

            frappe.msgprint(f"Container criado e site provisionado: {container_name} -> {site}")
            return True
        except Exception as e:
            frappe.log_error(f"Erro ao criar container do tenant: {str(e)}")
            frappe.throw(f"Erro ao criar container do tenant: {str(e)}")

    def _build_site_fqdn(self) -> str:
        base_domain = frappe.local.conf.get('base_domain', 'innexar.local')
        return f"{self.subdomain}.{base_domain}"

    def _bench_new_site(self, site: str, db_name: str, admin_password: str):
        bench_new_site(
            site=site,
            mariadb_root_password=MYSQL_ROOT_PASSWORD,
            admin_password=admin_password,
            db_name=db_name,
        )

    def _bench_install_app(self, site: str, app: str):
        bench_install_app(site=site, app=app)

    def _apply_plan_apps(self, site: str):
        """Instala apps adicionais conforme o plano (placeholder para futuras apps)."""
        try:
            plan = frappe.get_doc("SAAS Plan", self.plan)
            # Exemplo: se enterprise, instalar 'payments' caso exista
            plan_name = (plan.technical_name or plan.name or '').lower()
            if 'enterprise' in plan_name:
                try:
                    self._bench_install_app(site=site, app="payments")
                except Exception:
                    pass
        except Exception:
            # Não bloquear provisionamento por falha opcional
            pass

    def _apply_brand_and_languages(self, site: str):
        languages = ["en", "pt-BR", "es-ES"]
        default_language = "pt-BR"
        app_name = "Innexar ERP Cloud"
        # bench execute <module.path>:func --args '{"languages":[...],"default_language":"pt-BR","app_name":"..."}'
        args_json = json.dumps({
            "languages": languages,
            "default_language": default_language,
            "app_name": app_name,
        })
        cmd = (
            f"bench --site {site} execute "
            f"innexar_core.saas_management.utils.site_post_setup.apply_brand_and_languages "
            f"--kwargs '{args_json}'"
        )
        run_bench(cmd)
    
    def get_available_port(self):
        """Encontra uma porta disponível para o container"""
        used_ports = frappe.get_all("SAAS Tenant", 
                                 filters={"container_port": ["!=", ""]}, 
                                 fields=["container_port"])
        used_ports = {int(p['container_port']) for p in used_ports if p['container_port']}
        
        # Portas entre 8000 e 9000
        for port in range(8000, 9000):
            if port not in used_ports:
                return port
        frappe.throw("Não há portas disponíveis para criar um novo container.")
    
    def start_container(self):
        """Compat: método mantido; não usado no modelo sem container por tenant."""
        frappe.msgprint("Operação não necessária: tenant roda no backend compartilhado.")
    
    def stop_container(self):
        """Compat: método mantido; não usado no modelo sem container por tenant."""
        self.state = 'suspended'
        self.container_status = 'stopped'
        self.save()
        frappe.msgprint("Tenant marcado como suspenso.")
    
    def delete_container(self):
        """Compat: método mantido; não remove containers (não criados). Pode, futuramente, remover site."""
        self.container_id = None
        self.container_name = None
        self.container_port = None
        self.container_status = 'not_created'
        self.state = 'draft'
        self.save()
        frappe.msgprint("Tenant redefinido para rascunho.")

@frappe.whitelist()
def create_tenant(tenant_data):
    """Cria um novo tenant via API"""
    try:
        if isinstance(tenant_data, str):
            tenant_data = json.loads(tenant_data)
        
        # Verifica se o plano existe
        if not frappe.db.exists("SAAS Plan", tenant_data.get("plan")):
            return {"status": "error", "message": "Plano não encontrado"}
        
        # Cria o tenant
        tenant = frappe.new_doc("SAAS Tenant")
        tenant.update(tenant_data)
        tenant.insert(ignore_permissions=True)
        
        return {
            "status": "success", 
            "message": "Tenant criado com sucesso", 
            "name": tenant.name,
            "access_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}",
            "admin_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}/app"
        }
    except Exception as e:
        frappe.log_error(f"Erro ao criar tenant: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_tenant_status(tenant_name):
    """Obtém o status de um tenant"""
    try:
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        return {
            "status": "success",
            "data": {
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "state": tenant.state,
                "container_status": tenant.container_status,
                "access_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}",
                "admin_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}/app",
                "created_at": tenant.creation
            }
        }
    except Exception as e:
        frappe.log_error(f"Erro ao obter status do tenant: {str(e)}")
        return {"status": "error", "message": str(e)}
