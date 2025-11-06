from frappe import _


def get_data():
	return [
		{
			"label": _("Gerenciamento SaaS"),
			"items": [
				{
					"type": "doctype",
					"name": "SAAS Plan",
					"description": _("Planos disponíveis")
				},
				{
					"type": "doctype",
					"name": "SAAS Tenant",
					"description": _("Tenants/Clientes")
				}
			]
		}
	]


