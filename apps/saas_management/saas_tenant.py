# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import docker
import json
import random
import string
import time
from datetime import datetime

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
        # Se o plano requer container dedicado, cria automaticamente
        plan = frappe.get_doc("SAAS Plan", self.plan)
        if plan.dedicated_container:
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
        """Cria um container Docker para o tenant"""
        try:
            client = docker.from_env()
            plan = frappe.get_doc("SAAS Plan", self.plan)
            
            # Configurações do container
            container_name = f"innexar-{self.subdomain}"
            port = self.get_available_port()
            
            # Mapeamento de portas
            ports = {
                '8000/tcp': port
            }
            
            # Variáveis de ambiente
            environment = {
                'SITE_NAME': self.name,
                'ADMIN_EMAIL': self.admin_email,
                'ADMIN_PASSWORD': self.admin_password,
                'DB_HOST': 'db',
                'DB_NAME': f"tenant_{self.subdomain}",
                'DB_USER': f"user_{self.subdomain}",
                'DB_PASSWORD': self.generate_password(),
                'MAX_USERS': plan.max_users,
                'MAX_STORAGE_GB': plan.max_storage_gb,
                'CPU_CORES': plan.cpu_cores,
                'MEMORY_GB': plan.memory_gb
            }
            
            # Cria o container
            container = client.containers.run(
                'innexar-platform-backend:latest',
                name=container_name,
                ports=ports,
                environment=environment,
                detach=True,
                restart_policy={"Name": "always"},
                network='innexar-network',
                volumes={
                    f"innexar-{self.subdomain}-sites": {'bind': '/home/frappe/bench-repo/sites', 'mode': 'rw'},
                    f"innexar-{self.subdomain}-logs": {'bind': '/home/frappe/bench-repo/logs', 'mode': 'rw'}
                },
                mem_limit=f"{plan.memory_gb}g",
                cpu_quota=int(plan.cpu_cores * 100000)
            )
            
            # Atualiza os dados do tenant
            self.container_id = container.id
            self.container_name = container_name
            self.container_port = port
            self.container_status = 'running'
            self.state = 'active'
            self.save()
            
            frappe.msgprint(f"Container criado com sucesso: {container_name}")
            return True
            
        except Exception as e:
            frappe.log_error(f"Erro ao criar container: {str(e)}")
            frappe.throw(f"Erro ao criar container: {str(e)}")
    
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
        """Inicia o container do tenant"""
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.start()
            self.container_status = 'running'
            self.state = 'active'
            self.save()
            frappe.msgprint("Container iniciado com sucesso.")
        except Exception as e:
            frappe.log_error(f"Erro ao iniciar container: {str(e)}")
            frappe.throw(f"Erro ao iniciar container: {str(e)}")
    
    def stop_container(self):
        """Para o container do tenant"""
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.stop()
            self.container_status = 'stopped'
            self.state = 'suspended'
            self.save()
            frappe.msgprint("Container parado com sucesso.")
        except Exception as e:
            frappe.log_error(f"Erro ao parar container: {str(e)}")
            frappe.throw(f"Erro ao parar container: {str(e)}")
    
    def delete_container(self):
        """Remove o container do tenant"""
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.remove(force=True)
            
            # Remove os volumes associados
            for volume in client.volumes.list():
                if f"innexar-{self.subdomain}-" in volume.name:
                    volume.remove(force=True)
            
            self.container_id = None
            self.container_name = None
            self.container_port = None
            self.container_status = 'not_created'
            self.state = 'draft'
            self.save()
            frappe.msgprint("Container removido com sucesso.")
        except Exception as e:
            frappe.log_error(f"Erro ao remover container: {str(e)}")
            frappe.throw(f"Erro ao remover container: {str(e)}")

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
