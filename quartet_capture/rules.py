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

import traceback
import logging
import importlib
from datetime import datetime
from enum import Enum
from abc import ABCMeta, abstractmethod
from quartet_capture import models, errors
from pydoc import locate
from django.utils.translation import gettext as _
from django.db import transaction
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

    def debug(self, *args: object, task: models.Task = None):
        '''
        Creates a debug message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(*args, task=task or self.task,
                                  level=TaskMessageLevel.DEBUG)

    def info(self, *args: object, task: models.Task = None):
        '''
        Creates an info message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(*args, task=task)

    def warning(self, *args: object, task: models.Task = None):
        '''
        Creates a warning message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(*args, task=task,
                                  level=TaskMessageLevel.WARNING)

    def error(self, *args: object, task: models.Task = None):
        '''
        Creates an error message.
        :param message: The message to store.
        :param task: The associated task.
        '''
        self._create_task_message(*args, task=task,
                                  level=TaskMessageLevel.ERROR)

    def _create_task_message(
        self,
        *args: object,
        task: models.Task = None,
        level: TaskMessageLevel = TaskMessageLevel.INFO
    ):
        '''
        Creates a TaskMessage model instance and saves it.
        :param message: The message to store.
        :param task: The associated task.
        :param level: The severity of the message.
        '''
        if len(args) > 1:
            message = args[0] % tuple(args[1:])
        else:
            message = args[0]
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


class RuleContext:
    '''
    The RuleContext is passed to each step in the rule and can be
    used by steps to pass data to and from one another.
    '''

    def __init__(self, rule_name: str, task_name: str, context: dict = None):
        '''
        Initializes a new RuleContext.
        :param rule_name: The name of the current rule.
        :param task_name: The name of the current task.
        :param context: A dictionary for use by steps to communicate data.
        '''
        self.context = context or {}
        self._rule_name = rule_name
        self._task_name = task_name

    def get_required_context_variable(self, key: str):
        '''
        Returns a required context variable from the context dictionary by
        key or throws a BaseCaptureError.
        :param key: The key to utilize for the lookup.
        :return: The value found in the context dictionary.
        '''
        ret = self.context.get(key)
        if not ret:
            raise errors.ExpectedContextVariableError(
                _('The context variable with key %s could not be located '
                  'in the rule context.  This typically indicates that an '
                  'expected upstream step has not behaved properly and '
                  'populated the context with the expeted data.  Check '
                  'your rule configuration.'), key
            )
        return ret

    @property
    def task_name(self):
        return self._task_name

    @task_name.setter
    def task_name(self, value):
        self._task_name = value

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    @property
    def rule_name(self):
        return self._rule_name

    @rule_name.setter
    def rule_name(self, value):
        self._rule_name = value


class Rule(TaskMessaging):
    '''
    The Rule class loads all models.Step data from the database and creates,
    from each model, a concrete Step class that can execute against the
    data passed into the rule.  Steps execute in the order they are configured
    in the database by their `order` field.

    A rule will pass a `RuleContext` to all steps in the rule.  The initial
    state of the context contains the rule name and the rule's parameters (if
    any).  The rule parameters are in the context's context dictionary as
    a dictionary entry under the name of RULE_PARAMETERS
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
        self.start_time = datetime.utcnow()
        self.db_rule = rule
        self.db_task = task
        super().__init__(self.db_task)
        self.context = RuleContext(rule.name, task.name)
        self.context.context['RULE_PARAMETERS'] = {p.name: p.value for p in
                                                   self.db_rule.ruleparameter_set.all()}
        self.steps = self._load_steps()

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
            with transaction.atomic():
                for number, step in self.steps.items():
                    # execute each step in order
                    logger.debug('Executing step %s.', number)
                    try:
                        new_data = step.execute(data, self.context)
                        data = new_data or data
                    except:
                        # try to clean up and then raise the original exception
                        self._on_step_failure(step)
                        raise
        except Exception:
            # make sure error info is routed into the TaskMessage
            # execution messages
            # for this rule
            data = traceback.format_exc()
            self.error('Could not execute the rule.\r\n%s' % data)
            raise

    def _on_step_failure(self, step):
        '''
        If a step fails, it has a last chance to make things right and
        do any cleanup, etc...this is called when a failure occurs.
        :param data: The data the step failed to process
        :param step: The step that failed.
        '''
        try:
            self.error('Performing step failure routine.')
            step.on_failure()
        except Exception:
            self.error('Step\'s on failure routine failed!')
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
                    'and can be loaded.' % db_step.step_class
                )
        params = {p.name: p.value
                  for p in db_step.stepparameter_set.all()}
        self.info('Step loaded successfully.')
        return step(self.db_task, **params)

    def _step_import(self, step_name: str):
        '''
        Called if _load_step fails as a backup.
        :return: A Step instance.
        '''
        try:
            components = step_name.rsplit('.', 1)
            logger.debug('components = %s', components)
            module = importlib.import_module(components[0])
            step = getattr(module, components[1])
            return step
        except (ImportError, AttributeError):
            logger.exception('Could not load step %s', step_name)
            tb = traceback.format_exc()
            self.error(tb)


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
        self._declared_parameters = {}
        self._check_parameters(self.parameters, self._declared_parameters)

    @property
    @abstractmethod
    def declared_parameters(self):
        '''
        Define any parameters you want to declare here.
        :return: A List of Parameter instances.
        '''
        return self._declared_parameters

    @abstractmethod
    def execute(self, data, rule_context: RuleContext):
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

    def get_parameter(self, parameter_name: str,
                      default: str = None,
                      raise_exception: bool = False):
        '''
        A helper function that looks
        at the local parameters dict and returns a parameter value
        or the value of the default parameter if it does not exist.  To
        make finding the parameter required and to raise an exception if it
        is not found, set the `raise_exception` parameter to `True`.
        :param parameter_name: The name of the parameter from which the value
        should be obtained.
        :param default: If the parameter is not found, return this value-
        default is None.
        :param raise_exception: Whether or not to raise an Exception if
        the value is not found.
        :return: The value of the parameter.
        '''
        ret = self.parameters.get(parameter_name, default)
        if not ret and raise_exception == True:
            raise self.ParameterNotFoundError(
                'Parameter with name %s could '
                'not be found in the parameters'
                'list.  Make sure this parameter'
                ' is configured in the Step\'s '
                'parameters settings.' % parameter_name
            )
        return ret

    def get_boolean_parameter(self, parameter_name: str,
                              default: bool = False,
                              raise_exception: bool = False):
        '''
        A helper function that will convert a boolean parameter value from
        the string stored into the database into a valid python bool.  Any
        of the following parameter values will result in a `True` result:
        * True
        * true
        * 1
        * Any capital/lower variation of the word True- i.e., trUe.
        :param parameter_name: The name of the parameter from which the value
        should be obtained.
        :param default: If the parameter is not found, return this value-
        default is None.
        :param raise_exception: Whether or not to raise an Exception if
        the value is not found.
        :return: The value of the parameter.
        '''
        ret = False
        val = self.get_parameter(parameter_name, default, raise_exception)
        if isinstance(val, str):
            ret = val.lower() in ['true', '1']
        return ret or default

    def get_or_create_parameter(self, step: models.Step, name: str,
                                default: str,
                                description: str = 'Default value.'):
        '''
        Gets or creates the parameter with *name*.  Returns the existing
        value if the parameter exists or creates the new one with value
        *default* and returns that.
        :param name: The name of the parameter.
        :param default: The value to add if creating a new parameter.
        :param description: The description to add.
        :return: The value of the parameter.
        '''
        try:
            param = models.StepParameter.objects.get(name=name)
        except models.StepParameter.DoesNotExist:
            param = models.StepParameter.objects.create(
                name=name,
                value=default,
                step=step,
                description=description
            )
        return param.value

    @abstractmethod
    def on_failure(self):
        '''
        Implement to handle any failed steps for post processing/cleanup.
        :param data: The data that was passed in.
        :param context: The rule context dict.
        '''
        pass

    def _check_parameters(self, declared:dict, parameters:dict):
        for parameter in parameters.keys():
            if not declared.get(parameter):
                raise self.ParameterNotFoundError(
                    _('A parameter with name %s was found in the parameters '
                      'collection.  This parameter is not valid for this '
                      'step. This step will accept the following parameters: '
                      '%s' % (parameter, parameters.keys()))
                )

    class ParameterNotFoundError(Exception):
        '''
        Raise when expecting a parameter and it was not found.
        '''
        pass
