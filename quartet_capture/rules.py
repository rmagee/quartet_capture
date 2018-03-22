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

import logging
import importlib
from abc import ABCMeta, abstractmethod
from quartet_capture import models
from pydoc import locate

logger = logging.getLogger('quartet_capture')


class Rule:
    '''
    The Rule class loads all models.Step data from the database and creates,
    from each model, a concrete Step class that can execute against the
    data passed into the rule.  Steps execute in the order they are configured
    in the database by their `order` field.
    '''

    def __init__(self, rule: models.Rule):
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
        if len(self.steps) == 0:
            raise self.StepsNotConfigured(
                'The rule %s was loaded with no '
                'steps configured.' % self.db_rule.name
            )
        for number, step in self.steps.items():
            logger.debug('Executing step %s.', number)
            data = step.execute(data, self.context)

    def _load_steps(self):
        '''
        Dynamically loads each of the steps into memory for execution.
        :return: A list of Step instances.
        '''
        db_steps = self.db_rule.step_set.all()
        steps = {}
        for db_step in db_steps:
            step = self._load_step(db_step)
            steps[db_step.order] = step
        return steps

    def _load_step(self, db_step: models.Step):
        '''
        Attempts to load the python module defined in the database Step
        into memory for execution.
        :param db_step: The database Step configuration.
        :return: A Step instance.
        '''
        step = locate(db_step.step_class)
        if not step:
            step = self._step_import(db_step.step_class)
            if not step:
                raise Rule.StepNotFound(
                    'The step %s could not be loaded. '
                    'make sure it and '
                    'any dependencies are on the PYTHONPATH '
                    'and can be loaded.', db_step.step_class
                )
        params = {p.name: p.value
                  for p in db_step.stepparameter_set.all()}
        return step(params)

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


class Step(metaclass=ABCMeta):
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

    def __init__(self, *args, **kwargs):
        '''
        Any parameters loaded from the database will be sent
        via the **kwargs keyword arguments parameter.
        :param args:
        :param kwargs: Any parameters loaded from the database.
        '''
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
