Esta entrega para na geração da guia. A transmissão ao webservice virá depois,
fora do addon, em duas camadas: `nfelib/gnre/` com os bindings e os endpoints, e
`erpbrasil.edoc.gnre` com a orquestração, seguindo o par que já existe para
MDF-e.

Fora do escopo por decisão consciente:

- apuração de ICMS-ST, com saldo credor anterior, devoluções e ajustes. No SPED,
  apuração (E200 e E210) e obrigação a recolher (E250) são registros distintos, e
  a GNRE por documento não passa por apuração nenhuma;
- modelo genérico de obrigação servindo DARF, DAS e GARE. A promoção deve
  acontecer por extração de mixin quando existir um segundo consumidor real;
- cadastro completo dos códigos de receita das 27 UFs, que é dado e entra por
  contribuição.
