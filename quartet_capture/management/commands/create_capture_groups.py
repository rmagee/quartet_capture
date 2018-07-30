# This program is free software: you can redistribute it and/| modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, |
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY | FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.utils.translation import gettext as _


class Command(BaseCommand):
    help = _('Creates the default Capture Access Group.')

    def handle(self, *args, **options):
        print(_('Creating group "Capture Access"...'))
        group, created = Group.objects.get_or_create(
            name='Capture Access'
        )
        if created:
            permissions = Permission.objects.filter(
                Q(codename__endswith='_rule') |
                Q(codename__endswith='_ruleparameter') |
                Q(codename__endswith='_step') |
                Q(codename__endswith='_stepparameter') |
                Q(codename__endswith='_task') |
                Q(codename__endswith='_taskparameter') |
                Q(codename__endswith='_taskhistory') |
                Q(codename__endswith='_taskmessage')
            )
            group.permissions.set(permissions)
            group.save()
            print(_('Group created successfully.'))
        else:
            print(_('Group already exists.'))

