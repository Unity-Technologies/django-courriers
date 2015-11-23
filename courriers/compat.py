from django.conf import settings

__all__ = ['update_fields', 'get_user_model']

update_fields = lambda instance, fields: instance.save(update_fields=fields)

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
