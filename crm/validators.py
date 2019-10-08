from django.core.exceptions import ValidationError

def xls_only(file):
    if not file.name.lower().endswith('.xls'):
        raise ValidationError('Only .xls files accepted')
