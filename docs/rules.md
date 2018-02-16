# Rule Framework

## Intro
The `quartet_capture.rules` module contains the framework for a simple, rule-based
engine that can execute a series of python modules in order while maintaining
an overall context throughout the process.  

This basic rule engine is in place to allow developers to associate inbound
messages with rules- thereby granting the ability to process different types
of messages different ways by associating messages with rules.

When a message is processed through the Rules framework, the following things
happen:

1. A message is passed into the Rule framework with a `rule_name` parameter
that identifies a configured rule in the database.
2. The Rule framework pulls the `models.Rule` data from the database.
3. A `rules.Rule` instance is created and the database model instance is 
passed to it.
4. The `rules.Rule` instance loads any `models.RuleParameter`s into it's 
context.
5. The `rules.Rule` instance loads any `models.Step` instances associated
with the rule into memory and tries to dynamically instantiate python
class instances defined in the `models.Step.step_class` field.
6. Each loaded `rules.Step` instance is loaded into the `rules.Rule.steps`
dictionary.  Any `models.RuleParameters` are loaded into a dictionary and
passed into the `rules.Step` initializer as a dictionary.
7. The `rules.Rule.execute` method is called which causes the rule
to loop through each step in the steps dictionary and execute each step by
calling the `rules.Step.execute` instance method on each.

## What is a Rule?
> Before we start, to avoid any confusion, let's make it clear that
there are two types of Rule classes:
>* `quartet_capture.models.Rule` - used to store info about rules in the database
>* `quartet_capture.rules.Rule` - classes that use info from models.Rule to execute business
logic.

The rule database model stores all data necessary to instantiate a 
`rules.Rule` instance at runtime.  In addition, it maintains additional
database relationships to `models.RuleParameter`s and `models.Step`s
that are also important to the functioning of the Rule framework.

The `rules.Rule` class is initialized by passing in a `models.Rule`

## Example

First we start by creating a database model instance for our new Rule.

### Creating a Rule Database Model

For now, we will be dealing with the Django database model 
`models.Rule` class, creating an instance
of it and saving some data to the database.

```python
# create a new rule and give it a test parameter
from quartet_capture import models

db_rule = models.Rule()
db_rule.name = 'epcis'
db_rule.description = 'EPCIS Parsing rule utilizing quartet_epcis.'
# save the rule to the database
db_rule.save()
# here we create a parameter.  This parameter will later become
# part of the rules.Rule.context dictionary that will be passed along
# to every Step in the Rule.
rp = models.RuleParameter(name='test name', value='test value',
                          rule=db_rule)
# save the rule to the database
rp.save()
```

So above, we create a database `Rule` model and a parameter for the rule. We
also save both to the database which stores the configuration for later use.   

>NOTE: When a Rule configuration is later used during exection in the rule
engine- the parameters for a given Rule are passed into the 
rules.Rule instances and are used in the context dictionary which is 
passed to every step in a given rule.Rule instance.

### Create a Step Configuration for our Rule Model

Here we create a new Step model instance and save it to the database.  Our
example Rule will only have on Step in it.  However, take special note of
the `order` field.  This field is responsible for telling the Rule framework
in what order all of the given steps for a rule will execute.  The `order`
field is used to sort the steps before execution when they are loaded into
memory as `rules.Step` instance.

***

> #### Super Important NOTE!
>When you define the `step_class` property for a `models.Step` instance,
you must make sure the class path is complete and that it's parent package
is on the PYTHONPATH- otherwise it will not load.

***

```python
# create a new step
epcis_step = models.Step()
epcis_step.name = 'parse-epcis'
epcis_step.description = 'Parse the EPCIS data and store in database.'
epcis_step.order = 1
epcis_step.step_class = 'quartet_epcis.parsing.steps.EPCISParsingStep'
epcis_step.rule = db_rule
epcis_step.save()
```

> Above we used the `quartet_capture.rules.Step` implementation defined 
in the `quartet_epcis.parsing.steps` module as an example.  The
`quartet_capture.rules.Step` is an abstract base class that is meant
to be implemented by developers to customize rule processing.  More on 
this later.


    
