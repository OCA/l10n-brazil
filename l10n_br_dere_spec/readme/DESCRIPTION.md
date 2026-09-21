This module provides abstract Odoo models mapped from the official DeRE
(Declaração de Regimes Específicos) XSD package **1.2.0**, published by
CGIBS/RFB.

It does not generate or transmit declarations. The implementation module
`l10n_br_dere` maps these mixins onto concrete records and talks to
Receita Integra.

Official schemas shipped under `schemas/v1_2_0/` come from:

https://cgibs.gov.br/declaracao-de-regimes-especificos-dere

Wave 1 covers D-1001, D-1011, D-1101, D-1106, D-1121, D-1198, D-1199 and
the official return events D-9001, D-9101, D-9106, D-9112, D-9198 and
D-9199. The D-9121 and D-9209 schemas are shipped so later events can
reuse them. Transactional events (D-3201 and others) remain out of this
first version because their layouts are still preliminary.
