# Generated by Django 2.0.2 on 2018-07-13 17:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import quartet_capture.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A rule is composed of multiple steps that execute in order.', max_length=100, unique=True, verbose_name='Rule')),
                ('description', models.CharField(help_text='A short description.', max_length=500, null=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Rule',
            },
        ),
        migrations.CreateModel(
            name='RuleParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='The name of the field.', max_length=100, verbose_name='Name')),
                ('value', models.TextField(help_text='The value of the field.', verbose_name='Value')),
                ('description', models.CharField(help_text='A short description.', max_length=500, null=True, verbose_name='Description')),
                ('rule', models.ForeignKey(help_text="A parameter associted with a given rule.  Each parameter is passed into the Rule as a dictionary entrance in the rule's context.", on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Rule', verbose_name='Rule Field')),
            ],
            options={
                'verbose_name': 'Rule Parameter',
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A step is a piece of logic that runs within a rule.', max_length=100, verbose_name='Step')),
                ('description', models.CharField(help_text='A short description.', max_length=500, null=True, verbose_name='Description')),
                ('step_class', models.CharField(help_text='The full python path to where the Step class is defined for example, mypackage.mymodule.MyStep', max_length=100, verbose_name='Class Path')),
                ('order', models.IntegerField(help_text='Defines the order in which the step is executed.  Steps are executed in numerical order.', verbose_name='Execution Order')),
                ('rule', models.ForeignKey(help_text='The parent rule.', on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Rule', verbose_name='Rule')),
            ],
            options={
                'verbose_name': 'Step',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='StepParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='The name of the field.', max_length=100, verbose_name='Name')),
                ('value', models.TextField(help_text='The value of the field.', verbose_name='Value')),
                ('description', models.CharField(help_text='A short description.', max_length=500, null=True, verbose_name='Description')),
                ('step', models.ForeignKey(help_text='A field associted with a given step.  Fields are passed into Step instances when they are dynamically created as variables.', on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Step', verbose_name='Step Field')),
            ],
            options={
                'verbose_name': 'Step Parameter',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('status', model_utils.fields.StatusField(choices=[('RUNNING', 'RUNNING'), ('FINISHED', 'FINISHED'), ('WAITING', 'WAITING'), ('FAILED', 'FAILED'), ('QUEUED', 'QUEUED')], default='RUNNING', max_length=100, no_check_for_status=True, verbose_name='status')),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', verbose_name='status changed')),
                ('name', models.CharField(default=quartet_capture.models.haikunate, help_text='The unique name of the job- autogenerated.', max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='Name')),
                ('type', models.CharField(default='Input', help_text="The type of task.  Default is 'Input'.  The task type is the responsibility of the component queuing/creating the task.", max_length=20, verbose_name='Type')),
                ('execution_time', models.PositiveIntegerField(default=0, help_text='The time (in seconds) it took for this task to execute.', verbose_name='Execution Time')),
                ('rule', models.ForeignKey(help_text='The rule to execute.', on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Rule', verbose_name='Rule')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaskHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('task', models.ForeignKey(help_text='The related Task.', null=True, on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Task', verbose_name='Task')),
                ('user', models.ForeignKey(help_text='The user that created or ran the task.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaskMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('DEBUG', 'DEBUG'), ('INFO', 'INFO'), ('WARNING', 'WARNING'), ('ERROR', 'ERROR')], default='INFO', help_text='The severity level of the message.', max_length=10, verbose_name='Severity Level')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, help_text='The time the task message was created.', verbose_name='Created Time')),
                ('message', models.TextField(help_text='The message data.', verbose_name='Message')),
                ('task', models.ForeignKey(help_text='The task that created the message.', on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Task', verbose_name='Task')),
            ],
        ),
        migrations.CreateModel(
            name='TaskParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='The name of the field.', max_length=100, verbose_name='Name')),
                ('value', models.TextField(help_text='The value of the field.', verbose_name='Value')),
                ('description', models.CharField(help_text='A short description.', max_length=500, null=True, verbose_name='Description')),
                ('task', models.ForeignKey(help_text='A field associted with a given task.  Fields are passed into task instances when they are dynamically created as variables.', on_delete=django.db.models.deletion.CASCADE, to='quartet_capture.Task', verbose_name='Task')),
            ],
            options={
                'verbose_name': 'Task Parameter',
            },
        ),
        migrations.AlterUniqueTogether(
            name='taskparameter',
            unique_together={('name', 'task')},
        ),
        migrations.AlterUniqueTogether(
            name='stepparameter',
            unique_together={('name', 'step')},
        ),
        migrations.AlterUniqueTogether(
            name='step',
            unique_together={('name', 'rule', 'order')},
        ),
        migrations.AlterUniqueTogether(
            name='ruleparameter',
            unique_together={('name', 'rule')},
        ),
    ]
