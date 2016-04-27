from django.test import TestCase
from django.test import Client
from runner.models import Command, Job, Pipeline, InputKey
from runner.monitors import SlurmMonitor, decodestatus
from django.core.urlresolvers import reverse
import json
from datetime import datetime
import drmaa

class PipelineJsonTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_command_1 = Command(pk=1, name="test name", description="test description")
        self.test_command_2 = Command(pk=2, name="test name 2", description="test description 2")
        self.test_command_1.save()
        self.test_command_2.save()

        self.test_pipeline_1 = Pipeline(pk=1, name="test_name3", description="test description 3")
        self.test_pipeline_1.save()
        self.test_pipeline_1.commands.add(self.test_command_1)
        self.test_pipeline_1.commands.add(self.test_command_2)
        
        self.test_pipeline_2 = Pipeline(pk=2, name="test_name4", description="test description 4")
        self.test_pipeline_2.save()

    def test_PipelineListJSON(self):
        url = reverse("pipeline_list_api")
        response = self.client.post(url)
        py_response = json.loads(response.json())
        self.assertEqual(2, len(py_response))
        self.assertEqual(self.test_pipeline_1.pk, py_response[0].get('pk'))
        self.assertEqual(self.test_pipeline_1.name, py_response[0].get('fields').get('name'))
        self.assertEqual(self.test_pipeline_1.description, py_response[0].get('fields').get('description'))
        
        self.assertEqual(1, py_response[0].get('fields').get('commands')[0])
        self.assertEqual(2, py_response[0].get('fields').get('commands')[1])

        self.assertEqual(self.test_pipeline_2.pk, py_response[1].get('pk'))
        self.assertEqual(self.test_pipeline_2.name, py_response[1].get('fields').get('name'))
        self.assertEqual(self.test_pipeline_2.description, py_response[1].get('fields').get('description'))
        self.assertEqual([], py_response[1].get('fields').get('commands'))

    def test_PipelineCreateOrUpdateJSON(self):

        Pipeline.objects.all().delete()
        self.assertEqual(0, Pipeline.objects.count())
        new_name = "crazy name"
        new_description = "wacky description"
        url = reverse("pipeline_create_update_api")
        data = {'name': self.test_pipeline_1.name, 'description': self.test_pipeline_1.description, 'commands[]': [self.test_command_1.pk, self.test_command_2.pk]}
        response = self.client.post(url, data).json()

        new_id = response.get("id")
        self.assertEqual(1, Pipeline.objects.count())
        self.assertEqual({"success": True, "created": True, "id": new_id}, response)

        response = self.client.post(url, {'pk':new_id, 'name':new_name, 'description': new_description, 'commands[]': [self.test_command_2.pk]}).json()

        self.assertEqual({"success": True, "created": False, "id": str(new_id)}, response)
        self.assertEqual(Pipeline.objects.count(), 1)

        updated_pipeline = Pipeline.objects.get(pk=new_id)
        self.assertEquals(new_name, updated_pipeline.name)
        self.assertEquals(new_description, updated_pipeline.description)
        self.assertEquals(1, updated_pipeline.commands.count())
        self.assertEquals(self.test_command_2, updated_pipeline.commands.all()[0])

    def test_PipelineDeleteJSON(self):
        self.assertEqual(Pipeline.objects.count(), 2)

        response = self.client.post(reverse("pipeline_delete_api"), {"pk": self.test_pipeline_2.pk}).json()
        response = json.loads(response)
        self.assertEqual({"success": True}, response)
        self.assertEqual(1, Pipeline.objects.count())
        self.assertIn(self.test_pipeline_1, Pipeline.objects.all())
        self.assertNotIn(self.test_pipeline_2, Pipeline.objects.all())

class CommandJsonTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.pk_1 = 1
        self.name_1 = "test name"
        self.description_1 = "test description"
        self.command_text_1 = "boog"
        self.pk_2 = 2
        self.name_2 = "test name 2"
        self.command_text_2 = "bloing"

        self.description_2 = "test description 2"
        self.test_command_1 = Command(pk=self.pk_1, name=self.name_1, description=self.description_1, command_text=self.command_text_1)
        self.test_command_2 = Command(pk=self.pk_2, name=self.name_2, description=self.description_2, command_text=self.command_text_2)
        self.test_command_1.save()
        self.test_command_2.save()


    def test_CommandListJSON(self):
        url = reverse("command_list_api")
        response = self.client.post(url)
        py_response = json.loads(response.json())
        self.assertEqual(2, len(py_response))
        self.assertEqual(self.pk_1, py_response[0].get('pk'))
        self.assertEqual(self.name_1, py_response[0].get('fields').get('name'))
        self.assertEqual(self.description_1, py_response[0].get('fields').get('description'))
 
        self.assertEqual(self.pk_2, py_response[1].get('pk'))
        self.assertEqual(self.name_2, py_response[1].get('fields').get('name'))
        self.assertEqual(self.description_2, py_response[1].get('fields').get('description'))

    def test_CommandCreateOrUpdateJSON(self):
        # pk_1 = 1
        Command.objects.all().delete()
        self.assertEqual(0, Command.objects.count())
        url = reverse("command_create_update_api")
        # create
        data = {'name':self.name_1, 'description':self.description_1, 'command_text': self.command_text_1}
        response = self.client.post(url, data)
        py_response = response.json()
        new_id = py_response.get("id")
        self.assertEqual({"success": True, "created": True, "id": new_id}, py_response)
        self.assertEqual(Command.objects.count(), 1)

        # update
        data = {'pk': str(new_id), 'name': self.name_2, 'description': self.description_2, 'command_text': self.command_text_2}
        response = self.client.post(url, data)
        py_response = response.json()

        self.assertEqual({"success": True, "created": False, "id": str(new_id)}, py_response)
        self.assertEqual(Command.objects.count(), 1)
        created_obj = Command.objects.get(pk=new_id)
        self.assertEqual(self.name_2, created_obj.name)
        self.assertEqual(self.description_2, created_obj.description)
        self.assertEqual(self.command_text_2, created_obj.command_text)

class JobJsonTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_command_1 = Command(pk=1, name="test name", description="test description")
        self.test_command_2 = Command(pk=2, name="test name 2", description="test description 2")
        self.test_command_1.save()
        self.test_command_2.save()

        self.test_pipeline_1 = Pipeline(pk=1, name="test_name3", description="test description 3")
        self.test_pipeline_1.save()
        self.test_pipeline_1.commands.add(self.test_command_1)
        self.test_pipeline_1.commands.add(self.test_command_2)
        
        self.test_pipeline_2 = Pipeline(pk=2, name="test_name4", description="test description 4")
        self.test_pipeline_2.save()

        self.test_job_1 = Job(name="tjn_1", description="tjd_1", pipeline=self.test_pipeline_1, output="tjo_1", error="tje_1", exit_code="1", state=1, current_command=self.test_command_1, last_run=datetime.now())
        self.test_job_2 = Job(name="tjn_2", description="tjd_2", pipeline=self.test_pipeline_2, input="testdir", output="tjo_2", error="tje_2", exit_code="2", state=2, current_command=self.test_command_2, last_run=datetime.now())

        self.test_job_1.save()
        self.test_job_2.save()


    def test_JobListJSON(self):
        url = reverse("job_list_api")
        response = self.client.post(url)
        py_response = json.loads(response.json())
        self.assertEqual(2, len(py_response))

        self.assertEqual(self.test_job_1.pk, py_response[0].get('pk'))
        self.assertEqual(self.test_job_2.pk, py_response[1].get('pk'))

        fields_1 = py_response[0].get('fields')
        fields_2 = py_response[1].get('fields')

        self.assertEqual(self.test_job_1.name, fields_1.get('name'))
        self.assertEqual(self.test_job_2.name, fields_2.get('name'))

        self.assertEqual(self.test_job_1.description, fields_1.get('description'))
        self.assertEqual(self.test_job_2.description, fields_2.get('description'))

        self.assertEqual(self.test_job_1.pipeline.pk, fields_1.get('pipeline'))
        self.assertEqual(self.test_job_2.pipeline.pk, fields_2.get('pipeline'))

        self.assertEqual(self.test_job_1.input, fields_1.get('input'))
        self.assertEqual(self.test_job_2.input, fields_2.get('input'))

        self.assertEqual(self.test_job_1.output, fields_1.get('output'))
        self.assertEqual(self.test_job_2.output, fields_2.get('output'))

        self.assertEqual(self.test_job_1.exit_code, fields_1.get('exit_code'))
        self.assertEqual(self.test_job_2.exit_code, fields_2.get('exit_code'))

        self.assertEqual(self.test_job_1.state, fields_1.get('state'))
        self.assertEqual(self.test_job_2.state, fields_2.get('state'))

        self.assertEqual(self.test_job_1.current_command.pk, fields_1.get('current_command'))
        self.assertEqual(self.test_job_2.current_command.pk, fields_2.get('current_command'))

        format = "%Y-%m-%dT%H:%M:%S.%f"

        # remove last 3 microseconds as date isn't returned with that precision
        test_date_1 = str(self.test_job_1.last_run)[:-3]
        test_date_2 = str(self.test_job_2.last_run)[:-3]
        field_1 = str(datetime.strptime(fields_1.get('last_run'), format))[:-3]
        field_2 = str(datetime.strptime(fields_2.get('last_run'), format))[:-3]
        self.assertEqual(test_date_1, field_1)
        self.assertEqual(test_date_2, field_2)

    def test_JobCreateOrUpdateJSON(self):
        Job.objects.all().delete()
        self.assertEqual(0, Job.objects.count())

        url = reverse("job_create_update_api")
        # create
        data = {
            'name': self.test_job_1.name, 
            'description': self.test_job_1.description,
            'pipeline': self.test_job_1.pipeline.pk,
            'input': self.test_job_1.input,
            'output': self.test_job_1.output,
            'error': self.test_job_1.error,
            'exit_code': self.test_job_1.exit_code,
            'state': self.test_job_1.state,
            'current_command': self.test_job_1.current_command.pk,
            'last_run': self.test_job_1.last_run
        }

        response = self.client.post(url, data).json()
        self.assertEqual(1, Job.objects.count())
        created_job = Job.objects.get(pk=response.get('id'))
        self.assertEqual({u'id': response.get('id'), u'success': True, u'created': True}, response)

        self.assertEqual(data['name'], created_job.name)
        self.assertEqual(data['description'], created_job.description)
        self.assertEqual(data['pipeline'], created_job.pipeline.pk)
        self.assertEqual(data['input'], created_job.input)
        self.assertEqual(data['output'], created_job.output)
        self.assertEqual(data['error'], created_job.error)
        self.assertEqual(data['exit_code'], created_job.exit_code)
        self.assertEqual(data['state'], created_job.state)
        self.assertEqual(data['current_command'], created_job.current_command.pk)
        self.assertEqual(data['last_run'], created_job.last_run)

        #update
        data = {
            'pk': created_job.pk,
            'name': self.test_job_2.name, 
            'description': self.test_job_2.description,
            'pipeline': self.test_job_2.pipeline.pk,
            'input': self.test_job_2.input,
            'output': self.test_job_2.output,
            'error': self.test_job_2.error,
            'exit_code': self.test_job_2.exit_code,
            'state': self.test_job_2.state,
            'current_command': self.test_job_2.current_command.pk,
            'last_run': self.test_job_2.last_run
        }

        response = self.client.post(url, data).json()
        self.assertEqual(1, Job.objects.count())
        created_job = Job.objects.get(pk=response.get('id'))
        self.assertEqual({'id': response.get('id'), 'success': True, 'created': False}, response)
        self.assertEqual(data['name'], created_job.name)
        self.assertEqual(data['description'], created_job.description)
        self.assertEqual(data['pipeline'], created_job.pipeline.pk)
        self.assertEqual(data['input'], created_job.input)
        self.assertEqual(data['output'], created_job.output)
        self.assertEqual(data['error'], created_job.error)
        self.assertEqual(data['exit_code'], created_job.exit_code)
        self.assertEqual(data['state'], created_job.state)
        self.assertEqual(data['current_command'], created_job.current_command.pk)
        self.assertEqual(data['last_run'], created_job.last_run)


    def test_JobDeleteJSON(self):
        self.assertEqual(Job.objects.count(), 2)

        response = self.client.post(reverse("job_delete_api"), {"pk": self.test_job_2.pk}).json()
        response = json.loads(response)
        self.assertEqual({"success": True}, response)
        self.assertEqual(1, Job.objects.count())
        self.assertIn(self.test_job_1, Job.objects.all())
        self.assertNotIn(self.test_job_2, Job.objects.all())

