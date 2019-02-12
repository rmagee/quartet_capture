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
from django.contrib import admin
from quartet_capture import models

class RuleFilterInline(admin.StackedInline):
    model = models.RuleFilter
    extra = 0

@admin.register(models.Filter)
class FilterAdmin(admin.ModelAdmin):
    inlines = [
        RuleFilterInline,
    ]
    list_display = ('name', 'description')

@admin.register(models.RuleFilter)
class RuleFilterAdmin(admin.ModelAdmin):
    pass

class StepInline(admin.StackedInline):
    model = models.Step
    extra = 0

@admin.register(models.Rule)
class RuleAdmin(admin.ModelAdmin):
    inlines = [
        StepInline
    ]
    list_display = ('name', 'description')

class StepParameterInline(admin.StackedInline):
    model = models.StepParameter
    extra = 0

@admin.register(models.Step)
class StepAdmin(admin.ModelAdmin):
    inlines = [
        StepParameterInline
    ]
    list_display = ('name', 'rule', 'order', 'description')

class TaskMessageInline(admin.TabularInline):
    model = models.TaskMessage
    extra = 0
    readonly_fields = ('level', 'message', 'created')

class TaskHistoryInline(admin.TabularInline):
    model = models.TaskHistory
    extra = 0

class TaskParameterInline(admin.TabularInline):
    model = models.TaskParameter
    extra = 0
    readonly_fields = ('name', 'value', 'description')

@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [
        TaskParameterInline,
        TaskHistoryInline,
        TaskMessageInline,
    ]
    list_display = ('status_changed', 'name', 'rule', 'status', 'execution_time')
    ordering = ('-status_changed',)

def register_to_site(admin_site):
    admin_site.register(models.RuleFilter, RuleFilterAdmin)
    admin_site.register(models.Filter, FilterAdmin)
    admin_site.register(models.Rule, RuleAdmin)
    admin_site.register(models.Step, StepAdmin)
    admin_site.register(models.Task, TaskAdmin)
