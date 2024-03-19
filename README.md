
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/l10n-brazil&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/l10n-brazil/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/l10n-brazil/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/l10n-brazil/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/l10n-brazil/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/l10n-brazil/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/l10n-brazil)
[![Translation Status](https://translation.odoo-community.org/widgets/l10n-brazil-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/l10n-brazil-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Odoo Brazilian Localization / Localização brasileira do Odoo

Documentos fiscais, impostos brasileiros, notas fiscais, integrações bancárias... Você pode começar com o módulo `l10n_br_base` apenas. Se você precisa da parte fiscal ou de notas fiscais eletrônicas, o próximo módulo que você deve considerar é o módulo `l10n_br_fiscal`... Você pode testar a localização no Runboat com o botão "try me" (admin/admin) e eventualmente selecionar a empresa demo do Simples ou do Lucro Presumido.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[l10n_br_account](l10n_br_account/) | 14.0.10.4.2 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Brazilian Localization Account
[l10n_br_account_due_list](l10n_br_account_due_list/) | 14.0.2.0.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Brazilian Account Due List
[l10n_br_account_nfe](l10n_br_account_nfe/) | 14.0.3.1.0 | [![antoniospneto](https://github.com/antoniospneto.png?size=30px)](https://github.com/antoniospneto) [![felipemotter](https://github.com/felipemotter.png?size=30px)](https://github.com/felipemotter) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Integration between l10n_br_account and l10n_br_nfe
[l10n_br_account_payment_brcobranca](l10n_br_account_payment_brcobranca/) | 14.0.5.1.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | L10n Br Account Payment BRCobranca
[l10n_br_account_payment_order](l10n_br_account_payment_order/) | 14.0.5.1.0 | [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Brazilian Payment Order
[l10n_br_base](l10n_br_base/) | 14.0.3.13.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Customization of base module for implementations in Brazil.
[l10n_br_cnab_structure](l10n_br_cnab_structure/) | 14.0.1.1.0 | [![antoniospneto](https://github.com/antoniospneto.png?size=30px)](https://github.com/antoniospneto) [![felipemotter](https://github.com/felipemotter.png?size=30px)](https://github.com/felipemotter) | This module allows defining the structure for generating the CNAB file. Used to exchange information with Brazilian banks.
[l10n_br_cnpj_search](l10n_br_cnpj_search/) | 14.0.1.5.2 |  | Integração com os Webservices da ReceitaWS e SerPro
[l10n_br_coa](l10n_br_coa/) | 14.0.3.5.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Base do Planos de Contas brasileiros
[l10n_br_coa_generic](l10n_br_coa_generic/) | 14.0.3.4.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Plano de Contas para empresas do Regime normal (Micro e pequenas empresas)
[l10n_br_coa_simple](l10n_br_coa_simple/) | 14.0.3.1.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Plano de Contas ITG 1000 para Microempresas e Empresa de Pequeno Porte
[l10n_br_contract](l10n_br_contract/) | 14.0.2.3.3 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Customization of Contract module for implementations in Brazil.
[l10n_br_crm](l10n_br_crm/) | 14.0.1.3.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Brazilian Localization CRM
[l10n_br_cte_spec](l10n_br_cte_spec/) | 14.0.1.0.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | CT-e spec
[l10n_br_currency_rate_update](l10n_br_currency_rate_update/) | 14.0.1.0.2 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Update exchange rates using OCA modules for Brazil
[l10n_br_delivery](l10n_br_delivery/) | 14.0.2.0.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | delivery module Brazilian Localization
[l10n_br_delivery_nfe](l10n_br_delivery_nfe/) | 14.0.1.1.0 | [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Brazilian Localization Delivery NFe
[l10n_br_fiscal](l10n_br_fiscal/) | 14.0.21.5.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian fiscal core module.
[l10n_br_fiscal_certificate](l10n_br_fiscal_certificate/) | 14.0.1.3.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | A1 fiscal certificate management for Brazil
[l10n_br_fiscal_closing](l10n_br_fiscal_closing/) | 14.0.1.3.0 |  | Fechamento fiscal do periodo
[l10n_br_fiscal_dfe](l10n_br_fiscal_dfe/) | 14.0.2.3.0 |  | Distribuição de documentos fiscais
[l10n_br_hr](l10n_br_hr/) | 14.0.1.5.0 |  | Brazilian Localization HR
[l10n_br_ie_search](l10n_br_ie_search/) | 14.0.1.2.0 |  | Integração com a API SintegraWS e SEFAZ
[l10n_br_mdfe_spec](l10n_br_mdfe_spec/) | 14.0.1.0.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | CT-e spec
[l10n_br_mis_report](l10n_br_mis_report/) | 14.0.1.0.1 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) | Templates de relatórios contábeis brasileiros: Balanço Patrimonial e DRE
[l10n_br_nfe](l10n_br_nfe/) | 14.0.14.2.1 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian Eletronic Invoice NF-e
[l10n_br_nfe_spec](l10n_br_nfe_spec/) | 14.0.6.1.0 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | nfe spec
[l10n_br_nfse](l10n_br_nfse/) | 14.0.1.17.0 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | NFS-e
[l10n_br_nfse_barueri](l10n_br_nfse_barueri/) | 14.0.1.0.1 | [![AndreMarcos](https://github.com/AndreMarcos.png?size=30px)](https://github.com/AndreMarcos) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![ygcarvalh](https://github.com/ygcarvalh.png?size=30px)](https://github.com/ygcarvalh) | NFS-e (Barueri)
[l10n_br_nfse_focus](l10n_br_nfse_focus/) | 14.0.1.0.1 | [![AndreMarcos](https://github.com/AndreMarcos.png?size=30px)](https://github.com/AndreMarcos) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![ygcarvalh](https://github.com/ygcarvalh.png?size=30px)](https://github.com/ygcarvalh) [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | NFS-e (FocusNFE)
[l10n_br_nfse_ginfes](l10n_br_nfse_ginfes/) | 14.0.1.1.0 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) | NFS-e (Ginfes)
[l10n_br_nfse_paulistana](l10n_br_nfse_paulistana/) | 14.0.1.1.6 | [![gabrielcardoso21](https://github.com/gabrielcardoso21.png?size=30px)](https://github.com/gabrielcardoso21) [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) | NFS-e (Nota Paulistana)
[l10n_br_portal](l10n_br_portal/) | 14.0.2.0.1 |  | Campos Brasileiros no Portal
[l10n_br_pos](l10n_br_pos/) | 14.0.1.5.2 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![lfdivino](https://github.com/lfdivino.png?size=30px)](https://github.com/lfdivino) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) [![ygcarvalh](https://github.com/ygcarvalh.png?size=30px)](https://github.com/ygcarvalh) | Ponto de venda adaptado a legislação Brasileira
[l10n_br_pos_cfe](l10n_br_pos_cfe/) | 14.0.1.4.0 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![lfdivino](https://github.com/lfdivino.png?size=30px)](https://github.com/lfdivino) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) [![ygcarvalh](https://github.com/ygcarvalh.png?size=30px)](https://github.com/ygcarvalh) | CF-e
[l10n_br_pos_nfce](l10n_br_pos_nfce/) | 14.0.1.1.4 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![lfdivino](https://github.com/lfdivino.png?size=30px)](https://github.com/lfdivino) [![luismalta](https://github.com/luismalta.png?size=30px)](https://github.com/luismalta) [![ygcarvalh](https://github.com/ygcarvalh.png?size=30px)](https://github.com/ygcarvalh) [![felipezago](https://github.com/felipezago.png?size=30px)](https://github.com/felipezago) | NFC-E no Ponto de Venda
[l10n_br_product_contract](l10n_br_product_contract/) | 14.0.1.1.1 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Criação de contratos através dos Pedidos de Vendas
[l10n_br_purchase](l10n_br_purchase/) | 14.0.3.4.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Brazilian Localization Purchase
[l10n_br_purchase_request](l10n_br_purchase_request/) | 14.0.1.0.2 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Purchase Request Brazilian Localization Purchase Request
[l10n_br_purchase_stock](l10n_br_purchase_stock/) | 14.0.1.3.1 |  | Brazilian Localization Purchase Stock
[l10n_br_repair](l10n_br_repair/) | 14.0.1.1.5 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Brazilian Localization Repair
[l10n_br_resource](l10n_br_resource/) | 14.0.1.0.4 | [![mileo](https://github.com/mileo.png?size=30px)](https://github.com/mileo) [![hendixcosta](https://github.com/hendixcosta.png?size=30px)](https://github.com/hendixcosta) [![lfdivino](https://github.com/lfdivino.png?size=30px)](https://github.com/lfdivino) | This module extend core resource to create important brazilian informations. Define a Brazilian calendar and some tools to compute dates used in financial and payroll modules
[l10n_br_sale](l10n_br_sale/) | 14.0.3.6.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian Localization Sale
[l10n_br_sale_blanket_order](l10n_br_sale_blanket_order/) | 14.0.1.0.1 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Brazilian Localization Sale Blanket Order
[l10n_br_sale_commission](l10n_br_sale_commission/) | 14.0.1.0.0 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Customization of Sales commissions module for implementations in Brazil.
[l10n_br_sale_invoice_plan](l10n_br_sale_invoice_plan/) | 14.0.1.0.3 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) | Brazilian Localization Sale Invoice Plan
[l10n_br_sale_stock](l10n_br_sale_stock/) | 14.0.1.2.1 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | Brazilian Localization Sales and Warehouse
[l10n_br_setup_tests](l10n_br_setup_tests/) | 14.0.1.0.1 | [![antoniospneto](https://github.com/antoniospneto.png?size=30px)](https://github.com/antoniospneto) | Modules for Odoo's Brazil-focused usability with integration tests.
[l10n_br_stock](l10n_br_stock/) | 14.0.2.1.1 |  | Brazilian Localization Warehouse
[l10n_br_stock_account](l10n_br_stock_account/) | 14.0.3.6.1 |  | Brazilian Localization WMS Accounting
[l10n_br_stock_account_report](l10n_br_stock_account_report/) | 14.0.1.1.3 | [![mbcosta](https://github.com/mbcosta.png?size=30px)](https://github.com/mbcosta) | P7 Stock Valuation Report
[l10n_br_website_sale](l10n_br_website_sale/) | 14.0.2.0.1 |  | Website sale localização brasileira.
[l10n_br_website_sale_delivery](l10n_br_website_sale_delivery/) | 14.0.1.0.1 | [![marcelsavegnago](https://github.com/marcelsavegnago.png?size=30px)](https://github.com/marcelsavegnago) [![DiegoParadeda](https://github.com/DiegoParadeda.png?size=30px)](https://github.com/DiegoParadeda) | Implements Brazilian freight values for delivery.
[l10n_br_zip](l10n_br_zip/) | 14.0.2.1.2 | [![renatonlima](https://github.com/renatonlima.png?size=30px)](https://github.com/renatonlima) | Brazilian Localisation ZIP Codes
[payment_bacen_pix](payment_bacen_pix/) | 14.0.1.1.0 |  | Payment PIX with bacen
[payment_pagseguro](payment_pagseguro/) | 14.0.1.0.9 |  | Payment Acquirer: PagSeguro Implementation
[spec_driven_model](spec_driven_model/) | 14.0.5.2.2 | [![rvalyi](https://github.com/rvalyi.png?size=30px)](https://github.com/rvalyi) | Tools for specifications driven mixins (from xsd for instance)

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
