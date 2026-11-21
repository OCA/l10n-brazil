This module integrates the MDF-e, from the Brazilian Localization, with the
vehicle registry of the `l10n_br_delivery <https://github.com/OCA/l10n-brazil/tree/16.0/l10n_br_delivery>`_
module.

It adds a vehicle field on the MDF-e document, so the road modal vehicle data
(plate, RENAVAM, tara, capacities, wheel and body type and the vehicle state)
can be selected from the vehicles registered in **l10n_br_delivery** instead of
being typed by hand.

It also adds the list of vehicles owned by a partner in the MDF-e tab of the
partner form, which makes it easier to register the vehicle owner.

This is a glue module: **l10n_br_mdfe** does not depend on **l10n_br_delivery**,
so the MDF-e can still be installed without the delivery localization and its
long dependency chain.
