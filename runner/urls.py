from django.conf.urls import url

from runner.views import CommandCreate, PipelineCreate, PipelineList, JobCreate, JobList, run_job
urlpatterns = [
    url(r'^$', JobList.as_view()),
    url(r'^new/command/$', CommandCreate.as_view(), name='command_create'),
    url(r'^new/pipeline/$', PipelineCreate.as_view(), name='pipeline_create'),
    url(r'^new/job/$', JobCreate.as_view(), name='job_create'),
    url(r'^list/job/$', JobList.as_view(), name='job_list'),
    url(r'^list/pipeline/$', PipelineList.as_view(), name='pipeline_list'),
    url(r'^run/job', run_job, name='run_job')

]