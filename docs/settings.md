# Settings

All quartet_capture settings begin with *QUARTET_CAPTURE_* and can be overriden
in your project's settings.py file.  Here the default settings and each 
setting's description are noted.

## QUARTET_CAPTURE_BROKER

#### Default Value:
    
    'pyamqp://guest@localhost//'
    
#### Description

The broker URL for celery.  The default assumes a *RabbitMQ*
backend, but any broker compatible with Celery can be used.


