from modeltranslation.translator import register, TranslationOptions
from .models import Subscribe


@register(Subscribe)
class SubscribeTranslationOptions(TranslationOptions):
    fields = ('title', 'content')
