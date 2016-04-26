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
from runner.monitors import monitors, decodestatus
import drmaa
# Non-restful API for integration


def _serialize_objs(objs):
    serialized = serializers.serialize('json', objs)
    return JsonResponse(serialized, safe=False)

def _get_data_for_state(clazz, drmaa_state, serialize=True):
    objs = clazz.objects.filter(scheduler_state=decodestatus[drmaa_state])
    if serialize:
        return _serialize_objs(objs)
    else:
        return objs

def get_completed_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as completed.
    """

    return _get_data_for_state(Job, drmaa.JobState.DONE)

def get_failed_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as failed.
    """
    
    return _get_data_for_state(Job, drmaa.JobState.FAILED)

def get_running_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as running.
    """

    return _get_data_for_state(Job, drmaa.JobState.RUNNING)

def get_pending_jobs(request):
    """
    Returns all jobs that have been marked by the scheduler as pending.
    """
    
    # uses set union | operator for joining querysets.
    union = _get_data_for_state(Job, drmaa.JobState.QUEUED_ACTIVE, False) |_get_data_for_state(Job, drmaa.JobState.SYSTEM_ON_HOLD, False) |_get_data_for_state(Job, drmaa.JobState.USER_ON_HOLD, False) |_get_data_for_state(Job, drmaa.JobState.USER_SYSTEM_ON_HOLD, False)
    
    return _serialize_objs(union)

def get_jobs(request):
    """
    Return all the jobs!
    """
    
    return _serialize_objs(Job.objects.all())

def get_job(request):
    """
    Get a job by id.
    POST should look like:
    `{
        'query': 'getPipeline',
        'params': {
           'name': 'taskid'
       }
    }`
    """

    params = json.loads(request.POST.get('params'))
    name = params.get("name")
    return _serialize_objs([Job.objects.get(pk=name)])

def get_pipeline(request):
    """
    Get a pipeline by name.
    POST should look like:
    `{
        'query': 'getPipeline',
        'params': {
           'name': 'pipeline name'
       }
    }`
    """

    params = json.loads(request.POST.get('params'))
    name = params.get("name")
    return _serialize_objs([Pipeline.objects.get(pk=name)])

def get_pipelines(request):
    """
    Return all pipeline objects.
    """
    
    return _serialize_objs(Pipeline.objects.all())

def submit_job(request):
    """
    Creates a job from a request object and submits it.
    The request should contain everything needed to start a job:
    {
        'pipeline': 'pipeline',
        'params': {
            'name': 'the job name',
            'description: 'a description for the job',
            'input': {
                //a list of kvps for a specific run that will be passed to the commands.
            }
        }
    }
    """

    name = "pipelion submitted job"
    description = "pipelion submitted job"
    pipeline = request.POST.get("pipeline")
    params = json.loads(request.POST.get("params"))
    run = True

    if "name" in params:
        name = params.get("name")
    if "description" in params:
        description = params.get("description")
    if "run" in params:
        run = params.get("run")
    job = Job(name=name, description=description, pipeline=Pipeline.objects.get(pk=pipeline))
    job.save()
    if run:
        run_job(None, job.pk)
    return _serialize_objs([job])

def miso(request):
    """
    Marshalls between miso specific API methods based on query.
    """

    query = request.POST.get("query")
    views = {
        "getCompletedTasks": get_completed_jobs,
        "getFailedTasks": get_failed_jobs,
        "getPendingTasks": get_pending_jobs,
        "getPipeline": get_pipeline,
        "getPipelines": get_pipelines,
        "getRunningTasks": get_running_jobs,
        "getTask": get_job,
        "getTasks": get_jobs,
        "submitTask": submit_job,
    }
#     print 'POST'
#     print request.POST
    return views[query](request)

# end of miso specific code.

def run_job(request, pk):
    success_url = '/runner/list_job'
    def run_commands(job):
        # run each command in the pipeline
        job.last_run = datetime.now()
        job.state = 1
        if job.exit_code:
            job.output = None
            job.error = None
            job.exit_code = None
            job.current_command = None
        job.save()
        for command in job.pipeline.commands.all():
            print 'running:'
            print command
            job.current_command = command
            job.save()
            raw_command = command.command_text
            try:
                print 'setting input'
                print job.input
                input = json.loads("[" + job.input + "]")
                for item in input:
                    for placeholder, value in item.iteritems():
                        raw_command = raw_command.replace(placeholder, value)
            except Exception as ex:
                'threw'+ str(ex)
                job.error = ex
                job.state = 3
                job.exit_code = -1
                job.save()
                return

            print "executing " + command.command_text
            try:
                p = subprocess.Popen(raw_command, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output, output_err = p.communicate()
                job.output = output
                job.error = output_err
                job.exit_code = p.returncode
                job.save()
                # at this point the command has been executed.
                # since this is designed for schedulers this may not be the end of the story!
                # we need a way of monitoring the progress of the job and then reporting back
                # when things have changed.
                if command.monitor != 0:
                    monitor_instance = monitors.get(command.monitor)()
                    monitor_instance.monitor(job)
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

@csrf_exempt
def CommandListJSON(request):
    data = serializers.serialize('json', Command.objects.all())
    return JsonResponse(data, safe=False)


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

@csrf_exempt
def JobDeleteJSON(request):
    id = request.POST.get('pk')
    Job.objects.get(pk=id).delete()
    return JsonResponse(json.dumps({"success": True}), safe=False)

@csrf_exempt
def PipelineListJSON(request):
    data = serializers.serialize('json', Pipeline.objects.all())
    return JsonResponse(data, safe=False)

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

@csrf_exempt
def PipelineDeleteJSON(request):
    id = request.POST.get('pk')
    Pipeline.objects.get(pk=id).delete()
    return JsonResponse(json.dumps({"success": True}), safe=False)

# Views for pipelion ui


class CommandList(ListView):
    queryset = Command.objects.order_by('-id')
    model = Command
    def get_context_data(self, **kwargs):
        context = super(CommandList, self).get_context_data(**kwargs)
        return context

class CommandCreate(CreateView):
    model = Command
    success_url = '/'
    fields = ['name', "description", "command_text"]


class CommandDelete(DeleteView):
    model = Command
    success_url = '/list/command'

class JobCreate(CreateView):
    success_url = '/list/job'
    model = Job
    fields = ['name', "description", "pipeline"]
    def post(self, request):
        new_model = Job()
        new_model.name = request.POST.get('name')
        new_model.description = request.POST.get('description')
        new_model.input = request.POST.get('input_json')
        new_model.pipeline = Pipeline.objects.get(pk=request.POST.get('pipeline'))
        new_model.save()
        return HttpResponseRedirect(self.success_url)

class JobList(ListView):
    queryset = Job.objects.order_by('-id')
    model = Job
    def get_context_data(self, **kwargs):
        context = super(JobList, self).get_context_data(**kwargs)
        return context

class JobDelete(DeleteView):
    model = Job
    success_url = '/list/job'

class PipelineList(ListView):
    model = Pipeline
    def get_context_data(self, **kwargs):
        context = super(PipelineList, self).get_context_data(**kwargs)
#         context['now'] = timezone.now()
        return context

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

class PipelineDelete(DeleteView):
    model = Pipeline
    success_url = '/list/pipeline'

def Login(request):
    success_url = '/runner/list_job'

def LoginOrHome(request):
    if request.user.is_authenticated():
        return redirect('job_list')
    else:
        return redirect('/login')
