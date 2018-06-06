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

import sys
import traceback
import logging
import importlib
from enum import Enum
from abc import ABCMeta, abstractmethod
from quartet_capture import models
from pydoc import locate
from django.utils.translation import gettext as _

logger = logging.getLogger('quartet_capture')


class TaskMessageLevel(Enum):
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class TaskMessaging:
    '''
    A helper class to handle the creation and insertion of task messages.
    The helper class should never raise an exception handling a message.
    '''

    def __init__(self, task: models.Task = None):
        '''
        Initializes with an optional default task.
        :param task: The task to associate messages with.
        '''
        self.task = task

    def debug(self, message: str, task: models.Task = None):
        '''
        Creates a debug message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(message, task or self.task,
                                  TaskMessageLevel.DEBUG)

    def info(self, message: str, task: models.Task = None):
        '''
        Creates an info message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(message, task)

    def warning(self, message: str, task: models.Task = None):
        '''
        Creates a warning message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(message, task, TaskMessageLevel.WARNING)

    def error(self, message: str, task: models.Task = None):
        '''
        Creates an error message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(message, task, TaskMessageLevel.ERROR)

    def _create_task_message(
        self,
        message: str,
        task: models.Task = None,
        level: TaskMessageLevel = TaskMessageLevel.INFO,
    ):
        '''
        Creates a TaskMessage model instance and saves it.
        :param message: The message to store.
        :param task: The associated task.
        :param level: The severity of the message.
        '''
        try:
            if not (task or self.task):
                raise models.Task.DoesNotExist('No task was supplied.')
            models.TaskMessage.objects.create(
                message=message,
                task=task or self.task,
                level=level.value
            )
        except:
            logger.exception('Could not create TaskMessage.')


class Rule(TaskMessaging):
    '''
    The Rule class loads all models.Step data from the database and creates,
    from each model, a concrete Step class that can execute against the
    data passed into the rule.  Steps execute in the order they are configured
    in the database by their `order` field.
    '''

    def __init__(self, rule: models.Rule, task: models.Task):
        '''
        A Rule is a conglomeration of Step class instances along with
        a context that gets passed along to each step as it is executed.
        The Rule is built by deserializing the data in the models.Rule
        django model instance into a Rule class instance.
        This initializer will create all of the Step classes and load
        them into memory for execution.
        :param rule: The django models.Rule instance.
        '''
        self.db_rule = rule
        self.db_task = task
        super().__init__(self.db_task)
        self.steps = self._load_steps()
        self.context = {p.name: p.value for p in
                        self.db_rule.ruleparameter_set.all()}

    def execute(self, data):
        '''
        Implement this to handle inbound messaging and to
        do any pre-rule execution handling.

        Raises a Rule.StepsNotConfigured exception if no steps were configured.

        :param data: The data to be handled by each of the steps in the rule.
        '''
        self.info(_('Beginning execution of the Rule.'))
        try:
            if len(self.steps) == 0:
                self.error(
                    _('No steps were configured for the rule. Aborting.'))
                raise self.StepsNotConfigured(
                    'The rule %s was loaded with no '
                    'steps configured.' % self.db_rule.name
                )
            for number, step in self.steps.items():
                logger.debug('Executing step %s.', number)
                data = step.execute(data, self.context)
        except Exception:
            # make sure error info is routed into the TaskMessage
            # execution messages
            # for this rule
            data = traceback.format_exc()
            self.error('Could not execute the rule.')
            self.error(data)
            logger.exception('Failed task execution.')
            raise

    def _load_steps(self):
        '''
        Dynamically loads each of the steps into memory for execution.
        :return: A list of Step instances.
        '''
        try:
            db_steps = self.db_rule.step_set.all()
            steps = {}
            for db_step in db_steps:
                step = self._load_step(db_step)
                steps[db_step.order] = step
            return steps
        except Exception:
            # make sure error info is routed into the TaskMessage
            # execution messages
            # for this rule
            data = traceback.format_exc()
            self.error('Could not load the steps.')
            self.error(data)
            raise

    def _load_step(self, db_step: models.Step):
        '''
        Attempts to load the python module defined in the database Step
        into memory for execution.
        :param db_step: The database Step configuration.
        :return: A Step instance.
        '''
        self.info(_('Loading step %s') % db_step.name)
        step = locate(db_step.step_class)
        if not step:
            step = self._step_import(db_step.step_class)
            if not step:
                self.error(_(
                    'Step %s could not be loaded. '
                    'Make sure it and any dependencies are on the PYTHONPATH '
                    'and that the class string is correct.'
                ) % db_step.name)
                raise Rule.StepNotFound(
                    'The step %s could not be loaded. '
                    'make sure it and '
                    'any dependencies are on the PYTHONPATH '
                    'and can be loaded.', db_step.step_class
                )
        params = {p.name: p.value
                  for p in db_step.stepparameter_set.all()}
        self.info('Step loaded successfully.')
        return step(params, self.db_task)

    def _step_import(self, step_name: str):
        '''
        Called if _load_step fails as a backup.
        :return: A Step instance.
        '''
        components = step_name.rsplit('.', 1)
        logger.debug('components = %s', components)
        module = importlib.import_module(components[0])
        step = getattr(module, components[1])
        return step

    @abstractmethod
    def on_success(self, data, context: dict):
        '''
        Implement this to handle a successful execution.
        :param data: The data that was handled
        :param context: The state of the context after processing.
        '''
        pass

    def on_failure(self, data, context: dict):
        '''
        Implement to handle any failed rules for post processing/cleanup.
        :param data: The data that was passed in.
        :param context: The rule context dict.
        '''
        pass

    class StepNotFound(Exception):
        '''
        If a step can not be loaded into memory, this will be raised
        by the Rule during initialization.
        '''
        pass

    class StepsNotConfigured(Exception):
        '''
        If a step can not be loaded into memory, this will be raised
        by the Rule during initialization.
        '''
        pass


