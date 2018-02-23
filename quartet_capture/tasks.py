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
from __future__ import absolute_import, unicode_literals
from logging import getLogger
from celery import shared_task
from quartet_capture.models import Rule as DBRule
from quartet_capture.rules import Rule

logger = getLogger('quartet_capture')

@shared_task(name='execute_rule')
def execute_rule(message: str, rule_name: str):
    '''
    When a message arrives, creates a record of the message and parses
    it using the appropriate parser.
    :param message_data: The data to be handled.
    '''
    # get the rule from the database
    print('executing task')
    db_rule = DBRule.objects.get(name=rule_name)
    # create a rule instance with the db rule
    c_rule = Rule(db_rule)
    # execute the rule
    c_rule.execute(message)


