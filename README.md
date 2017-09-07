# target-intercom

A [Singer](https://singer.io) target that pushes data to an Intercom account

## How to use it

`target-intercom` works together with any other [Singer Tap] to move data
from sources like a [CSV] to
an Intercom account. It is commonly used for creating/updating users in an
intercom account for filtering and creating segments.

The target uses the bulk user API via [python-intercom](python-intercom)
and therefore creates/updates users according to the Intercom API documentation:

> Users not found via email or user_id will be created, and those that are found will be updated.
> Note that the following lookup order applies when updating users - id then user_id then email, and results in the following logic
> - id is matched - the user_id and email will be updated if they are sent.
> - user_id match - the email will be updated, the id is not updated.
> - email match where no user_id set on the matching user - the user_id will be set to the value sent in the request, the id is not updated.
> - email match where there is a user_id set on the matching user - a new unique record with new id will be created if a new value for user_id is sent in the request.

The target updates the [core user model]. Any additional fields will be created as custom attributes on the Intercom user.

---

[tap-csv]: https://github.com/robertjmoore/tap-csv
[python-intercom]: https://github.com/jkeyes/python-intercom
[intercom-user-model]: https://developers.intercom.com/reference#user-model
