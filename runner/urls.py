from django.conf.urls import url
from runner.views import CommandCreate, CommandList, CommandDelete
from runner.views import JobCreate, JobList, JobDelete
from runner.views import PipelineCreate, PipelineList, PipelineDelete
from runner.views import run_job, CommandListJSON, CommandCreateOrUpdateJSON
from runner.views import PipelineListJSON, PipelineCreateOrUpdateJSON, PipelineDeleteJSON
from runner.views import JobListJSON, JobDeleteJSON, JobCreateOrUpdateJSON
from runner.views import LoginOrHome
from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', LoginOrHome, name='login_or_home'),

    url(r'^api/new/job/$', JobCreateOrUpdateJSON, name='job_create_update_api'),
    url(r'^api/new/pipeline/$', PipelineCreateOrUpdateJSON, name='pipeline_create_update_api'),
    url(r'^api/new/command/$', CommandCreateOrUpdateJSON, name='command_create_update_api'),
    url(r'^new/command/$', login_required(CommandCreate.as_view()), name='command_create'),
    url(r'^new/pipeline/$', login_required(PipelineCreate.as_view()), name='pipeline_create'),
    url(r'^new/job/$', login_required(JobCreate.as_view()), name='job_create'),

    url(r'^api/list/job/$', JobListJSON, name='job_list_api'),
    url(r'^api/list/pipeline/$', PipelineListJSON, name='pipeline_list_api'),
    url(r'^api/list/command/$', CommandListJSON, name='command_list_api'),
    url(r'^list/command/$', login_required(CommandList.as_view()), name='command_list'),
    url(r'^list/pipeline/$', login_required(PipelineList.as_view()), name='pipeline_list'),
    url(r'^list/job/$', login_required(JobList.as_view()), name='job_list'),
    
    url(r'^api/delete/job/$', JobDeleteJSON, name='job_delete_api'),
    url(r'^delete/command/(?P<pk>\d+)/$', login_required(CommandDelete.as_view()), name="command_delete"),
    url(r'^api/delete/pipeline/$', PipelineDeleteJSON, name='pipeline_delete_api'),
    url(r'^delete/pipeline/(?P<pk>\d+)/$', login_required(PipelineDelete.as_view()), name="pipeline_delete"),
    url(r'^delete/job/(?P<pk>\d+)/$', login_required(JobDelete.as_view()), name="job_delete"),

    url(r'^run/job/(?P<pk>\d+)/$', run_job, name="run_job"),
]