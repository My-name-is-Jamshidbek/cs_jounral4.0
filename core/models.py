from ckeditor.fields import RichTextField
from django.db import models


class Joining(models.Model):
    """
    Model to represent a joining request.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    institution = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} - {self.email}"

    class Meta:
        verbose_name = "Joining Request"
        verbose_name_plural = "Joining Requests"
        ordering = ['-id']
        db_table = 'joining'


class Default(models.Model):
    """
    Model to represent a default setting.
    """
    name = models.CharField(max_length=100, unique=True)
    value = RichTextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Default Setting"
        verbose_name_plural = "Default Settings"
        ordering = ['name']
        db_table = 'default'