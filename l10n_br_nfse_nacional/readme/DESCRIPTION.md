Integração direta com a API REST da SEFIN (Secretaria de Finanças Nacional) para
emissão, consulta e cancelamento de Notas Fiscais de Serviços Eletrônicas no Padrão
Nacional (NFS-e Nacional), sem dependência de prestadores intermediários.

Principais funcionalidades:

- Emissão de NFS-e Nacional via API REST da SEFIN com autenticação por certificado
  digital (mTLS)
- Consulta automática de status via ação agendada (cron)
- Cancelamento de NFS-e Nacional com justificativa
- Substituição de NFS-e Nacional (nota de substituição)
- DANFSE Nacional — gerado localmente pela biblioteca `brazilfiscalreport` a partir do
  XML autorizado pela SEFIN; opcionalmente baixado do serviço oficial SEFIN quando
  disponível
- Suporte ao regime fiscal MEI (Microempreendedor Individual)
- Retenção de tributos federais: PIS/COFINS, CSLL, IRRF, INSS
- Ambientes de Homologação e Produção configuráveis por empresa

O módulo implementa a estrutura DPS (Documento de Prestação de Serviços) definida pelo
Padrão Nacional NFS-e e se comunica com três serviços distintos:

- SEFIN Nacional — emissão, consulta e cancelamento de DPS
- ADN (Ambiente de Distribuição de NFS-e) — download do XML da NFS-e autorizada
- DANFSE — serviço opcional de download do PDF autorizado diretamente da SEFIN

Módulos relacionados:

- ``l10n_br_nfse`` — módulo base de NFS-e municipal; este módulo estende seu
  comportamento para o padrão nacional.
- ``l10n_br_nfse_spec`` — módulo de especificação DPS v1.0; é dependência direta
  deste módulo.
