=====
Usage
=====

To use quartet_capture in a project, add it to your `INSTALLED_APPS`:

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
