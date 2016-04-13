import StringIO
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.core import exceptions
import json
from runner.models import Command, Pipeline, Job, JOB_STATES
from subprocess import CalledProcessError
import subprocess
import thread
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def run_job(request, pk):
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


    job = Job.objects.get(id=pk)
    thread.start_new_thread (run_commands, (job,))

    return redirect('job_list')

class CommandList(ListView):
    queryset = Command.objects.order_by('-id')
    model = Command
    def get_context_data(self, **kwargs):
        context = super(CommandList, self).get_context_data(**kwargs)
        return context

@csrf_exempt
def CommandListJSON(request):
    data = serializers.serialize('json', Command.objects.all())
    return JsonResponse(data, safe=False)

class CommandCreate(CreateView):
    model = Command
    success_url = '/'
    fields = ['name', "description", "command_text"]
@csrf_exempt
def CommandCreateOrUpdateJSON(request):
    post = request.POST
    command = None
    created = False
    if 'pk' in request.POST:
        #edit
        command = Command(pk=post.get('pk'), name=post.get('name'), description=post.get('description'), command_text=post.get('command_text') )
    else:
        created = True
        command = Command(name=post.get('name'), description=post.get('description'), command_text=post.get('command_text') )
    command.save()
    return JsonResponse({"success": True, "created": created, "id": command.pk}, safe=False)

class CommandEdit(UpdateView):
    model = Command
    success_url = '/list/command'
    fields = '__all__'
    template_name_suffix = '_update_form'
    def get_initial(self):
        initial = super(CommandEdit, self).get_initial()
        return initial

class CommandDelete(DeleteView):
    model = Command
    success_url = '/list/command'

@csrf_exempt
def CommandDeleteJSON(request):
    id = request.POST.get('pk')
    Command.objects.get(pk=id).delete()
    return JsonResponse(json.dumps({"success": True}), safe=False)

class JobCreate(CreateView):
    success_url = '/list/job'
    model = Job
    fields = ['name', "description", "pipeline", "input"]

class JobList(ListView):
    queryset = Job.objects.order_by('-id')
    model = Job
    def get_context_data(self, **kwargs):
        context = super(JobList, self).get_context_data(**kwargs)
        return context
@csrf_exempt
def JobListJSON(request):
    data = serializers.serialize('json', Job.objects.all())
    return JsonResponse(data, safe=False)

@csrf_exempt
def JobCreateOrUpdateJSON(request):
    post = request.POST
    job = None
    created = False
    if 'pk' in request.POST:
        #edit
        job = Job(pk=post.get('pk'))
    else:
        #create
        created = True
        job = Job()

    # wanted to use **unpacking here to create objects
    # but pk is a list?
    job.name = post.get('name')
    job.description=post.get('description')
    job.pipeline = Pipeline.objects.get(pk=post.get('pipeline'))
    job.input = post.get('input')
    job.output = post.get('output')
    job.error = post.get('error')
    job.exit_code = post.get('exit_code')
    job.state = post.get('state')
    job.current_command = Command.objects.get(pk=post.get('current_command'))
    job.last_run = post.get('last_run')
    job.save()

    return JsonResponse({"success": True, "created": created, "id": job.pk}, safe=False)

class JobEdit(UpdateView):
    model = Job
    success_url = '/list/job'
    fields = '__all__'
    template_name_suffix = '_update_form'
    def get_initial(self):
        initial = super(JobEdit, self).get_initial()
        return initial

class JobDelete(DeleteView):
    model = Job
    success_url = '/list/job'

@csrf_exempt
def JobDeleteJSON(request):
    id = request.POST.get('pk')
    Job.objects.get(pk=id).delete()
    return JsonResponse(json.dumps({"success": True}), safe=False)

@csrf_exempt
def PipelineListJSON(request):
    data = serializers.serialize('json', Pipeline.objects.all())
    return JsonResponse(data, safe=False)


class PipelineList(ListView):
    model = Pipeline
    def get_context_data(self, **kwargs):
        context = super(PipelineList, self).get_context_data(**kwargs)
#         context['now'] = timezone.now()
        return context
@csrf_exempt
def PipelineCreateOrUpdateJSON(request):
    post = request.POST
    pipeline = None
    created = False
    if 'pk' in request.POST:
        #edit
        pipeline = Pipeline(pk=post.get('pk'), name=post.get('name'), description=post.get('description'))
    else:
        #create
        created = True
        pipeline = Pipeline(name=post.get('name'), description=post.get('description'))

    pipeline.save()
    commands = post.getlist('commands[]')
    pipeline.commands.clear()
    for id in commands:
        pipeline.commands.add(Command.objects.get(pk=id))
    
    return JsonResponse({"success": True, "created": created, "id": pipeline.pk}, safe=False)

class PipelineCreate(CreateView):
    success_url = '/list/pipeline'
    model = Pipeline
    fields = ['name', "description"]
    def post(self, request):
        new_model = Pipeline()
        new_model.name = request.POST.get('name')
        new_model.description = request.POST.get('description')
        new_model.save()
        commands = request.POST.getlist('commands[]')
        for command in commands:
            new_model.commands.add(command)
        new_model.save()
        return HttpResponseRedirect(self.success_url)
    def get_context_data(self, **kwargs):
        context = super(PipelineCreate, self).get_context_data(**kwargs)
        context['commands']= Command.objects.all()
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

@csrf_exempt
def PipelineDeleteJSON(request):
    id = request.POST.get('pk')
    Pipeline.objects.get(pk=id).delete()
    return JsonResponse(json.dumps({"success": True}), safe=False)

def Login(request):
    success_url = '/runner/list_job'

def LoginOrHome(request):
    if request.user.is_authenticated():
        return redirect('job_list')
    else:
        return redirect('/login')
