Este módulo emite a **NFS-e Nacional** (Nota Fiscal de Serviços eletrônica no
padrão nacional) diretamente no ambiente **Sefin Nacional / ADN** (Ambiente de
Dados Nacional), sem gateway pago e sem passar pelo webservice de cada
prefeitura.

**O que é a NFS-e Nacional.** É o padrão único de NFS-e mantido pelo Governo
Federal e pelos municípios, com leiaute e regras de validação comuns. O
prestador não emite a nota diretamente: ele envia uma **DPS** (Declaração de
Prestação de Serviços) assinada, e o ADN valida, autoriza e devolve a NFS-e com
sua chave de acesso de 50 dígitos. Os municípios conveniados ao padrão nacional
usam esse mesmo ambiente.

**O que o módulo faz.** A partir de um `l10n_br_fiscal.document` de serviço
(modelo `SE`) confirmado:

- monta a **DPS** (versão 1.00 do leiaute) e valida contra o XSD oficial;
- assina a DPS com o **certificado A1** (ICP-Brasil) da empresa;
- envia ao ADN por **REST com mTLS** e grava a NFS-e autorizada, a chave de
  acesso de 50 dígitos, o número e o protocolo;
- trata a rejeição do ADN, mostrando o motivo legível no chatter e no evento do
  documento;
- **cancela** a NFS-e pelo evento `101101`, com o código do motivo escolhido no
  assistente de cancelamento;
- **consulta** no ADN se a nota foi cancelada fora do Odoo (eventos `101101` e
  `305101`);
- gera o **DANFSe** em PDF a partir do XML autorizado (layout v2.0 da NT
  008/2026), sem consultar nenhum portal;
- **importa** o XML de uma NFS-e Nacional ou de uma DPS para um documento fiscal.

**Como se encaixa.** Depende de `l10n_br_nfse`, de onde vêm o campo de provedor
e o de ambiente da NFS-e, mas mapeia a DPS direto sobre o
`l10n_br_fiscal.document`: os campos de serviço e de impostos já estão no núcleo
fiscal, então nada do fluxo municipal (RPS, ABRASF) é reaproveitado. O leiaute
vem do módulo `l10n_br_nfse_spec` (mixins xsdata-odoo sobre os schemas
oficiais), ligado ao documento pelo `spec_driven_model`. Ao escolher o provedor
**Sefin Nacional (ADN)** na empresa, os documentos de serviço dela passam por
este módulo, e os módulos municipais e de gateway continuam atendendo as demais
empresas.
