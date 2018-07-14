#!/usr/bin/env python
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
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
django.setup()
from lxml.etree import XMLSyntaxError
from django.test import TestCase
from quartet_epcis.parsing.steps import EPCISParsingStep
from quartet_capture import models
from quartet_capture import rules
from quartet_capture.loader import load_data
from quartet_capture.rules import TaskMessaging

class TestQuartet_capture(TestCase):

    def setUp(self):
        pass

    def test_epcis_rule(self):
        # create a new rule and give it a test parameter
        db_task = self._create_task()
        db_rule = db_task.rule
        data = self.load_test_data()
        # declare a rule class
        rule = rules.Rule(db_rule, db_task)
        # execute the rule
        rule.execute(data)

    def test_bad_step(self):
        # create a new rule and give it a test parameter
        db_task = self._create_bad_task()
        db_rule = db_task.rule
        data = self.load_test_data()
        # declare a rule class
        with self.assertRaises(rules.Rule.StepNotFound):
            rule = rules.Rule(db_rule, db_task)

    def test_bad_error_handler(self):
        # create a new rule and give it a test parameter
        db_task = self._create_bad_task()
        db_rule = self._create_rule_bad_error_handler()
        db_task.rule = db_rule
        db_task.save()
        data = self.load_test_data()
        # declare a rule class
        with self.assertRaises(rules.Rule.StepNotFound):
            rule = rules.Rule(db_rule, db_task)

    def test_bad_data(self):
        # create a new rule and give it a test parameter
        db_task = self._create_task()
        db_rule = db_task.rule
        data = self.load_test_data('data/bad-xml.xml')
        # declare a rule class
        rule = rules.Rule(db_rule, db_task)
        # execute the rule
        with self.assertRaises(XMLSyntaxError):
            rule.execute(data)

    def test_data_loader(self):
        print('test_data_loader')
        load_data()

    def _create_rule(self):
        db_rule = models.Rule()
        db_rule.name = 'epcis'
        db_rule.description = 'EPCIS Parsing rule utilizing quartet_epcis.'
        db_rule.save()
        rp = models.RuleParameter(name='test name', value='test value',
                                  rule=db_rule)
        rp.save()
        # create a new step
        epcis_step = models.Step()
        epcis_step.name = 'parse-epcis'
        epcis_step.description = 'Parse the EPCIS data and store in database.'
        epcis_step.order = 1
        epcis_step.step_class = 'quartet_epcis.parsing.steps.EPCISParsingStep'
        epcis_step.rule = db_rule
        epcis_step.save()
        return db_rule

    def _create_rule_bad_step(self):
        db_rule = models.Rule()
        db_rule.name = 'epcis'
        db_rule.description = 'EPCIS Parsing rule utilizing quartet_epcis.'
        db_rule.save()
        rp = models.RuleParameter(name='test name', value='test value',
                                  rule=db_rule)
        rp.save()
        # create a new step
        epcis_step = models.Step()
        epcis_step.name = 'no-no-epcis'
        epcis_step.description = 'I do not exist step.'
        epcis_step.order = 1
        epcis_step.step_class = 'quartet_epcis.not_here.steps.IDontExist'
        epcis_step.rule = db_rule
        epcis_step.save()
        return db_rule

    def test_bad_parameter(self):
        with self.assertRaises(rules.Step.ParameterNotFoundError):
            task = self._create_task()
            step = EPCISParsingStep(db_task=task)
            step.get_parameter('i do not exist', raise_exception=True)

    def _create_rule_bad_error_handler(self):
        db_rule = models.Rule()
        db_rule.name = 'epcis2'
        db_rule.description = 'EPCIS Parsing rule utilizing quartet_epcis.'
        db_rule.save()
        rp = models.RuleParameter(name='test name', value='test value',
                                  rule=db_rule)
        rp.save()
        # create a new step
        epcis_step = models.Step()
        epcis_step.name = 'no-no-epcis'
        epcis_step.description = 'bad step.'
        epcis_step.order = 1
        epcis_step.step_class = 'tests.test_models.PoorStep'
        epcis_step.rule = db_rule
        epcis_step.save()
        return db_rule

    def _create_task(self):
        db_task = models.Task()
        db_task.status = 'QUEUED'
        db_task.name = 'test'
        db_task.rule = self._create_rule()
        db_task.save()
        return db_task

    def _create_bad_task(self):
        db_task = models.Task()
        db_task.status = 'QUEUED'
        db_task.name = 'test'
        db_task.rule = self._create_rule_bad_step()
        db_task.save()
        return db_task

    def load_test_data(self, file_path='data/epcis.xml'):
        curpath = os.path.dirname(__file__)
        f = open(os.path.join(curpath, file_path))
        return f.read().encode()

    def test_rule_no_steps(self):
        # create a new rule and give it a test parameter
        db_task = self._create_task()
        rule = models.Rule.objects.create(name="blank rule",
                                          description="bad rule for unit test")
        db_rule = rule
        db_task.rule = db_rule
        data = self.load_test_data()
        # declare a rule class
        rule = rules.Rule(db_rule, db_task)
        with self.assertRaises(rules.Rule.StepsNotConfigured):
            # execute the rule
            rule.execute(data)

    def test_task_messages(self):
        rule = self._create_rule()
        task = models.Task()
        task.name='Test task'
        task.status='RUNNING'
        task.rule=rule
        task.save()
        tm = TaskMessaging(task=task)
        tm.debug('This is a debugmessage')
        tm.info('This is an info message')
        tm.warning('This is a warning!')
        tm.error('This is an error!!!')

    def tearDown(self):
        pass

    class PoorStep(EPCISParsingStep):
        def on_failure(self):
            raise Exception('I am a bad step')
