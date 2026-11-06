- Only the immediate charge (`cob`) is implemented. The API also offers the
  charge with a due date (`cobv`), with interest, fine and discount, which is
  the natural next step for the integration with the payment orders.
- Pix Automático (`rec`, `solicrec` and `cobr`, introduced in version 2.7 of
  the API) is not implemented: recurring payments still need a new charge each
  time.
- Refunds (`PUT /pix/{e2eid}/devolucao/{id}`) are not implemented.
- The webhook is not registered automatically: it must be declared once with
  `PUT /webhook/{chave}` on the PSP. The notification is not trusted as is, the
  charge is always queried again on the PSP.
- Adding another PSP means adding an entry to `PSP_CONFIG` with its URLs and
  the way it authenticates, not a new module.
