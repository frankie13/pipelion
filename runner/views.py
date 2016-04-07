import StringIO
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
import json
from runner.models import Command, Pipeline, Job, JOB_STATES
from subprocess import CalledProcessError
import subprocess
import thread


def run_job(request):
    success_url = '/runner/list_job'
    def run_commands(job):
    # run each command in the pipeline
        job.state = 1
        job.save()
        for command in job.pipeline.commands.all():
            job.current_command = command
            job.save()
            raw_command = command.command_text
            try:
                input = json.loads(job.input)
                for item in input:
                    for placeholder, value in item.iteritems():
                        raw_command = raw_command.replace(placeholder, value)
            except Exception as ex:
                job.error = ex
                job.state = 3
                job.exit_code = -1
                job.save()
                return
                
            print "executing " + command.command_text
            try:
                job.last_run = datetime.now()
                p = subprocess.Popen(raw_command, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output, output_err = p.communicate()
                job.output = output
                job.error = output_err
                job.exit_code = p.returncode
                job.save()
            except CalledProcessError as cpe:
                job.state = 3
                job.exit_code = cpe.returncode
                job.save()
                raise cpe
            except OSError as ose:
                job.state = 3
                job.exit_code = ose.errno
                job.save()
                raise ose
            except Exception as ex:
                job.state = 3
                job.exit_code = -1
                job.save()
                raise ex
        job.state = 2
        job.save()


    job_id = request.POST.get('id')
    job = Job.objects.get(id=job_id)
    thread.start_new_thread (run_commands, (job,))


    return redirect('job_list')


class CommandCreate(CreateView):
    model = Command
    success_url = '/'
    fields = ['name', "description", "command_text"]
    
class PipelineCreate(CreateView):
    success_url = '/list/pipeline'
    model = Pipeline
    fields = ['name', "description", "commands"]
    
class JobCreate(CreateView):
    success_url = '/list/job'
    model = Job
    fields = ['name', "description", "pipeline", "input"]

class JobList(ListView):
    queryset = Job.objects.order_by('-id')
    model = Job
    def get_context_data(self, **kwargs):
        context = super(JobList, self).get_context_data(**kwargs)
#         context['form2'] = JobCreate()
#         context['ctx'] = context
        return context

class PipelineList(ListView):

    model = Pipeline
    def get_context_data(self, **kwargs):
        context = super(PipelineList, self).get_context_data(**kwargs)
#         context['now'] = timezone.now()
        return context

class PipelineEdit(UpdateView):
    model = Pipeline
    success_url = '/list/pipeline'
    fields = '__all__'
    template_name_suffix = '_update_form'
    def get_initial(self):
        initial = super(PipelineEdit, self).get_initial()
        return initial

class PipelineDelete(DeleteView):
    model = Pipeline
    success_url = '/list/pipeline'
