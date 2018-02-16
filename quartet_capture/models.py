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

from django.db import models
from django.utils.translation import gettext_lazy as _


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

    class Meta:
        abstract = True


class Rule(models.Model):
    '''
    Defines a rule which consists of multiple steps.
    '''
    name = models.CharField(
        max_length=100,
        null=False,
        help_text=_('A rule is composed of multiple steps that execute in'
                    'order.'),
        verbose_name=_('Rule')
    )
    description = models.CharField(
        max_length=500,
        null=True,
        help_text=_('A short description.'),
        verbose_name=_('Description')
    )


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
        max_length=100,
        null=False,
        help_text=_('The full python path to where the Step class is defined'
                    'for example, mypackage.mymodule.MyStep'),
        verbose_name=_('Class Path')
    )
    order = models.IntegerField(
        null=False,
        help_text=_('Defines the order in which the step is executed.  Steps'
                    'are executed in numerical order.'),
        verbose_name=_('Execution Order'),
        unique=True,
    )
    rule = models.ForeignKey(
        Rule,
        null=False,
        on_delete=models.CASCADE,
        help_text=_('The parent rule.'),
        verbose_name=_('Rule')
    )

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
