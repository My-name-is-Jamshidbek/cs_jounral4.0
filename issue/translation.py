from modeltranslation.translator import register, TranslationOptions
from .models import Issue, JournalIssue


@register(Issue)
class IssueTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(JournalIssue)
class JournalIssueTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
