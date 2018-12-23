# Filters and Rule Filters

The capture module gives you the ability to search inbound messages and
execute a give rule or group of rules based on the search value.  For example,
on an inbound message you can define a *Rule Filter* that searches a message
for the word *shipping* and then execute a rule named *Handle Shipping*.

In short, you can:

1. Dynamically execute different rules based on inbound values.
2. Dynamically execute more than one rule.
3. Execute a default rule if your inbound search values are not found.

## Setting Up Filters

A rule filter has the following components:

1. A parent database rule `Filter` record
2. One or more child `RuleFilter` records that specify a Rule, a search term and a 
search type.

## Example

#### Filter

The following example configuration shows how you can set up filters to 
route messages to rules based on search values in inbound data.  Keep in mind,
you can execute 1 or more rules based on the *Rule Filters* you set up.

In the example below, different rules are returned if different GLN values
are found in the inbound message.  In addition, if no GLN values are found,
then a default rule is returned.

* **Name** Shipping Filter
* **Description** Looks for the specific GLN values in inbound messages and
sends the inbound data to a specific rule if there is a match.  If no match,
processes EPCIS with standard EPCIS rule.

#### Rule Filter One

This rule filter will return the rule *EPCIS Outbound Trading Partner 1* if
it finds the GLN *0355550000018* in an inbound message. If the GLN value
is found, the logic to keep searching against subsequent *Rule Filters* will
be bypassed and this will be the only *Rule Filter* that returns a match.
This is because the **Break on True** flag has been set on the *Rule Filter*.

* **Filter** Shipping Filter
* **Rule** EPCIS Outbound Trading Partner 1
* **Search Value** 0355550000018
* **Search Type** search 
* **Break on True** True
* **Order** 1

#### Rule Filter Two

This rule filter will return the rule *EPCIS Outbound Trading Partner 2* if
it finds the GLN *0355550000025* in an inbound message.  

* **Filter** Shipping Filter
* **Rule** EPCIS Outbound Trading Partner 2
* **Search Value** 0355550000025
* **Search Type** search
* **Order** 2

#### Rule Filter Three (Default)

If the prior two *Rule Filters* do not find a match the rule *EPCIS* will be 
returned since it is has its default flag set to true.

* **Filter** Shipping Filter
* **Default** True 
* **Rule** EPCIS
* **Search Value** epcis
* **Search Type** search
* **Order** 3

