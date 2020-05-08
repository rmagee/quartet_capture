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
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth.models import Group, User
from quartet_capture import models
from quartet_capture.rules import clone_rule
from quartet_capture.views import get_rules_by_filter
from quartet_capture.management.commands.create_capture_groups import Command

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
django.setup()


class ViewTest(APITestCase):
    '''
    Tests the capture API and executes the rule framework.
    '''

    def setUp(self):
        user = User.objects.create_user(username='testuser',
                                        password='unittest',
                                        email='testuser@seriallab.local')
        Command().handle()
        oag = Group.objects.get(name='Capture Access')
        user.groups.add(oag)
        user.save()
        self.client.force_authenticate(user=user)
        self.user = user

    def test_data(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        self.client.post('{0}?rule=epcis&run-immediately=true'.format(url),
                         {'file': data},
                         format='multipart')

    def test_task_parameters(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?rule=epcis&run-immediately=true&param=abcdef'.format(url),
            {'file': data},
            format='multipart')
        name = response.data
        db_task = models.Task.objects.get(
            name=name
        )
        self.assertEqual(1, db_task.taskparameter_set.count())
        task_param = db_task.taskparameter_set.get(name='param',
                                                   value='abcdef')
        self.assertEqual(db_task, task_param.task)

    def test_epcis(self):
        self._create_rule()
        url = reverse('epcis-capture')
        data = self._get_test_data()
        ret = self.client.post(
            '{0}?rule=epcis&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')

    def test_no_data_epcis(self):
        self._create_rule()
        url = reverse('epcis-capture')
        data = ''
        ret = self.client.post(
            '{0}?rule=epcis&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')

    def test_no_data_capture(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = ''
        self.client.post('{0}?rule=epcis&run-immediately=true'.format(url),
                         {'file': data},
                         format='multipart')

    def test_execute_view(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?rule=epcis&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        self.assertEqual(response.status_code, 500)
        # now try to download the file
        url = reverse('task-data', kwargs={"task_name": task_name})
        response = self.client.get(url)
        test = response.content.decode('utf-8')
        self.assertEqual(test[:3], "<ep")

    def test_execute_view_with_filter(self):
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        rf_2.search_value = 'asdfasdfasdfasdf'
        rf_2.save()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        self.assertEqual(response.status_code, 500)
        # now try to download the file
        url = reverse('task-data', kwargs={"task_name": task_name})
        response = self.client.get(url)
        test = response.content.decode('utf-8')
        self.assertEqual(test[:3], "<ep")

    def test_execute_view_with_filter_1_true(self):
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        rf_2.search_value = 'no findy'
        rf_3.default = False
        rf_3.search_value = 'no findy'
        rf_2.save()
        rf_3.save()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        rules = get_rules_by_filter(filter_name='utf', message=data)
        self.assertIn('epcis', rules, msg='Rule epcis_1 should have been '
                                            'selected.')


    def test_execute_view_with_filter_2_true(self):
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        rf_1.search_value = 'no findy'
        rf_3.default = False
        rf_3.search_value = 'no findy'
        rf_1.save()
        rf_3.save()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        rules = get_rules_by_filter(filter_name='utf', message=data)
        self.assertIn('epcis_2', rules, msg='Rule epcis_1 should have been '
                                            'selected.')

    def test_execute_view_with_default(self):
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        rf_1.search_value = 'no findy'
        rf_2.search_value = 'no findy'
        rf_1.save()
        rf_2.save()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        rules = get_rules_by_filter(filter_name='utf', message=data)
        self.assertIn('epcis_3', rules, msg='Rule epcis_1 should have been '
                                            'selected.')

    def test_execute_view_with_break_on_true(self):
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        rf_1.break_on_true = True
        rf_1.save()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        task_name = response.data
        url = reverse('execute-task', kwargs={"task_name": task_name})
        response = self.client.get(
            '{0}?run-immediately=true'.format(url)
        )
        rules = get_rules_by_filter(filter_name='utf', message=data)
        self.assertEqual(len(rules), 1, "Too many rules were returned.")
        self.assertIn('epcis', rules)

    def test_execute_view_with_return_all(self):
        """
        Returns everything but the default value.
        """
        filter, rf_1, rf_2, rf_3 = self._create_filter()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        response = self.client.post(
            '{0}?filter=utf&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')
        self.assertEqual(response.status_code, 201)
        rules = get_rules_by_filter(filter_name='utf', message=data)
        self.assertEqual(len(rules), 1, "1 rules should be returned.")

    def test_no_rule_capture(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = ''
        self.client.post('{0}?run-immediately=true'.format(url),
                         {'file': data},
                         format='multipart')

    def test_task_api(self):
        self._create_rule()
        url = reverse('epcis-capture')
        data = self._get_test_data()
        ret = self.client.post(
            '{0}?rule=epcis&run-immediately=true'.format(url),
            {'file': data},
            format='multipart')

    def _get_test_data(self):
        '''
        Loads the XML file and passes its data back as a string.
        '''
        curpath = os.path.dirname(__file__)
        data_path = os.path.join(curpath, 'data/epcis.xml')
        with open(data_path) as data_file:
            return data_file.read()

    def test_clone_rule(self):
        rule = self._create_rule()
        self._create_filter(rule)
        new_rule = clone_rule(rule.name, 'new_rule')
        self.assertEqual(new_rule.step_set.count(), 1)
        self.assertEqual(new_rule.ruleparameter_set.count(), 1)
        self.assertEqual(new_rule.rulefilter_set.count(), 0)

    def _create_rule(self, rule_name='epcis'):
        db_rule = models.Rule()
        db_rule.name = rule_name
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

    def _create_filter(self, rule=None):
        rule = rule or self._create_rule()
        rule_2 = self._create_rule('epcis_2')
        rule_3 = self._create_rule('epcis_3')
        filter = models.Filter.objects.create(name='utf',
                                              description='unit testing')
        rule_filter_1 = models.RuleFilter.objects.create(
            filter=filter,
            rule=rule,
            search_value='^<epcis',
            search_type='regex',
            order=1,
            reverse=False
        )
        rule_filter_2 = models.RuleFilter.objects.create(
            filter=filter,
            rule=rule_2,
            search_value='urn:epc:id:sgtin:305555.0555555.5',
            search_type='search',
            order=2,
            reverse=False
        )
        rule_filter_3 = models.RuleFilter.objects.create(
            filter=filter,
            rule=rule_3,
            search_value='',
            search_type='search',
            order=3,
            reverse=False,
            default=True
        )
        return filter, rule_filter_1, rule_filter_2, rule_filter_3
