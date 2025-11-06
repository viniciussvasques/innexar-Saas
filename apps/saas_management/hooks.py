# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

# import frappe

def get_hooks():
    return {
        'on_session_creation': 'saas_management.api.create_session',
        'on_logout': 'saas_management.api.clear_session',
        'has_permission': 'saas_management.utils.permissions.has_permission',
        'has_website_permission': 'saas_management.utils.permissions.has_website_permission',
        'website_route_rules': [
            {"from_route": "/saas/<path:app_path>", "to_route": "saas_management"},
        ],
        'website_context': {
            'favicon': "/assets/saas_management/images/favicon.ico",
            'splash_image': "/assets/saas_management/images/splash.png"
        },
        'doc_events': {
            "*": {
                "on_update": "saas_management.utils.telemetry.log_updated_doc"
            },
        },
        'scheduler_events': {
            "daily": ["saas_management.utils.background_tasks.daily_backup"],
            "daily_long": ["saas_management.utils.background_tasks.cleanup_old_backups"],
        },
        'include_js': ["saas_management.bundle.js"],
        'include_css': ["saas_management.bundle.css"],
        'bootstrap': "saas_management.config.boot"
    }
