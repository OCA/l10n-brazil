This is a **Brazilian localization** module (it depends on
`l10n_br_sale_stock` and writes the fiscal fields of `l10n_br_fiscal`).
It makes loyalty/coupon **discount** rewards reach the Brazilian invoice
as a fiscal discount (`discount_value` / `vDesc`) on the delivered
product lines, instead of a separate reward line.

The folding is Brazil-specific on purpose: on an NF-e a discount must be
the item's `vDesc`, not a negative product line, so the generic reward
line cannot simply be invoiced as-is.

It matters when the company invoices from the delivery
(`Sale Invoicing Policy = Stock Picking`, from
`sale_stock_picking_invoicing`). A discount reward is a service line
with no stock move, so the picking-based invoice drops it: the invoice
keeps the full price while the customer paid the discounted total, and
the invoice stays *partially paid*. A negative reward line would also
not be a valid NF-e item.

The reward amount is folded into `discount_value` of the product lines
it applies to (respecting the reward `discount_applicability` through
`sale_loyalty_order_line_link`), prorated by the invoiced amount with
the rounding remainder on the last line, and composes with the discount
already prorated for kit components. The reward line is then considered
invoiced so the order does not emit the discount again as a second
document.

A hook (`sale.order.line._loyalty_reward_fiscal_fold`) lets other
modules fold further reward types; `l10n_br_sale_loyalty_delivery` uses
it for the free-shipping reward (`freight_value` / `vFrete`).
