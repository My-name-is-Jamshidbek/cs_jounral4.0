from ckeditor.fields import RichTextField
from django.db import models

class Subscribe(models.Model):
    """ Model to subscribe page content. """
    title = models.CharField(max_length=255, verbose_name="Title")
    content = RichTextField(verbose_name="Content")
    type = models.CharField(max_length=255, verbose_name="Type", choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main')
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Subscribe Page Content"
        verbose_name_plural = "Subscribe Page Contents"
        ordering = ['-created_at']
        db_table = 'subscribe_page_content'

    def __str__(self):
        return self.title
