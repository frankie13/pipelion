from __future__ import unicode_literals

from django.db import models

class Command(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    command_text = models.CharField(max_length=5000)
    def __str__(self):
        return self.name
    
class Pipeline(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    commands = models.ManyToManyField(Command)
    def __str__(self):
        return self.name
JOB_STATES = ((0, 'not started'), (1, 'running'), (2, 'finished'), (3, 'error'))

class Job(models.Model):
    """
    A run of a pipeline
    """
    
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    pipeline = models.ForeignKey(Pipeline)
    input = models.CharField(max_length=10000, default='[]')
    output = models.CharField(max_length=10000, null=True, blank=True)
    error = models.CharField(max_length=10000, null=True, blank=True)
    exit_code = models.CharField(max_length=5, null=True, blank=True)
    state = models.PositiveSmallIntegerField(choices=JOB_STATES, default=0, null=True, blank=True)
    current_command = models.ForeignKey(Command, null=True, blank=True)
    last_run = models.DateTimeField(blank=True, null=True, )
    def __str__(self):
        return self.name
    
