<<<<<<< HEAD
# Copyright (C) 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
=======
# Copyright (C) 2021 - Renato Lima - Akretion
>>>>>>> bump l10n_br_fiscal version 12.0.18.0.0 and add script migration
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

<<<<<<< HEAD
_field_renames = [
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_pis_ret_base",
        "amount_pis_wh_base",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_cofins_ret_base",
        "amount_confis_wh_base",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_issqn_ret_base",
        "amount_issqn_wh_base",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_csll_ret_base",
        "amount_csll_wh_base",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_irpj_ret_base",
        "amount_irpj_wh_base",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_pis_ret_value",
        "amount_pis_wh_value",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_cofins_ret_value",
        "amount_confis_wh_value",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_issqn_ret_value",
        "amount_issqn_wh_value",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_csll_ret_value",
        "amount_csll_wh_value",
    ),
    (
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal_document_mixin",
        "amount_irpj_ret_value",
        "amount_irpj_wh_value",
    ),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
=======

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE
            l10n_br_fiscal_document
        SET
            document_key = regexp_replace(document_key, '[^0-9]+', '', 'g')
        """
    )
>>>>>>> bump l10n_br_fiscal version 12.0.18.0.0 and add script migration
