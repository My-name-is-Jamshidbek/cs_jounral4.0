# from django.contrib import admin
# from django.utils.html import format_html, strip_tags
# from django.utils.safestring import mark_safe
# from .models import Permission
#
#
# @admin.register(Permission)
# class PermissionAdmin(admin.ModelAdmin):
#     list_display = (
#         'name',
#         'permission_type_badge',
#         'content_preview',
#         'word_count_display',
#         'content_status',
#         'updated_at',
#         'created_at'
#     )
#
#     list_filter = (
#         ('created_at', admin.DateFieldListFilter),
#         ('updated_at', admin.DateFieldListFilter),
#     )
#
#     search_fields = ('name', 'description')
#
#     readonly_fields = (
#         'created_at',
#         'updated_at',
#         'word_count',
#         'character_count',
#         'content_html_preview'
#     )
#
#     ordering = ('name',)
#
#     save_on_top = True
#
#     fieldsets = (
#         ('📋 Permission Information', {
#             'fields': ('name', 'description'),
#             'description': 'Define the permission name and detailed description using the rich text editor.',
#             'classes': ('wide',)
#         }),
#         ('📊 Content Statistics', {
#             'fields': ('word_count', 'character_count'),
#             'description': 'Automatically calculated content metrics',
#             'classes': ('collapse',)
#         }),
#         ('🔍 Content Preview', {
#             'fields': ('content_html_preview',),
#             'description': 'HTML preview of your formatted permission content',
#             'classes': ('collapse',)
#         }),
#         ('📅 System Information', {
#             'fields': (('created_at', 'updated_at'),),
#             'classes': ('collapse',),
#             'description': 'System timestamps'
#         }),
#     )
#
#     actions = [
#         'duplicate_permissions',
#         'export_permissions_as_text',
#         'mark_as_template',
#     ]
#
#     def permission_type_badge(self, obj):
#         """Display permission type based on name keywords"""
#         name_lower = obj.name.lower()
#
#         if 'access' in name_lower:
#             color, icon = '#28a745', '🔓'
#         elif 'subscription' in name_lower or 'subscribe' in name_lower:
#             color, icon = '#007bff', '💳'
#         elif 'library' in name_lower:
#             color, icon = '#6f42c1', '📚'
#         elif 'citation' in name_lower or 'cite' in name_lower:
#             color, icon = '#fd7e14', '📝'
#         elif 'token' in name_lower:
#             color, icon = '#ffc107', '🔑'
#         elif 'content' in name_lower or 'copyright' in name_lower:
#             color, icon = '#dc3545', '©️'
#         else:
#             color, icon = '#6c757d', '📄'
#
#         return format_html(
#             '<span style="background: {}; color: white; padding: 3px 8px; '
#             'border-radius: 12px; font-size: 11px; font-weight: bold; '
#             'display: inline-flex; align-items: center; gap: 4px;">'
#             '{} Permission</span>',
#             color, icon
#         )
#     permission_type_badge.short_description = '🏷️ Type'
#
#     def content_preview(self, obj):
#         """Display clean content preview without HTML tags"""
#         if not obj.description:
#             return format_html('<span style="color: #dc3545; font-style: italic;">No description</span>')
#
#         preview = strip_tags(obj.description)[:120]
#         if len(strip_tags(obj.description)) > 120:
#             preview += "..."
#
#         full_content = strip_tags(obj.description)
#         return format_html(
#             '<div style="max-width: 350px; line-height: 1.4; font-size: 12px;" '
#             'title="{}">{}</div>',
#             full_content[:200] + '...' if len(full_content) > 200 else full_content,
#             preview
#         )
#     content_preview.short_description = '👁️ Description Preview'
#
#     def word_count_display(self, obj):
#         """Display word count with color coding"""
#         if not obj.description:
#             return format_html('<span style="color: #dc3545;">❌ No content</span>')
#
#         count = len(strip_tags(obj.description).split())
#
#         if count >= 150:
#             color, icon = '#28a745', '📚'  # Green for comprehensive
#         elif count >= 75:
#             color, icon = '#007bff', '📖'  # Blue for good
#         elif count >= 25:
#             color, icon = '#ffc107', '📄'  # Yellow for moderate
#         else:
#             color, icon = '#dc3545', '📝'  # Red for short
#
#         return format_html(
#             '<span style="color: {}; font-weight: bold;">{} {} words</span>',
#             color, icon, count
#         )
#     word_count_display.short_description = '📊 Words'
#
#     def content_status(self, obj):
#         """Display content completeness status"""
#         if not obj.description:
#             return format_html('<span style="color: #dc3545; font-weight: bold;">❌ Empty</span>')
#
#         word_count = len(strip_tags(obj.description).split())
#         char_count = len(strip_tags(obj.description))
#
#         if word_count >= 50 and char_count >= 200:
#             return format_html('<span style="color: #28a745; font-weight: bold;">✅ Complete</span>')
#         elif word_count >= 25 or char_count >= 100:
#             return format_html('<span style="color: #ffc107; font-weight: bold;">⚠️ Partial</span>')
#         else:
#             return format_html('<span style="color: #dc3545; font-weight: bold;">📝 Draft</span>')
#     content_status.short_description = '📋 Status'
#
#     def word_count(self, obj):
#         """Get word count for readonly field"""
#         if not obj.description:
#             return 0
#         return len(strip_tags(obj.description).split())
#     word_count.short_description = 'Word Count'
#
#     def character_count(self, obj):
#         """Get character count for readonly field"""
#         if not obj.description:
#             return 0
#         return len(strip_tags(obj.description))
#     character_count.short_description = 'Character Count (without HTML)'
#
#     def content_html_preview(self, obj):
#         """Show HTML preview in admin"""
#         if obj.description:
#             return format_html(
#                 '<div style="border: 1px solid #ddd; padding: 15px; '
#                 'max-height: 300px; overflow-y: auto; background: #f9f9f9; '
#                 'border-radius: 4px; font-family: inherit;">{}</div>',
#                 obj.description
#             )
#         return format_html('<div style="color: #999; font-style: italic; padding: 15px;">No content available</div>')
#     content_html_preview.short_description = "📋 HTML Preview"
#
#     # Admin Actions
#     def duplicate_permissions(self, request, queryset):
#         """Duplicate selected permissions"""
#         duplicated = 0
#         for obj in queryset:
#             obj.pk = None
#             obj.name = f"Copy of {obj.name}"
#             obj.save()
#             duplicated += 1
#         self.message_user(request, f'📋 Created {duplicated} duplicate permission(s).')
#     duplicate_permissions.short_description = "📋 Duplicate selected permissions"
#
#     def export_permissions_as_text(self, request, queryset):
#         """Export permissions as plain text file"""
#         from django.http import HttpResponse
#
#         response = HttpResponse(content_type='text/plain')
#         response['Content-Disposition'] = 'attachment; filename="permissions_export.txt"'
#
#         for obj in queryset:
#             response.write(f"Permission: {obj.name}\n")
#             response.write(f"Created: {obj.created_at}\n")
#             response.write(f"Updated: {obj.updated_at}\n")
#             response.write(f"Word Count: {self.word_count(obj)}\n")
#             response.write(f"Description:\n{strip_tags(obj.description) if obj.description else 'No description'}\n")
#             response.write("-" * 80 + "\n\n")
#
#         return response
#     export_permissions_as_text.short_description = "📤 Export as text file"
#
#     def mark_as_template(self, request, queryset):
#         """Mark permissions as templates by adding [TEMPLATE] prefix"""
#         updated = 0
#         for obj in queryset:
#             if not obj.name.startswith('[TEMPLATE]'):
#                 obj.name = f"[TEMPLATE] {obj.name}"
#                 obj.save()
#                 updated += 1
#         self.message_user(request, f'🏷️ Marked {updated} permission(s) as template.')
#     mark_as_template.short_description = "🏷️ Mark as template"
#
#     def get_queryset(self, request):
#         """Optimize database queries"""
#         return super().get_queryset(request)
#
#     class Media:
#         css = {
#             'all': (
#                 'admin/css/permission-admin.css',
#             )
#         }
#         js = (
#             'admin/js/permission-admin.js',
#         )
from django.contrib import admin

from submit.models import Permission


admin.site.register(Permission)
