In the form view of the **Payment Transaction**, the boleto and Pix fields show
when the transaction is a boleto payment.

When a charge is paid, the payment is reconciled with its installment only, so
paying out of order does not settle another installment. Generating the charges
again skips the installments with a live one (draft, pending, authorized or
done); an installment whose charge failed or was canceled gets a new one.

Provider modules reuse the actions of the payment transaction with another
meaning:

- **Capture** queries the status of the charge in the bank. Nothing is captured.
- **Void** and **Refund** ask the bank to write the charge off. A charge already
  paid is not refunded by the bank: the money goes back outside the boleto.
