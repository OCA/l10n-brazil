O modulo implementa a parte comum da infra-estrutura necessária para o
uso do CNAB 240 ou 400 localizando o modulo
<https://github.com/OCA/bank-payment/tree/12.0/account_payment_order>
onde o Modo de Pagamento é usado para as configurações especificas de
cada CNAB e a Ordem de Pagamento para o envio de Instruções CNAB, também
é incluído grupos de acesso para permissões de segurança e o registro do
LOG de retorno. Porém a implementação foi pensada para permitir que seja
possível usar diferentes bibliotecas para gerar e tratar o retorno do
CNAB, por isso é preciso instalar um segundo modulo que vai ter essa
função, portanto a ideia é que aqui estará tudo que for comum para a
implementação mas não irá funcionar sem esse segundo modulo.