class SlurmMonitorTestCase(TestCase):
    def setUp(self):
        self.monitor = SlurmMonitor()
    def test_get_job_reference(self):
        value = self.monitor.get_job_reference(self.SAMPLE_OUTPUT)
        self.assertEqual('663816', value)


    SAMPLE_OUTPUT = """
                    sourcing perl-5.16.2
                    sourcing casava-1.8.2
                    sourcing bcl2fastq-1.8.4
                    sourcing fastqc-0.11.4
                    sourcing texlive-1.2.2013
                    sourcing ImageMagick-6.8.4
                    exporting these variables 
                    TGACTOOLS_RUN_DIR=/tgac/pnp/qc
                    TGACTOOLS_SEQUENCER_DIR=/tgac/pnp/raw
                    TGACTOOLS_CONFIG_DIR=/tgac/software/production/tgac_tools/0.3/x86_64/config
                    TGACTOOLS_RUN_SUFFIX=
                    REFERENCES=/tgac/references/databases/kontaminants/
                    PAP dir : /tgac/pnp/qc/160411_SN790_0064_AHJMMJBCXX
                    Creating Directory: /tgac/pnp/qc/160411_SN790_0064_AHJMMJBCXX/test_new_miso/Scripts
                    getting base-mask
                    obtained base mask: y51,i6n1
                    Basecall directory /tgac/pnp/raw/HiSeq-2/160411_SN790_0064_AHJMMJBCXX/Data/Intensities/BaseCalls
                    running configureBclToFastq now
                    /tgac/software/production/bcl2fastq/1.8.4/x86_64/bin/configureBclToFastq.pl --input-dir /tgac/pnp/raw/HiSeq-2/160411_SN790_0064_AHJMMJBCXX/Data/Intensities/BaseCalls --output-dir test_new_miso --mismatches 1 --use-bases-mask y51,i6n1 --sample-sheet SampleSheet-PAP.csv --force
                    Submitted batch job 663816
    """

class MisoAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

        ik1 = InputKey(name='{feeb}')
        ik2 = InputKey(name='{ one }')
        ik3 = InputKey(name='{ boiled }')
        ik4 = InputKey(name='{ egg }')

        ik1.save()
        ik2.save()
        ik3.save()
        ik4.save()

        self.test_command_1 = Command(pk=1, name="test name", description="test description")
        self.test_command_2 = Command(pk=2, name="test name 2", description="test description 2")
        self.test_command_1.save()
        self.test_command_2.save()

        self.test_command_1.input_keys.add(ik1)
        self.test_command_1.input_keys.add(ik2)
        self.test_command_1.input_keys.add(ik3)

        self.test_pipeline_1 = Pipeline(pk=1, name="test_name3", description="test description 3")
        self.test_pipeline_1.save()
        self.test_pipeline_1.commands.add(self.test_command_1)
        self.test_pipeline_1.commands.add(self.test_command_2)
        
        self.test_pipeline_2 = Pipeline(pk=2, name="test_name4", description="test description 4")
        self.test_pipeline_2.save()

        self.test_job_0 = Job(name="tjn_0", description="tjd_0", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.FAILED])
        self.test_job_1 = Job(name="tjn_1", description="tjd_1", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.UNDETERMINED])
        self.test_job_2 = Job(name="tjn_2", description="tjd_2", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.QUEUED_ACTIVE])
        self.test_job_3 = Job(name="tjn_3", description="tjd_3", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.SYSTEM_ON_HOLD])
        self.test_job_4 = Job(name="tjn_4", description="tjd_4", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.USER_ON_HOLD])
        self.test_job_5 = Job(name="tjn_5", description="tjd_5", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.USER_SYSTEM_ON_HOLD])
        self.test_job_6 = Job(name="tjn_6", description="tjd_6", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.RUNNING])
        self.test_job_7 = Job(name="tjn_7", description="tjd_7", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.SYSTEM_SUSPENDED])
        self.test_job_8 = Job(name="tjn_8", description="tjd_8", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.USER_SUSPENDED])
        self.test_job_9 = Job(name="tjn_9", description="tjd_9", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.DONE])

        self.test_job_0.save()
        self.test_job_1.save()
        self.test_job_2.save()
        self.test_job_3.save()
        self.test_job_4.save()
        self.test_job_5.save()
        self.test_job_6.save()
        self.test_job_7.save()
        self.test_job_8.save()
        self.test_job_9.save()

