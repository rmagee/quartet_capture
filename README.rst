--------------
QU4TET CAPTURE
--------------

.. image:: https://gitlab.com/serial-lab/quartet_capture/badges/master/pipeline.svg
        :target: https://gitlab.com/serial-lab/quartet_capture/commits/master

.. image:: https://gitlab.com/serial-lab/quartet_capture/badges/master/coverage.svg
        :target: https://gitlab.com/serial-lab/quartet_capture/pipelines

.. code-block::text

         .d8888b.      d8888  8888888b. 88888888888 888     888 8888888b.  8888888888
        d88P  Y88b    d8P888  888   Y88b    888     888     888 888   Y88b 888
        888    888   d8P 888  888    888    888     888     888 888    888 888
        888         d8P  888  888   d88P    888     888     888 888   d88P 8888888
        888        d88   888  8888888P"     888     888     888 8888888P"  888
        888    888 8888888888 888           888     888     888 888 T88b   888
        Y88b  d88P       888  888           888     Y88b. .d88P 888  T88b  888
         "Y8888P"        888  888           888      "Y88888P"  888   T88b 8888888888

A capture and queuing interface for QU4RTET.  This package defines the
generic structure of the QU4RTET rule engine and defines the base classes
necessary for use when extending the functionality of QU4RTET.

Documentation
=============

The full documentation here includes an overall explanation and example of
implementing rules and steps along with installation instructions:

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
* Stores inbound messages in RabbitMQ backend for processing with the Celery Task Queue.
* Keeps track of messages and their processing state.

Running The Unit Tests
======================

.. code-block::text

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ python runtests.py

