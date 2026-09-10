- Only the credit card is implemented. The Orders API also supports Pix, boleto
  and debit card with 3DS, which are the natural next steps.
- Payments are made in a single installment; PagBank supports installments with
  interest either from the seller or from the buyer.
- Refunds are full only, although PagBank accepts partial cancellations.
- 3DS authentication is not implemented. Without it, the chargeback liability
  stays with the seller.
- The webhook of PagBank (`notification_urls`) is not consumed yet: a charge
  that changes state on the PagBank side (an analysis that ends in approval,
  for instance) is only seen by Odoo on the next request.
- The browser tour that existed in 14.0 was dropped along with the dependency
  on `website_sale`; the flows are covered by unit tests instead.
