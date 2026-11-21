1. At the Melhor Envio panel (sandbox or production), create an application under
   *Integrações > Área Dev.* with the redirect URL
   `https://<your odoo>/melhorenvio/oauth/callback`.
2. In *Inventory > Configuration > Delivery > Melhor Envio Accounts* (administrators
   only), create an account with the environment, the technical contact e-mail, the
   Client ID and the Secret, then click *Authorize at Melhor Envio*. A token generated
   at the Melhor Envio panel can be pasted in *Access Token* instead.
3. Click *Synchronize Services*: one delivery method is created per service. Archive
   the services you do not offer and set the box dimensions on the ones you keep.

The quotation uses the weight of the products of the order (at least 50 g) and the
ZIP code of the warehouse address as origin. The label needs the street, the city,
the ZIP code and the CPF or CNPJ of the warehouse and of the customer.
