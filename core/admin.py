from django.contrib import admin
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from .models import Joining, Default


@admin.register(Joining)
class JoiningAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'institution_display',
        'country_flag',
        'join_date',
        'contact_actions'
    )

    list_filter = (
        'country',
        'institution',
        ('id', admin.DateFieldListFilter),
    )

    search_fields = ('first_name', 'last_name', 'email', 'institution', 'country')

    readonly_fields = ('id', 'formatted_join_info')

    ordering = ('-id',)


    fieldsets = (
        ('👤 Personal Information', {
            'fields': ('first_name', 'last_name', 'email'),
            'description': 'Subscriber\'s personal details'
        }),
        ('🏛️ Institutional Information', {
            'fields': ('institution', 'country'),
            'description': 'Academic or professional affiliation'
        }),
        ('📊 System Information', {
            'fields': ('id', 'formatted_join_info'),
            'classes': ('collapse',),
            'description': 'System generated information'
        }),
    )

    actions = [
        'export_subscribers_csv',
        'export_subscribers_email_list',
        'send_welcome_email',
    ]

    def full_name(self, obj):
        """Display full name with proper formatting"""
        return format_html(
            '<strong>{} {}</strong>',
            obj.first_name,
            obj.last_name
        )
    full_name.short_description = '👤 Full Name'

    def institution_display(self, obj):
        """Display institution with truncation if too long"""
        if len(obj.institution) > 30:
            short_name = obj.institution[:27] + "..."
            return format_html(
                '<span title="{}">{}</span>',
                obj.institution,
                short_name
            )
        return obj.institution
    institution_display.short_description = '🏛️ Institution'

    def country_flag(self, obj):
        """Display country with flag emoji"""
        country_flags = {
            'United Kingdom': '🇬🇧',
            'United States': '🇺🇸',
            'Canada': '🇨🇦',
            'Australia': '🇦🇺',
            'Germany': '🇩🇪',
            'France': '🇫🇷',
            'Spain': '🇪🇸',
            'Italy': '🇮🇹',
            'Netherlands': '🇳🇱',
            'Sweden': '🇸🇪',
            'Norway': '🇳🇴',
            'Japan': '🇯🇵',
            'South Korea': '🇰🇷',
            'China': '🇨🇳',
            'India': '🇮🇳',
            'Brazil': '🇧🇷',
            'Mexico': '🇲🇽',
            'Argentina': '🇦🇷',
            'South Africa': '🇿🇦',
        }

        flag = country_flags.get(obj.country, '🌍')
        return format_html('{} {}', flag, obj.country)
    country_flag.short_description = '🌍 Country'

    def join_date(self, obj):
        """Display join date with relative time"""
        return format_html(
            '<span title="Subscriber ID: {}">ID #{}</span>',
            obj.id,
            obj.id
        )
    join_date.short_description = '📅 Join Order'

    def contact_actions(self, obj):
        """Display quick contact actions"""
        return format_html(
            '<a href="mailto:{}" class="button" style="margin-right: 5px;" title="Send email">✉️</a>'
            '<span style="color: #666; font-size: 11px;">#{}</span>',
            obj.email,
            obj.id
        )
    contact_actions.short_description = '📧 Actions'

    def formatted_join_info(self, obj):
        """Display formatted join information"""
        return format_html(
            '<div style="background: #f9f9f9; padding: 10px; border-radius: 4px;">'
            '<strong>Subscriber Details:</strong><br>'
            'ID: #{}<br>'
            'Email: <a href="mailto:{}">{}</a><br>'
            'Full Name: {} {}<br>'
            'Institution: {}<br>'
            'Country: {}<br>'
            '</div>',
            obj.id, obj.email, obj.email,
            obj.first_name, obj.last_name,
            obj.institution, obj.country
        )
    formatted_join_info.short_description = "📋 Complete Info"

    # Admin Actions
    def export_subscribers_csv(self, request, queryset):
        """Export subscribers as CSV file"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'

        import csv
        writer = csv.writer(response)
        writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Institution', 'Country'])

        for obj in queryset:
            writer.writerow([obj.id, obj.first_name, obj.last_name, obj.email, obj.institution, obj.country])

        return response
    export_subscribers_csv.short_description = "📊 Export as CSV"

    def export_subscribers_email_list(self, request, queryset):
        """Export email list for mailing"""
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="email_list.txt"'

        for obj in queryset:
            response.write(f'"{obj.first_name} {obj.last_name}" <{obj.email}>\n')

        return response
    export_subscribers_email_list.short_description = "📧 Export email list"

    def send_welcome_email(self, request, queryset):
        """Mark for welcome email sending"""
        count = queryset.count()
        self.message_user(request, f'📧 Marked {count} subscriber(s) for welcome email.')
    send_welcome_email.short_description = "📧 Mark for welcome email"


admin.site.register(Default)
