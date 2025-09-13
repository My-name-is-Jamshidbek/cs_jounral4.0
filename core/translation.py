from modeltranslation.translator import register, TranslationOptions
from .models import Default


@register(Default)
class DefaultTranslationOptions(TranslationOptions):
    fields = ('name', 'value')
