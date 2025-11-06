import frappe


def execute() -> None:
    plans = [
        {
            "plan_name": "Starter",
            "technical_name": "starter",
            "monthly_price_usd": 49,
            "yearly_price_usd": 49 * 12,
            "monthly_price_brl": 149,
            "yearly_price_brl": 149 * 12,
            "max_users": 5,
            "max_storage_gb": 1,
            "max_companies": 1,
            "trial_days": 14,
            "erpnext_modules": "stock,crm,accounts,selling",
            "active": 1,
        },
        {
            "plan_name": "Professional",
            "technical_name": "professional",
            "monthly_price_usd": 99,
            "yearly_price_usd": 99 * 12,
            "monthly_price_brl": 299,
            "yearly_price_brl": 299 * 12,
            "max_users": 25,
            "max_storage_gb": 10,
            "max_companies": 3,
            "trial_days": 14,
            "erpnext_modules": "stock,crm,accounts,selling,buying,projects",
            "active": 1,
        },
        {
            "plan_name": "Enterprise",
            "technical_name": "enterprise",
            "monthly_price_usd": 199,
            "yearly_price_usd": 199 * 12,
            "monthly_price_brl": 499,
            "yearly_price_brl": 499 * 12,
            "max_users": 0,  # 0 = ilimitado
            "max_storage_gb": 0,
            "max_companies": 0,
            "trial_days": 14,
            "erpnext_modules": "stock,crm,accounts,selling,buying,projects,hr,manufacturing,assets,api",
            "active": 1,
        },
    ]

    for plan in plans:
        existing = frappe.db.exists("SAAS Plan", {"technical_name": plan["technical_name"]})
        if existing:
            frappe.db.set_value("SAAS Plan", existing, {k: v for k, v in plan.items() if k != "plan_name"})
            continue

        doc = frappe.get_doc({"doctype": "SAAS Plan", **plan})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()



