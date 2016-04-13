from django.conf.urls import url
from runner.views import CommandCreate, CommandList, CommandEdit, CommandDelete
from runner.views import JobCreate, JobList, JobEdit, JobDelete
from runner.views import PipelineCreate, PipelineList, PipelineEdit, PipelineDelete
from runner.views import run_job, CommandListJSON, CommandCreateOrUpdateJSON, CommandDeleteJSON
from runner.views import PipelineListJSON, PipelineCreateOrUpdateJSON, PipelineDeleteJSON
from runner.views import JobListJSON, JobDeleteJSON, JobCreateOrUpdateJSON
from django.conf.urls import url, include

urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', JobList.as_view()),

    url(r'^api/new/job/$', JobCreateOrUpdateJSON, name='job_create_update_api'),
    url(r'^api/new/pipeline/$', PipelineCreateOrUpdateJSON, name='pipeline_create_update_api'),
    url(r'^api/new/command/$', CommandCreateOrUpdateJSON, name='command_create_update_api'),
    url(r'^new/command/$', CommandCreate.as_view(), name='command_create'),
    url(r'^new/pipeline/$', PipelineCreate.as_view(), name='pipeline_create'),
    url(r'^new/job/$', JobCreate.as_view(), name='job_create'),

    url(r'^api/list/job/$', JobListJSON, name='job_list_api'),
    url(r'^api/list/pipeline/$', PipelineListJSON, name='pipeline_list_api'),
    url(r'^api/list/command/$', CommandListJSON, name='command_list_api'),
    url(r'^list/command/$', CommandList.as_view(), name='command_list'),
    url(r'^list/pipeline/$', PipelineList.as_view(), name='pipeline_list'),
    url(r'^list/job/$', JobList.as_view(), name='job_list'),
    

    url(r'^edit/command/(?P<pk>\d+)/$', CommandEdit.as_view(), name="command_edit"),
    url(r'^edit/pipeline/(?P<pk>\d+)/$', PipelineEdit.as_view(), name="pipeline_edit"),
    url(r'^edit/job/(?P<pk>\d+)/$', JobEdit.as_view(), name="job_edit"),

    url(r'^api/delete/job/$', JobDeleteJSON, name='job_delete_api'),
    url(r'^api/delete/command/$', CommandDeleteJSON, name='command_delete_api'),
    url(r'^delete/command/(?P<pk>\d+)/$', CommandDelete.as_view(), name="command_delete"),
    url(r'^api/delete/pipeline/$', PipelineDeleteJSON, name='pipeline_delete_api'),
    url(r'^delete/pipeline/(?P<pk>\d+)/$', PipelineDelete.as_view(), name="pipeline_delete"),
    url(r'^delete/job/(?P<pk>\d+)/$', JobDelete.as_view(), name="job_delete"),

    url(r'^run/job/(?P<pk>\d+)/$', run_job, name="run_job"),
]