# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_permission_query_conditions(user):
    """
    Restringe a visualização de registros com base nas permissões do usuário
    """
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    # Se o usuário tem papel de gerente de SaaS, pode ver todos os tenants
    if "SAAS Manager" in frappe.get_roles(user):
        return ""
    
    # Usuários só podem ver seus próprios tenants
    return f"`tabSAAS Tenant`.`owner` = '{user}'"


def has_permission(doc, user=None, ptype=None):
    """
    Verifica permissões específicas para um documento
    """
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return True
    
    # Gerentes de SaaS têm permissão total
    if "SAAS Manager" in frappe.get_roles(user):
        return True
    
    # Donos podem ver e editar seus próprios tenants
    if doc.owner == user:
        return True
    
    # Por padrão, nega acesso
    return False


def get_permission_query(user):
    """
    Filtra os registros que um usuário pode ver
    """
    return get_permission_query_conditions(user)
