# -*- coding: utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.

from threading import Lock
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from model_utils import models as utils
from model_utils import Choices
from haikunator import Haikunator

haiku = Haikunator()

def haikunate():
    '''
    Since the haikunator is a class method
    it could not be used directly as a default callable for
    a django field...hence this function.
    '''
    try:
        lock = Lock()
        lock.acquire()
        ret = haiku.haikunate(token_length=8, token_hex=True)
    finally:
        lock.release()
    return ret

SEVERITY_CHOICES = (
    ('DEBUG', 'DEBUG'),
    ('INFO', 'INFO'),
    ('WARNING', 'WARNING'),
    ('ERROR', 'ERROR')
)


class Task(utils.StatusModel):
    '''
    Keeps track of the processing of a message.  When messages are stored
    and queued for later processing, the file name of the inbound message
    is the same as the `name` field of this model with `.dat` applied
    to the end.
    '''
    name = models.CharField(
        max_length=50,
        null=False,
        help_text=_('The unique name of the job- autogenerated.'),
        verbose_name=_('Name'),
        unique=True,
        primary_key=True,
        default=haikunate
    )
    rule = models.ForeignKey(
        'quartet_capture.Rule',
        help_text=_('The rule to execute.'),
        verbose_name=_('Rule'),
        on_delete=models.CASCADE
    )
    STATUS = Choices('RUNNING', 'FINISHED', 'WAITING', 'FAILED', 'QUEUED')
    type = models.CharField(
        max_length=20,
        verbose_name=_("Type"),
        help_text=_("The type of task.  Default is 'Input'.  The task type"
                    " is the responsibility of the component queuing/creating"
                    " the task."),
        null=False,
        default='Input'
    )
    execution_time = models.PositiveIntegerField(
        default=0,
        help_text=_('The time (in seconds) it took for this task to execute.'),
        verbose_name=_('Execution Time'),
    )


class TaskMessage(models.Model):
    '''
    A message relative to the execution of a specific task.
    '''
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name=_("Task"),
        help_text=_("The task that created the message."),
        null=False
    )
    level = models.CharField(
        max_length=10,
        verbose_name=_("Severity Level"),
        help_text=_("The severity level of the message."),
        null=False,
        choices=SEVERITY_CHOICES,
        default='INFO'
    )
    created = utils.AutoCreatedField(
        verbose_name=_("Created Time"),
        help_text=_("The time the task message was created."),
    )
    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("The message data."),
        null=False
    )


class Field(models.Model):
    '''
    An abstract name/value pair model
    '''
    name = models.CharField(
        max_length=100,
        null=False,
        db_index=True,
        help_text=_('The name of the field.'),
        verbose_name=_('Name')
    )
    value = models.TextField(
        help_text=_('The value of the field.'),
        verbose_name=_('Value')
    )
    description = models.CharField(
        max_length=500,
        null=True,
        help_text=_('A short description.'),
        verbose_name=_('Description')
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'quartet_capture'


class TaskParameter(Field):
    '''
    Fields associated with Tasks.
    '''
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=False,
        help_text=_('A field associted with a given task.  Fields are passed'
                    ' into task instances when they are dynamically created'
                    ' as variables.'),
        verbose_name=_('Task')
    )

    class Meta:
        verbose_name = _('Task Parameter')
        unique_together = ('name', 'task')
        app_label = 'quartet_capture'


class TaskHistory(utils.TimeStampedModel):
    """
    Keeps a history of each time a task is created, executed, etc.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name=_("Task"),
        help_text=_("The related Task."),
        null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("User"),
        help_text=_("The user that created or ran the task."),
        null=True
    )


class Rule(models.Model):
    '''
    Defines a rule which consists of multiple steps.
    '''
    name = models.CharField(
        max_length=100,
        null=False,
        help_text=_('A rule is composed of multiple steps that execute in '
                    'order.'),
        verbose_name=_('Rule'),
        unique=True
    )
    description = models.CharField(
        max_length=500,
        null=True,
        help_text=_('A short description.'),
        verbose_name=_('Description')
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Rule')
        app_label = 'quartet_capture'


class RuleParameter(Field):
    '''
    Fields associated with rules.
    '''
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        null=False,
        help_text=_('A parameter associted with a given rule.  Each parameter'
                    ' is passed into the Rule as a dictionary entrance in '
                    'the rule\'s context.'),
        verbose_name=_('Rule Field')
    )

    class Meta:
        verbose_name = _('Rule Parameter')
        unique_together = ('name', 'rule')
        app_label = 'quartet_capture'


class Step(models.Model):
    '''
    Defines a discrete step within a rule.  Steps are executed
    as defined in order.  All steps implement the quartet_capture
    rules.Step class interface.  Any configured Step Class Paths
    must be on the PYTHONPATH and/or findable by the Rule class as
    each Step class is loaded dynamically.
    '''
    name = models.CharField(
        max_length=100,
        null=False,
        help_text=_('A step is a piece of logic that runs within a rule.'),
        verbose_name=_('Step')
    )
    description = models.CharField(
        max_length=500,
        null=True,
        help_text=_('A short description.'),
        verbose_name=_('Description')
    )
    step_class = models.CharField(
        max_length=500,
        null=False,
        help_text=_('The full python path to where the Step class is defined '
                    'for example, mypackage.mymodule.MyStep'),
        verbose_name=_('Class Path')
    )
    order = models.IntegerField(
        null=False,
        help_text=_('Defines the order in which the step is executed.  Steps'
                    ' are executed in numerical order.'),
        verbose_name=_('Execution Order'),
    )
    rule = models.ForeignKey(
        Rule,
        null=False,
        on_delete=models.CASCADE,
        help_text=_('The parent rule.'),
        verbose_name=_('Rule')
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Step')
        unique_together = ('name', 'rule', 'order')
        app_label = 'quartet_capture'
        ordering = ['order']


class StepParameter(Field):
    '''
    Fields associated with Steps.
    '''
    step = models.ForeignKey(
        Step,
        on_delete=models.CASCADE,
        null=False,
        help_text=_('A field associted with a given step.  Fields are passed'
                    ' into Step instances when they are dynamically created'
                    ' as variables.'),
        verbose_name=_('Step Field')
    )

    class Meta:
        verbose_name = _('Step Parameter')
        unique_together = ('name', 'step')
        app_label = 'quartet_capture'
