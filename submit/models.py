from ckeditor.fields import RichTextField
from django.db import models

class Permission(models.Model):
    """
    Model to represent a permission for a user.
    """
    name = models.CharField(max_length=100, unique=True)
    description = RichTextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['name']
        db_table = 'permission'