from modeltranslation.translator import register, TranslationOptions
from .models import Permission


@register(Permission)
class PermissionTranslationOptions(TranslationOptions):
    fields = ('name', 'description')
