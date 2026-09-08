*(summary: extends the delivery module to comply with the fiscal
documents requirements)*

Esse módulo localiza o módulo *delivery* para adequar as necessidades do
Brasil. Em especial ele:

> - acrescenta informações para os Documentos Fiscais: Transportadora,
>   responsabilidade do frete, volume e peso bruto.
> - acrescenta na Transportadora o código ANTT e a lista de veículos.
> - cria um modelo simples de veículo com os campos fiscais (placa,
>   código ANTT, modelo, ano de fabricação...)
> - desativa o método *\_add_delivery_cost_to_so* da Expedição, pois o
>   frete já esta corretamente informado no pedido.
> - vale a pena notar que o rateamento do frete, seguro e outros custos
>   já esta sendo feito pelo módulo l10n_br_fiscal, tanto para notas de
>   saída como de entrada.
> - se você for emitir NF-e, você precisa do módulo
>   *l10n_br_delivery_nfe* que faz a integração deste módulo com o
>   módulo *l10n_br_nfe*.
