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
from quartet_capture import models

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
django.setup()


class ViewTest(APITestCase):
    '''
    Tests the capture API and executes the rule framework.
    '''

    def test_data(self):
        self._create_rule()
        url = reverse('quartet-capture')
        data = self._get_test_data()
        self.client.post('{0}?rule=epcis&run-immediately=true'.format(url),
                         {'file': data},
                         format='multipart')

    def test_epcis(self):
        self._create_rule()
        url = reverse('epcis-capture')
        data = self._get_test_data()
        self.client.post('{0}?rule=epcis&run-immediately=true'.format(url),
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
