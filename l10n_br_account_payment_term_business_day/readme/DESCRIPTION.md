Brazilian taxes are not due on a day the banks do not settle, and the rule differs per
tax: some anticipate to the previous banking business day, others postpone to the next
one. Getting it wrong costs a fine.

This module adds that direction to the payment term, so the due date already comes out
right instead of being corrected by hand on every entry.

The calendar comes from `l10n_br_resource`, which stacks country, state and municipality
holidays, so a municipal decree that closes the banks in one city is enough to move an
ISS due date there and nowhere else.
