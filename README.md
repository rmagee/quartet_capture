QU4TET CAPTURE
==============

[![pipeline status](https://gitlab.com/serial-lab/quartet_capture/badges/master/pipeline.svg)](https://gitlab.com/serial-lab/quartet_capture/commits/master)
[![coverage report](https://gitlab.com/serial-lab/quartet_capture/badges/master/coverage.svg)](https://gitlab.com/serial-lab/quartet_capture/commits/master)

A capture and queuing interface for QU4RTET.

## Documentation

The full documentation [can be found here](https://serial-lab.gitlab.io/quartet_capture).

## Quickstart


Install quartet_capture::

    pip install quartet_capture

Add it to your `INSTALLED_APPS`:


    INSTALLED_APPS = (
        ...
        'quartet_capture.apps.QuartetCaptureConfig',
        ...
    )

Add quartet_capture's URL patterns:

    from quartet_capture import urls as quartet_capture_urls


    urlpatterns = [
        ...
        url(r'^', include(quartet_capture_urls)),
        ...
    ]

## Features

* Accepts inbound HTTP Post messages and queues them up for processing.
* Stores inbound messages in RabbitMQ backend.
* Keeps track of messages and their processing state.

## Running Tests

Does the code actually work?

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ python runtests.py

## Credits


Tools used in rendering this package:

*  Cookiecutter
*  cookiecutter-djangopackage
