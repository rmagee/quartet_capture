=============================
quartet_capture
=============================

.. image:: https://badge.fury.io/py/quartet_capture.svg
    :target: https://badge.fury.io/py/quartet_capture

.. image:: https://travis-ci.org/serial-lab/quartet_capture.svg?branch=master
    :target: https://travis-ci.org/serial-lab/quartet_capture

.. image:: https://codecov.io/gh/serial-lab/quartet_capture/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/serial-lab/quartet_capture

A capture and queuing interface for QU4RTET.

Documentation
-------------

The full documentation is at https://quartet_capture.readthedocs.io.

Quickstart
----------

Install quartet_capture::

    pip install quartet_capture

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'quartet_capture.apps.QuartetCaptureConfig',
        ...
    )

Add quartet_capture's URL patterns:

.. code-block:: python

    from quartet_capture import urls as quartet_capture_urls


    urlpatterns = [
        ...
        url(r'^', include(quartet_capture_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
