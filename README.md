
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/l10n-brazil&target_branch=15.0)
[![Pre-commit Status](https://github.com/OCA/l10n-brazil/actions/workflows/pre-commit.yml/badge.svg?branch=15.0)](https://github.com/OCA/l10n-brazil/actions/workflows/pre-commit.yml?query=branch%3A15.0)
[![Build Status](https://github.com/OCA/l10n-brazil/actions/workflows/test.yml/badge.svg?branch=15.0)](https://github.com/OCA/l10n-brazil/actions/workflows/test.yml?query=branch%3A15.0)
[![codecov](https://codecov.io/gh/OCA/l10n-brazil/branch/15.0/graph/badge.svg)](https://codecov.io/gh/OCA/l10n-brazil)
[![Translation Status](https://translation.odoo-community.org/widgets/l10n-brazil-15-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/l10n-brazil-15-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Odoo Brazilian Localization / Localização Brasileira do Odoo

A localização brasileira do Odoo, criada pela comunidade Open Source da Odoo Community Association (OCA), inclui um conjunto de módulos detalhados para atender às normas fiscais e legais do Brasil. Esta localização aprimora o Odoo com funcionalidades para:

- **Documentos fiscais:** Suporte abrangente a documentações conforme legislação nacional.
- **Tributos específicos:** Gestão de ICMS, IPI, ISS, PIS, COFINS, CSLL, IRPJ, e outros, incluindo substituição tributária e retenção de impostos.
- **Emissão de notas fiscais eletrônicas:** Compatível com NF-e, NFS-e e mais.
- **Integrações bancárias:** Ferramentas para importação de extratos OFX e geração de CNAB 240 e 400.

## Começando com a Localização

Instale o módulo `l10n_br_base` para configurar as bases da localização brasileira no Odoo. Adicione o `l10n_br_fiscal` para expandir a emissão e gestão de documentos fiscais eletrônicos.

## :arrow_forward: **Teste a Localização Agora!**

Não perca a chance de ver a localização em ação:

1. Clique no botão abaixo para iniciar um container no ambiente Runboat:

   [![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/l10n-brazil&target_branch=15.0)

2. Aguarde até o container ficar disponível (indicador verde).
3. Clique em **Live** para acessar o Odoo.
4. Entre com `admin/admin`.
5. Escolha a empresa demo com o regime tributário de seu interesse, seja Simples Nacional ou Lucro Presumido, e explore um ambiente rico em detalhes e funcionalidades.

## ⚠️ **Aviso Importante sobre a branch 15.0**

A branch `15.0` é uma **transição técnica** entre as versões `14.0` e `16.0` e pode ser utilizada como **contingência** para implantações já realizadas no Odoo 15.0 no Brasil.

- **Se você está migrando da versão 14.0:** recomendamos migrar **diretamente para a 16.0**, que conta com uma base de usuários mais ampla e suporte mais ativo da comunidade.
- **Se você está iniciando um novo projeto Odoo:** opte por uma versão **superior à 15.0**, evitando começar por uma branch de transição.

💡 **OpenUpgrade:** no processo de migração **versão a versão** com o OpenUpgrade, recomendamos que **ao passar pela 15.0** você **não** inclua o repositório `OCA/l10n-brazil` no seu `addons_path`.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[l10n_br_account](l10n_br_account/) | 15.0.2.11.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | Invoicing and accounting entries for Brazil
[l10n_br_account_due_list](l10n_br_account_due_list/) | 15.0.1.1.0 |  | Brazilian Account Due List
[l10n_br_account_nfe](l10n_br_account_nfe/) | 15.0.2.1.0 | <a href='https://github.com/antoniospneto'><img src='https://github.com/antoniospneto.png' width='32' height='32' style='border-radius:50%;' alt='antoniospneto'/></a> <a href='https://github.com/felipemotter'><img src='https://github.com/felipemotter.png' width='32' height='32' style='border-radius:50%;' alt='felipemotter'/></a> <a href='https://github.com/mbcosta'><img src='https://github.com/mbcosta.png' width='32' height='32' style='border-radius:50%;' alt='mbcosta'/></a> | Integration between l10n_br_account and l10n_br_nfe
[l10n_br_account_payment_order](l10n_br_account_payment_order/) | 15.0.1.2.0 | <a href='https://github.com/mbcosta'><img src='https://github.com/mbcosta.png' width='32' height='32' style='border-radius:50%;' alt='mbcosta'/></a> | Brazilian Payment Order
[l10n_br_account_withholding](l10n_br_account_withholding/) | 15.0.1.1.0 | <a href='https://github.com/marcelsavegnago'><img src='https://github.com/marcelsavegnago.png' width='32' height='32' style='border-radius:50%;' alt='marcelsavegnago'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Brazilian Withholding Invoice Generator
[l10n_br_base](l10n_br_base/) | 15.0.1.1.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | Customization of base module for implementations in Brazil.
[l10n_br_cnab_structure](l10n_br_cnab_structure/) | 15.0.1.0.0 | <a href='https://github.com/antoniospneto'><img src='https://github.com/antoniospneto.png' width='32' height='32' style='border-radius:50%;' alt='antoniospneto'/></a> <a href='https://github.com/felipemotter'><img src='https://github.com/felipemotter.png' width='32' height='32' style='border-radius:50%;' alt='felipemotter'/></a> | This module allows defining the structure for generating the CNAB file. Used to exchange information with Brazilian banks.
[l10n_br_cnpj_search](l10n_br_cnpj_search/) | 15.0.1.2.0 |  | Integração com os Webservices da ReceitaWS e SerPro
[l10n_br_coa](l10n_br_coa/) | 15.0.2.1.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Base do Planos de Contas brasileiros
[l10n_br_coa_generic](l10n_br_coa_generic/) | 15.0.2.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Plano de Contas para empresas do Regime normal (Micro e pequenas empresas)
[l10n_br_coa_simple](l10n_br_coa_simple/) | 15.0.1.1.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Plano de Contas ITG 1000 para Microempresas e Empresa de Pequeno Porte
[l10n_br_crm](l10n_br_crm/) | 15.0.1.2.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/mbcosta'><img src='https://github.com/mbcosta.png' width='32' height='32' style='border-radius:50%;' alt='mbcosta'/></a> | Brazilian Localization CRM
[l10n_br_cte](l10n_br_cte/) | 15.0.1.2.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/marcelsavegnago'><img src='https://github.com/marcelsavegnago.png' width='32' height='32' style='border-radius:50%;' alt='marcelsavegnago'/></a> | Brazilian Electronic Invoice CT-e
[l10n_br_cte_spec](l10n_br_cte_spec/) | 15.0.1.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | CT-e spec
[l10n_br_currency_rate_update](l10n_br_currency_rate_update/) | 15.0.1.0.1 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Update exchange rates using OCA modules for Brazil
[l10n_br_fiscal](l10n_br_fiscal/) | 15.0.2.15.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Fiscal module/tax engine for Brazil
[l10n_br_fiscal_certificate](l10n_br_fiscal_certificate/) | 15.0.1.2.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | A1 fiscal certificate management for Brazil
[l10n_br_fiscal_closing](l10n_br_fiscal_closing/) | 15.0.2.3.0 |  | Period fiscal closing
[l10n_br_fiscal_dfe](l10n_br_fiscal_dfe/) | 15.0.1.1.1 |  | Distribuição de documentos fiscais
[l10n_br_fiscal_edi](l10n_br_fiscal_edi/) | 15.0.1.4.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Common EDI fiscal features
[l10n_br_hr](l10n_br_hr/) | 15.0.1.1.0 |  | Brazilian Localization HR
[l10n_br_ie_search](l10n_br_ie_search/) | 15.0.1.2.0 |  | Integração com a API SintegraWS e SEFAZ
[l10n_br_mdfe](l10n_br_mdfe/) | 15.0.1.3.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/marcelsavegnago'><img src='https://github.com/marcelsavegnago.png' width='32' height='32' style='border-radius:50%;' alt='marcelsavegnago'/></a> | Brazilian Eletronic Invoice MDF-e
[l10n_br_mdfe_spec](l10n_br_mdfe_spec/) | 15.0.1.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | MDF-e abstract models generated by xsdata-odoo from the oficial xsd
[l10n_br_mis_report](l10n_br_mis_report/) | 15.0.1.0.1 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Templates de relatórios contábeis brasileiros: Balanço Patrimonial e DRE
[l10n_br_nfe](l10n_br_nfe/) | 15.0.3.4.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Eletronic Invoicing for Brazil / NF-e
[l10n_br_nfe_spec](l10n_br_nfe_spec/) | 15.0.2.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | nfe spec
[l10n_br_nfse](l10n_br_nfse/) | 15.0.2.2.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/luismalta'><img src='https://github.com/luismalta.png' width='32' height='32' style='border-radius:50%;' alt='luismalta'/></a> <a href='https://github.com/marcelsavegnago'><img src='https://github.com/marcelsavegnago.png' width='32' height='32' style='border-radius:50%;' alt='marcelsavegnago'/></a> | Root electronic invoice for service / NFS-e module
[l10n_br_nfse_focus](l10n_br_nfse_focus/) | 15.0.1.3.0 | <a href='https://github.com/AndreMarcos'><img src='https://github.com/AndreMarcos.png' width='32' height='32' style='border-radius:50%;' alt='AndreMarcos'/></a> <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/ygcarvalh'><img src='https://github.com/ygcarvalh.png' width='32' height='32' style='border-radius:50%;' alt='ygcarvalh'/></a> <a href='https://github.com/marcelsavegnago'><img src='https://github.com/marcelsavegnago.png' width='32' height='32' style='border-radius:50%;' alt='marcelsavegnago'/></a> | NFS-e (FocusNFE)
[l10n_br_nfse_paulistana](l10n_br_nfse_paulistana/) | 15.0.1.1.0 | <a href='https://github.com/gabrielcardoso21'><img src='https://github.com/gabrielcardoso21.png' width='32' height='32' style='border-radius:50%;' alt='gabrielcardoso21'/></a> <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/luismalta'><img src='https://github.com/luismalta.png' width='32' height='32' style='border-radius:50%;' alt='luismalta'/></a> | NFS-e (Nota Paulistana)
[l10n_br_purchase](l10n_br_purchase/) | 15.0.1.3.1 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | Brazilian Localization Purchase
[l10n_br_resource](l10n_br_resource/) | 15.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> <a href='https://github.com/hendixcosta'><img src='https://github.com/hendixcosta.png' width='32' height='32' style='border-radius:50%;' alt='hendixcosta'/></a> <a href='https://github.com/lfdivino'><img src='https://github.com/lfdivino.png' width='32' height='32' style='border-radius:50%;' alt='lfdivino'/></a> | This module extend core resource to create important brazilian informations. Define a Brazilian calendar and some tools to compute dates used in financial and payroll modules
[l10n_br_sale](l10n_br_sale/) | 15.0.1.6.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Brazilian Localization Sale
[l10n_br_setup_tests](l10n_br_setup_tests/) | 15.0.1.0.0 | <a href='https://github.com/antoniospneto'><img src='https://github.com/antoniospneto.png' width='32' height='32' style='border-radius:50%;' alt='antoniospneto'/></a> | Modules for Odoo's Brazil-focused usability with integration tests.
[l10n_br_stock](l10n_br_stock/) | 15.0.1.0.1 |  | Brazilian Localization Warehouse
[l10n_br_zip](l10n_br_zip/) | 15.0.1.2.0 | <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Brazilian Localisation ZIP Codes
[spec_driven_model](spec_driven_model/) | 15.0.2.1.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> | XML binding for Odoo: XML to Odoo models and models to XML.

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
