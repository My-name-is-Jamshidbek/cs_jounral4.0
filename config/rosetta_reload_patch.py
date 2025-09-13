from rosetta.views import translate
from django.utils.translation import trans_real

_original_translate = translate

def translate_with_reload(*args, **kwargs):
    response = _original_translate(*args, **kwargs)
    # After saving translations, clear and reload translations cache
    trans_real._translations = {}
    trans_real._default = None
    return response

# Patch Rosetta's translate view
import rosetta.views
rosetta.views.translate = translate_with_reload