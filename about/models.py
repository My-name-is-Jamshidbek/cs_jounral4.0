from ckeditor.fields import RichTextField
from django.db import models


class About(models.Model):
    """ Model to represent the 'About' page content. """
    title = models.CharField(max_length=255, verbose_name="Title")
    content = RichTextField(verbose_name="Content")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "About Page Content"
        verbose_name_plural = "About Page Contents"
        ordering = ['-created_at']
        db_table = 'about_page_content'

    def __str__(self):
        return self.title