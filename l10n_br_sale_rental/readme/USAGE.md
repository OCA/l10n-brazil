1. No pedido de venda, adicione o serviço de aluguel com quantidade, data de
   início e de fim (como no `sale_rental`). A linha recebe a operação
   "Locação de bens móveis".
2. Ao confirmar, o pedido gera a transferência de remessa e a de retorno
   (aguardando). Valide a remessa na retirada e use *Criar Fatura* na
   transferência para emitir a NF-e de remessa (5908/6908).
3. Na devolução, valide a transferência de retorno e emita a NF-e de entrada
   (1909/2909) da mesma forma, quando o locatário não for contribuinte de ICMS.
4. Fature o aluguel pelo pedido: a fatura sai em NFS-e, com a operação de
   locação.
