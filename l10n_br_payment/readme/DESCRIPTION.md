Base for boleto and Pix charges issued through payment providers. It defines the
fields every provider fills and shows them to the customer; the providers are
other modules.

- The payment transaction carries the boleto data (due date, nosso numero,
  digitable line, bar code, PDF, penalty, interest, instructions) and the Pix
  data (copy and paste, TXID).
- Each charge pays one installment of the invoice (field **Installment**).
- The invoice PDF and the customer portal list the open charges with the
  digitable line and the Pix copy and paste (with its QR code).
