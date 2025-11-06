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
        # Garante que o nome técnico seja único
        if self.technical_name:
            self.technical_name = self.technical_name.lower()
            if frappe.db.exists("SAAS Plan", {"technical_name": self.technical_name, "name": ["!=", self.name]}):
                frappe.throw(f"O nome técnico {self.technical_name} já existe. Por favor, escolha outro.")
    
    def validate_resources(self):
        # Validações de recursos
        if self.max_users and self.max_users < 1:
            frappe.throw("O número máximo de usuários deve ser maior que zero.")
        
        if self.max_storage_gb and self.max_storage_gb < 1:
            frappe.throw("O armazenamento deve ser maior que zero.")
    
    def on_trash(self):
        # Impede a exclusão de planos em uso
        if frappe.db.count("SAAS Tenant", {"plan": self.name}) > 0:
            frappe.throw("Não é possível excluir um plano que está em uso por tenants.")
    
    def get_plan_config(self):
        """Retorna a configuração do plano em formato de dicionário"""
        return {
            "name": self.name,
            "technical_name": self.technical_name,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "max_companies": self.max_companies,
            "trial_days": self.trial_days,
            "pricing": {
                "monthly_usd": self.monthly_price_usd,
                "monthly_brl": self.monthly_price_brl,
                "yearly_usd": self.yearly_price_usd,
                "yearly_brl": self.yearly_price_brl
            }
        }
    
    def get_modules_to_install(self):
        """Retorna lista de módulos a serem instalados."""
        base = ["base", "web", "mail", "contacts"]
        plan_modules = []
        if self.erpnext_modules:
            plan_modules = [m.strip() for m in self.erpnext_modules.split(",") if m.strip()]
        return base + plan_modules

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
