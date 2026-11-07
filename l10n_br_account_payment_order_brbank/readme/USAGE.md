1. Set up the bank connection (Accounting > Configuration > Bank Connections), with
   the credentials of the bank API application and the certificate the bank asks
   for. The **Payment Settings** page lists the keys of the payment API of that bank;
   the document of the holder, the company name and, at Bradesco, the debit account
   come from the company and the journal.
2. Create an outbound payment mode with **Bank API Provider** set to brbank and the
   bank connection (and, at Banco do Brasil, the payment contract and the kind of
   payments). Its bank journal must have the company bank account with branch and
   account digit.
3. Use payment orders of this mode as usual, then **Send to Bank**. Odoo checks the
   bank every 10 minutes, or at once with **Check Bank Now**.
