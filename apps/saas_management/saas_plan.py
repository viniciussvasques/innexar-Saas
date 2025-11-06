# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class SAASPlan(Document):
    def validate(self):
        self.validate_plan_code()
        self.validate_resources()
    
    def validate_plan_code(self):
        # Garante que o código do plano seja único e em maiúsculas
        self.code = self.code.upper()
        if frappe.db.exists("SAAS Plan", {"code": self.code, "name": ["!=", self.name]}):
            frappe.throw(f"O código de plano {self.code} já existe. Por favor, escolha outro código.")
    
    def validate_resources(self):
        # Validações de recursos
        if self.max_users < 1:
            frappe.throw("O número máximo de usuários deve ser maior que zero.")
        
        if self.max_storage_gb < 1:
            frappe.throw("O armazenamento deve ser maior que zero.")
        
        if self.cpu_cores < 0.5:
            frappe.throw("Os núcleos de CPU devem ser iguais ou maiores que 0.5.")
        
        if self.memory_gb < 0.5:
            frappe.throw("A memória deve ser igual ou maior que 0.5GB.")
    
    def on_trash(self):
        # Impede a exclusão de planos em uso
        if frappe.db.count("SAAS Tenant", {"plan": self.name}) > 0:
            frappe.throw("Não é possível excluir um plano que está em uso por tenants.")
    
    def get_plan_config(self):
        """Retorna a configuração do plano em formato de dicionário"""
        return {
            "name": self.name,
            "code": self.code,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "dedicated_container": self.dedicated_container,
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "modules": {
                "inventory": self.module_inventory,
                "accounting": self.module_accounting,
                "hr": self.module_hr,
                "project": self.module_project
            },
            "pricing": {
                "monthly": self.price_monthly,
                "yearly": self.price_yearly
            }
        }

@frappe.whitelist()
def create_plan(plan_data):
    """Cria um novo plano via API"""
    try:
        if isinstance(plan_data, str):
            plan_data = json.loads(plan_data)
        
        plan = frappe.new_doc("SAAS Plan")
        plan.update(plan_data)
        plan.insert(ignore_permissions=True)
        
        return {"status": "success", "message": "Plano criado com sucesso", "name": plan.name}
    except Exception as e:
        frappe.log_error(f"Erro ao criar plano: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_plan(plan_name):
    """Obtém os dados de um plano via API"""
    try:
        plan = frappe.get_doc("SAAS Plan", plan_name)
        return {"status": "success", "data": plan.get_plan_config()}
    except Exception as e:
        frappe.log_error(f"Erro ao obter plano: {str(e)}")
        return {"status": "error", "message": str(e)}