# miso API specific tests
    def test_get_completed_jobs(self):
        query = "getCompletedTasks"
        url = reverse("miso")
        response = self.client.post(url, {"query": query}).json()
        response = json.loads(response)

        self.assertEqual(1, len(response))
        response = response[0]
        fields = response["fields"]
        self.assertEqual(self.test_job_9.pipeline.pk, fields["pipeline"])
        self.assertEqual(self.test_job_9.name, fields["name"])
        self.assertEqual(self.test_job_9.description, fields["description"])

    def test_get_failed_jobs(self):
        query = "getFailedTasks"
        url = reverse("miso")
        response = self.client.post(url, {"query": query}).json()
        response = json.loads(response)

        self.assertEqual(1, len(response))
        response = response[0]
        fields = response["fields"]
        self.assertEqual(self.test_job_0.pipeline.pk, fields["pipeline"])
        self.assertEqual(self.test_job_0.name, fields["name"])
        self.assertEqual(self.test_job_0.description, fields["description"])

    def test_get_pending_jobs(self):
        query = "getPendingTasks"
        url = reverse("miso")
        response = self.client.post(url, {"query": query}).json()
        response = json.loads(response)

        self.assertEqual(4, len(response))

        fields_1 = response[0]["fields"]
        fields_2 = response[1]["fields"]
        fields_3 = response[2]["fields"]
        fields_4 = response[3]["fields"]

        self.assertEqual(self.test_job_2.pipeline.pk, fields_1["pipeline"])
        self.assertEqual(self.test_job_2.name, fields_1["name"])
        self.assertEqual(self.test_job_2.description, fields_1["description"])

        self.assertEqual(self.test_job_3.pipeline.pk, fields_2["pipeline"])
        self.assertEqual(self.test_job_3.name, fields_2["name"])
        self.assertEqual(self.test_job_3.description, fields_2["description"])

        self.assertEqual(self.test_job_4.pipeline.pk, fields_3["pipeline"])
        self.assertEqual(self.test_job_4.name, fields_3["name"])
        self.assertEqual(self.test_job_4.description, fields_3["description"])

        self.assertEqual(self.test_job_5.pipeline.pk, fields_4["pipeline"])
        self.assertEqual(self.test_job_5.name, fields_4["name"])
        self.assertEqual(self.test_job_5.description, fields_4["description"])

    def test_get_jobs(self):
        query = "getTasks"
        url = reverse("miso")
        response = self.client.post(url, {"query": query}).json()
        response = json.loads(response)

        self.assertEqual(10, len(response))

    def test_get_job(self):
        query = "getTask"
        params = { "name": self.test_job_5.pk }
        data = { "query": query, "params": json.dumps(params) } 
        url = reverse("miso")
        response = self.client.post(url, data).json()

        response = json.loads(response)

        self.assertEqual(1, len(response))
        response = response[0]
        fields = response["fields"]
        self.assertEqual(self.test_job_5.pipeline.pk, fields["pipeline"])
        self.assertEqual(self.test_job_5.name, fields["name"])
        self.assertEqual(self.test_job_5.description, fields["description"])

    def test_get_pipeline(self):

        query = "getPipeline"
        params = { "name": self.test_pipeline_1.pk }
        data = { "query": query, "params": json.dumps(params) } 
        url = reverse("miso")
        response = self.client.post(url, data).json()

        response = json.loads(response)
        self.assertEqual(1, len(response))
        response = response[0]
        fields = response["fields"]
        self.assertEqual(self.test_pipeline_1.name, fields["name"])
        self.assertEqual(self.test_pipeline_1.description, fields["description"])
        keys = response["input_keys"]
        self.assertEqual(3, len(keys))
        for key in self.test_command_1.input_keys.all():
            self.assertTrue(key.name in keys)
        self.assertFalse('{ egg }' in keys)

    def test_get_pipelines(self):
        query = "getPipelines"
        url = reverse("miso")
        response = self.client.post(url, {"query": query}).json()
        response = json.loads(response)

        self.assertEqual(2, len(response))

    def test_submit_job(self):
        query = "submitTask"
        pipeline = self.test_pipeline_1.pk
        params = json.dumps({ "run": False })
        url = reverse("miso")
        response = self.client.post(url, { "query": query, "pipeline": pipeline, "params": params }).json()
        response = json.loads(response)

        self.assertEqual(1, len(response))