class Parameter(metaclass=ABCMeta):
    '''
    Defines a parameter for Steps.  Steps can declare their parameters
    and validate them when executing (both optional).
    '''

    def __init__(self,
                 datatype: type,
                 name: str,
                 regex_pattern: str,
                 description: str = None
                 ):
        '''
        Initialize a parameter.
        :param datatype: The expected datatype.
        :param name: The name.
        :param regex_pattern: A regex pattern to use to check against expected
        values.
        :param description: A description of the parameter and what it is for.
        '''
        self.type = type
        self.name = name
        self.description = description
        self.regex_pattern = regex_pattern


class Step(TaskMessaging, metaclass=ABCMeta):
    '''
    Each Rule has a number of steps that execute in order.
    A step has a defined python.

    A step can declare it's parameters by providing a dictionary with
    parameter name and description.  For example:
    declared_paramters = {'order':'How to order the data.  Possible values
    are ascending and descending.'} ...

    The declared parameters field is used only for reflection to provide
    insight for GUIs and administrative applications looking to interrogate
    steps.
    '''

    def __init__(self, db_task: models.Task, **kwargs):
        '''
        Any parameters loaded from the database will be sent
        via the **kwargs keyword arguments parameter.
        :param args:
        :param kwargs: Any parameters loaded from the database.
        '''
        super().__init__(db_task)
        self.parameters = kwargs or {}
        self._declared_parameters = []

    @property
    @abstractmethod
    def declared_parameters(self):
        '''
        Define any parameters you want to declare here.
        :return: A List of Parameter instances.
        '''
        return self._declared_parameters

    @abstractmethod
    def execute(self, data, rule_context: dict):
        '''
        Implement this to handle the inbound data.  Modify data if you
        want subsequent steps to handle a modified version of the
        original data.  Otherwise, store any custom data that you may
        want to handle in subsequent steps in the rule_context by adding
        a new name value pair to the dictionary.
        :param data: The data passed in.
        :param fields: The fields configured for this step.
        :param rule_context: The overall rule context.
        :return: Either return the original data or None.  If None
        then the data will remain unchanged for following steps.
        If the data is modified, then subsequent steps will get the
        '''
        pass

    def get_parameter(self, parameter_name):
        '''
        A helper function that looks
        at the local parameters dict and returns a parameter value
        or None if it does not exist.
        :param parameter_name: The name of the parameter from which the value
        should be obtained.
        :return: The value of the parameter.
        '''
        return self.parameters.get(parameter_name, None)
