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

## QUARTET_CAPTURE_MAX_WAIT_CYCLES

How many wait cycles will a task run through before it gives up waiting 
for other tasks to complete.  

Default is 1000

Combined with the default below you have a little less than 
three hours before the task stops.

## QUARTET_CAPTURE_WAIT_CYCLE_INTERVAL

How long should a task wait between cycles before checking if the tasks 
it is waiting on have completed.  This should be an integer in seconds.

Default is 10 seconds.
