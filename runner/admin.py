from django.contrib import admin

from .models import Command, Pipeline

admin.site.register(Command)
admin.site.register(Pipeline)