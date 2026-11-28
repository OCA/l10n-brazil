1. On the sale order, *Add shipping* lists the Melhor Envio services with their
   prices; pick one.
2. On the delivery, *Buy Melhor Envio Label* buys the label and *Print Melhor Envio
   Label* opens it. If a step fails after the cart entry is created (for instance
   when the wallet has no balance), the delivery keeps the Melhor Envio order and the
   same button resumes it; the order status is read at Melhor Envio first, so a paid
   label is never paid again.
3. The scheduled action of `delivery_state` updates the status and the tracking code.
   *Cancel* on the delivery cancels the label at Melhor Envio.
