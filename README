# uberphone

This module allows one to generate a dynamic list of phone numbers for
escalation in the event that a department's desk phone is not answered. This
also allows for departments which do not have a physical presence to direct
phone calls to whomever is currently working desginated shifts. An arbitrary
number of fallback sequences may be specified, each with any number of shifts,
persons, and specific phone numbers to be called.


# Example

The example configuration below specifies that, if TechOps does not answer their
phone, to call the cell phone of anyone working a desk staff shift. If they do
not answer, the manager on duty will be called. If they do not answer,
department heads and a static phone number will be called simultaneously. Note
that `shifts`, `people`, and `numbers` may all be used in the same escalation
step, and each step will be dialed simultaneously. Also, when an attendee is
specified by name, they will only be included if they are volunteering or
staffing.

```
{
    "uber": {
        "base_url": "https://staging4.uber.magfest.org/uber/jsonrpc",
        "token": "changeme"
    },
    "depts": {
        "Tech Ops": {
            "escalation": [
                {"shifts": ["Desk Staff"]},
                {"shifts": ["Manager Shift"]},
                {"people": ["Robert Scullin", "Ian McCombs"], "numbers": ["3015551234"]}
            ]
        }
    }
}
```
