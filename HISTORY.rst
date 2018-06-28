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
