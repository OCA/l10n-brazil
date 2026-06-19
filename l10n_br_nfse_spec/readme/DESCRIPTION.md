Módulo de especificação NFS-e Nacional (DPS v1.0) — fornece os modelos Odoo abstratos
gerados pelo ``xsdata-odoo`` a partir do schema XSD oficial do DPS (Documento de Prestação
de Serviços) publicado pela SEFIN para o padrão nacional de NFS-e.

Este módulo não realiza integração com nenhum serviço externo. Ele constitui a camada de
dados utilizada pelos módulos de integração, como o ``l10n_br_nfse_nacional``:

- Modelos Odoo abstratos com campos prefixados ``nfse10_``, gerados a partir do XSD
  oficial do DPS v1.0. Seguem o mesmo padrão do ``l10n_br_nfe_spec`` (campos ``nfe40_``).
- ``NfseSpecMixin`` — modelo abstrato base do qual todos os modelos ``nfse.10.*`` herdam,
  registrando as referências de binding e de módulo Odoo para o framework
  ``spec_driven_model``.
- ``DpsBuilder`` — converte um registro ``l10n_br_fiscal.document`` em um payload JSON DPS
  pronto para envio à API SEFIN, delegando para os métodos padrão do ``l10n_br_nfse``
  e utilizando o ``xsdata JsonSerializer`` para serialização.
- ``NfseResponse`` — dataclass para leitura segura e normalizada das respostas de
  autorização da SEFIN.

Módulos relacionados:

- ``l10n_br_nfse`` — módulo base de NFS-e municipal; este módulo reutiliza seus métodos
  de preparação de dados (``_prepare_lote_rps``, ``_prepare_dados_servico``).
- ``l10n_br_nfse_nacional`` — módulo de integração com a API REST da SEFIN que depende
  deste módulo.
- ``spec_driven_model`` — framework OCA para importação e exportação de documentos fiscais
  via modelos abstratos gerados por xsdata.
