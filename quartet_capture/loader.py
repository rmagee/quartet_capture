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

from quartet_capture.models import Rule, Step


def load_data():
    '''
    Use this utility at the command line to load the default step
    included in this package.
    :return: None.
    '''
    rule = Rule.objects.create(
        name='EPCIS Parsing Rule',
        description='Default EPCIS 1.2 Parsing Rule')
    rule.save()
    step = Step.objects.create(
        rule=rule,
        name='QU4RTET EPCIS Parsing',
        description='Parse EPCIS data and save in backend database.',
        step_class='quartet_epcis.parsing.steps.EPCISParsingStep',
        order=1
    )
    step.save()
