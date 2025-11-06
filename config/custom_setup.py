from __future__ import unicode_literals

def get_setup_stages(args):
    # Import default setup stages
    from erpnext.setup.setup_wizard.operations.install_fixtures import get_setup_stages as get_default_stages
    
    # Get default stages
    stages = get_default_stages(args)
    
    # Update language options to include Portuguese (Brazil) as default
    for stage in stages:
        if stage.get('title') == 'Region':
            for field in stage.get('fields', []):
                if field.get('fieldname') == 'language':
                    # Set Portuguese (Brazil) as default
                    field['default'] = 'portuguese'
                    # Ensure Portuguese is in the options
                    if 'portuguese' not in field.get('options', []):
                        field['options'].append('portuguese')
    
    return stages

def get_available_languages():
    """Return available languages with Portuguese as default"""
    return [
        {'lang_code': 'pt', 'lang_name': 'Português'},
        {'lang_code': 'en', 'lang_name': 'English'},
        {'lang_code': 'es', 'lang_name': 'Español'}
    ]
