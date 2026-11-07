Glue between the DDA inbox (`l10n_br_dda`) and the Brazilian payment schedule
(`l10n_br_payment_schedule`): the DDA boleto linked to a vendor bill becomes the
instrument of its payable item, so the item no longer waits for somebody to type
or scan the barcode.

- When a boleto is linked to a payable item, its barcode fills the item, if
  the item has none. An item that already has another barcode keeps it, and the
  divergence shows on the schedule and on the boleto. A boleto that settles
  several installments fills the first one, through which `l10n_br_dda` pays
  the amount of the boleto; the other installments show the boleto and stay
  out of the payment orders.
- When the link is undone, or the boleto is cancelled by the beneficiary,
  ignored, refused or paid elsewhere, the barcode written by this module is
  removed; a barcode typed by the user stays.
- The schedule shows the DDA boleto of each item, and the boleto shows the
  schedule status of its payable items and warns when its amount differs from
  the open amount of the item.
