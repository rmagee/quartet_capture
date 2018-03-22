# EPCIS Rule Configuration
If you are using the QU4RTET-UI app, you can peform all of these steps 
in the application interface.  The instructions below cover how the
configure the system via the API forms or via the API REST interface.

## Prerequisites
You must have the following SerialLab packages installed:
    
* EPCPyYes
* EParseCIS
* quartet_epcis

## Create a Rule

Via the API forms or via a tool, such as SOAP UI or Postman, you will create a 
rule. Below is the javascript you would send to do this.  If you are using 
the API forms you can fill in the same info as below by hand.

    {
        "name": "EPCIS",
        "description": "EPCIS Parsing Rule."
    }
    
## Create the EPCIS Parsing Step
The only essential field here that could cause problems if improperly 
configures would be the `step_class` field.  This field tells the 
rule engine where to find the python module to execute as part of the
parsing step.

    {
        "name": "EPCIS",
        "description": "Executes the EPCIS step within the quartet_epcis package.",
        "step_class": "quartet_epcis.parsing.steps.EPCISParsingStep",
        "order": 1,
        "rule": "EPCIS"
    }

## Call the API
Once you have the rule configured, calling the API is fairly straight forward.
You'll send an HTTP POST to the `/capture/quartet-capture/` resource.

    http[s]://[server_name]:[port]/capture/quartet-capture/?rule=[rule name]
    
Using the rule name supplied in the examples in this document your resource
URL may look something like this, for example:

    http://localhost:8000/capture/quartet-capture/?rule=EPCIS
    
   
