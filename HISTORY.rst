.. :changelog:

History
-------

0.1.0 (2018-02-13)
++++++++++++++++++

* First release on PyPI.

0.2.2
++++++++++++++++++
Fixed unique issue with step order and removed name as primary
key for rules.  Fixes issues with rules getting accidentally
created and steps having to have unique order across all steps.

1.0.0 to 1.0.12
+++++++++++++++
Updated continuous integration builds for official 1.0 launch in PyPI.
Added a default on_failure handler to the base `quartet_capture.rules.Step`
base class.
Improved rule context handling for steps.  The RuleContext class was
added instead of using a dictionary, the context is now a first-class citizen
in the step/rule framework.

1.0.13 to 1.0.18
++++++++++++++++
Added a new dependency for the unit tests supporting the `quartet_epcis`
module.  Also fixed an exception test in the unit tests.

Added the ability to send multiple string arguments to the TaskMessaging
mixin helpers using commas instead of having to manually concatenate. Similar
to python logging calls.

Some patches were to get the readme file to display correctly in PyPI.

Added sorting for steps.  Sorting was not being handled by the order parameter.

Added a `get_boolean_parameter` helper function to the base `rules.Step`
class.

1.1 to 1.2
++++++++++
Views now support DjangoModelAuthorization via sentinal querysets.  Model
ViewSets are unchanged.

Updated unit tests to use authorization.

Added convenience management command to create default capture group.

Fixed encoding issue with saving certain types of tasks.

1.3
+++
Added support for saving raw byte data in the task engine.

Modified the rule view to use the global task creation function in tasks.py.

Created a mechanism for request.GET variables to be passed to the rule engine
as task parameters.  The `Step` base-class now has a new helper function to
get any task parameters `quartet_capture.Rules.Step.get_task_parameters`.

Removed parent-level transaction scope from rule engine.  This allows steps
to declare and control their own transaction scopes explicitly.

`quartet_capture.rules.Step` classes now have an internal reference to
the database step model used to instantiate each Step instance
in the `db_step` property.

Changed the length of the class path for steps in the step model to 500 chars.
