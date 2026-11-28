A transmissão usa o cliente da GNRE da nfelib (akretion/nfelib#157), instalado
pelo git até ser publicado no PyPI. O envelope segue o WSDL do portal e foi
validado no portal de homologação: lote recebido, processado e guia devolvida em
PDF, para o DIFAL do RJ (receita 100102).

Fora do escopo por decisão consciente:

- apuração de ICMS-ST, com saldo credor anterior, devoluções e ajustes. No SPED,
  apuração (E200 e E210) e obrigação a recolher (E250) são registros distintos, e
  a GNRE por documento não passa por apuração nenhuma;
- modelo genérico de obrigação servindo DARF, DAS e GARE. A promoção deve
  acontecer por extração de mixin quando existir um segundo consumidor real;
- cadastro completo dos códigos de receita das 27 UFs, que é dado e entra por
  contribuição.

Próximos passos:

- detalhamento da receita e produto escolhidos a partir da lista que a consulta
  de configurações da UF devolve;
- os valores de multa, juros e atualização monetária no item;
- trocar a serialização em lxml pelo `StackedModel` sobre os mixins `gnre20_`,
  agora que os bindings estão na nfelib.
