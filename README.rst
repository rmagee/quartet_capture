--------------
QU4TET CAPTURE
--------------

.. image:: https://gitlab.com/serial-lab/EParseCIS/badges/master/pipeline.svg
        :target: https://gitlab.com/serial-lab/quartet_capture/commits/master

.. image:: https://gitlab.com/serial-lab/EParseCIS/badges/master/coverage.svg
        :target: https://gitlab.com/serial-lab/quartet_capture/pipelines

A capture and queuing interface for QU4RTET.

Documentation
=============

The full documentation here: 

https://serial-lab.gitlab.io/quartet_capture

Quickstart
==========

Install quartet_capture

.. code-block::text

    pip install quartet_capture

Add it to your `INSTALLED_APPS`:

.. code-block::text

    INSTALLED_APPS = (
        ...
        'quartet_capture.apps.QuartetCaptureConfig',
        ...
    )

Add quartet_capture's URL patterns:

.. code-block::text

    from quartet_capture import urls as quartet_capture_urls

    urlpatterns = [
        ...
        url(r'^', include(quartet_capture_urls)),
        ...
    ]

Features
========

* Accepts inbound HTTP Post messages and queues them up for processing.
* Stores inbound messages in RabbitMQ backend.
* Keeps track of messages and their processing state.

Running The Unit Tests
======================

.. code-block::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ python runtests.py

