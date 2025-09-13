from about.models import About
from core.models import Default
from django.utils.html import strip_tags


def site_context(request):
    """
    Context processor to add site-wide data to all templates
    """
    context = {}

    # Get About model data for header and site information
    try:
        # Get all about pages for navigation and footer
        context['about_pages'] = About.objects.all().order_by('title')[:10]

    except Exception:
        context['site_about'] = None
        context['about_pages'] = []
        context['about_description'] = ''

    # Get site configuration from Default model
    try:
        # Load all defaults into a dictionary for easy access - optimized query
        defaults_queryset = Default.objects.all().select_related()
        site_config = {default.name: default.value for default in defaults_queryset}

        context['site_config'] = site_config

        # Extract commonly used values with fallbacks
        context['site_title'] = site_config.get('site_title', 'Comparative Critical Studies')

        # Use site description from defaults, fallback to about description, then fallback text
        context['site_description'] = (
            site_config.get('site_description') or
            context.get('about_description') or
            'A leading journal for comparative literature and critical studies research'
        )

        # Core contact information
        context['publisher'] = site_config.get('publisher', 'Edinburgh University Press')
        context['contact_email'] = site_config.get('contact_email', 'journals@eup.ed.ac.uk')
        context['submission_email'] = site_config.get('submission_email', site_config.get('contact_email', 'journals@eup.ed.ac.uk'))

        # Journal metadata
        context['issn_print'] = site_config.get('issn_print', '1744-1854')
        context['issn_online'] = site_config.get('issn_online', '1750-0109')
        context['current_volume'] = site_config.get('current_volume', '21')
        context['publication_frequency'] = site_config.get('publication_frequency', '3 issues per year')

        # Society and organizational info
        context['society_name'] = site_config.get('society_name', 'British Comparative Literature Association (BCLA)')
        context['journal_abbreviation'] = site_config.get('journal_abbreviation', 'CCS')
        context['established_year'] = site_config.get('established_year', '2004')

        # Editorial information
        context['editor_in_chief'] = site_config.get('editor_in_chief', '')
        context['manuscript_submission_url'] = site_config.get('manuscript_submission_url', '')

        # Additional site configuration
        context['site_keywords'] = site_config.get('site_keywords', 'comparative literature, critical studies, academic journal')
        context['social_twitter'] = site_config.get('social_twitter', '')
        context['social_linkedin'] = site_config.get('social_linkedin', '')
        context['google_analytics_id'] = site_config.get('google_analytics_id', '')

        # Debug information (only in development)
        from django.conf import settings
        if settings.DEBUG:
            context['defaults_loaded'] = len(site_config)
            context['available_defaults'] = list(site_config.keys())

    except Exception as e:
        # Fallback values if database is not available
        context['site_config'] = {}
        context['site_title'] = 'Comparative Critical Studies'
        context['site_description'] = (
            context.get('about_description') or
            'A leading journal for comparative literature and critical studies research'
        )
        context['publisher'] = 'Edinburgh University Press'
        context['contact_email'] = 'journals@eup.ed.ac.uk'
        context['submission_email'] = 'journals@eup.ed.ac.uk'
        context['issn_print'] = '1744-1854'
        context['issn_online'] = '1750-0109'
        context['current_volume'] = '21'
        context['publication_frequency'] = '3 issues per year'
        context['society_name'] = 'British Comparative Literature Association (BCLA)'
        context['journal_abbreviation'] = 'CCS'
        context['established_year'] = '2004'
        context['editor_in_chief'] = ''
        context['manuscript_submission_url'] = ''
        context['site_keywords'] = 'comparative literature, critical studies, academic journal'
        context['social_twitter'] = ''
        context['social_linkedin'] = ''
        context['google_analytics_id'] = ''

        # Log the error in development
        from django.conf import settings
        if settings.DEBUG:
            print(f"Context processor error loading defaults: {e}")
    return context
