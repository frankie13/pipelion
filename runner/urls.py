from django.conf.urls import url

from runner.views import CommandCreate, PipelineCreate, PipelineList, JobCreate, JobList, run_job, PipelineEdit, PipelineDelete
urlpatterns = [
    url(r'^$', JobList.as_view()),
    url(r'^new/command/$', CommandCreate.as_view(), name='command_create'),
    url(r'^new/pipeline/$', PipelineCreate.as_view(), name='pipeline_create'),
    url(r'^new/job/$', JobCreate.as_view(), name='job_create'),
    url(r'^list/job/$', JobList.as_view(), name='job_list'),
    url(r'^list/pipeline/$', PipelineList.as_view(), name='pipeline_list'),
    url(r'^edit/pipeline/(?P<pk>\d+)/$', PipelineEdit.as_view(), name="pipeline_edit"),
    url(r'^delete/pipeline/(?P<pk>\d+)/$', PipelineDelete.as_view(), name="pipeline_delete"),

    url(r'^run/job', run_job, name='run_job')

]