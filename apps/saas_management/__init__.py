# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

# import frappe
from frappe import _

def get_data():
    return {
        'fieldname': 'saas_tenant',
        'transactions': [
            {
                'label': _('SaaS'),
                'items': ['SaaS Plan', 'SaaS Tenant']
            }
        ]
    }
