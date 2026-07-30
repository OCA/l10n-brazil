Este módulo permite transmitir documentos fiscais eletrônicos (NF-e,
NFC-e, etc.) à SEFAZ de forma assíncrona, através do `queue_job`.

Sem ele, a transmissão à SEFAZ ocorre na mesma transação da ação do
usuário: a requisição fica bloqueada durante todo o ida e volta com o
webservice da SEFAZ, que pode levar de alguns segundos a mais de um
minuto em picos ou indisponibilidade do órgão. Isso prende um worker
HTTP e degrada a resposta para todos os usuários.

Com este módulo, a operação fiscal pode ser configurada para enfileirar
a transmissão: a ação do usuário retorna imediatamente e o envio à SEFAZ
roda em um worker do `queue_job`, fora do caminho da requisição.
