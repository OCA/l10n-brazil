# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo.addons.l10n_br_fiscal.tools import set_journal_in_fiscal_operation


def post_init_hook(env):
    if env.ref("base.module_l10n_br_purchase").demo:
        purchase_orders = env["purchase.order"].search(
            [("company_id", "!=", env.ref("base.main_company").id)]
        )

        for order in purchase_orders:
            defaults = order.with_context(company_id=order.company_id.id).default_get(
                order._fields
            )
            defaults.update(
                {
                    "name": order.name,
                    "company_id": order.company_id.id,
                    "fiscal_operation_id": order.fiscal_operation_id.id,
                }
            )
            order.write(defaults)

        # Load COA Fiscal Operation properties
        purchase_set_journal_in_fiscal_operation(env)


def purchase_set_journal_in_fiscal_operation(env):
    company = env.ref("l10n_br_base.empresa_simples_nacional", raise_if_not_found=False)
    # COA Simple Fiscal Operation properties
    if company and env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_coa_simple"),
            ("state", "=", "installed"),
        ]
    ):
        # Load Fiscal Operation Main Company
        set_journal_in_fiscal_operation(
            env.cr,
            env.ref("base.main_company"),
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_compras",
                    "journal": "l10n_br_coa_simple.purchase_journal_main_company",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_devolucao_compras",
                    "journal": "l10n_br_coa_simple.purchase_journal_main_company",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_coa_simple.purchase_journal_main_company",
                },
            ],
        )

        # Load Fiscal Operation for Simples Nacional
        set_journal_in_fiscal_operation(
            env.cr,
            company,
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_compras",
                    "journal": "l10n_br_coa_simple.purchase_journal_empresa_sn",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_devolucao_compras",
                    "journal": "l10n_br_coa_simple.purchase_journal_empresa_sn",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_coa_simple.purchase_journal_empresa_sn",
                },
            ],
        )

    company_lc = env.ref(
        "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
    )

    # COA Generic Fiscal Operation properties
    if company_lc and env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_coa_generic"),
            ("state", "=", "installed"),
        ]
    ):
        # Load Fiscal Operation for Lucro Presumido
        set_journal_in_fiscal_operation(
            env.cr,
            company_lc,
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_compras",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lp",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_devolucao_compras",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lp",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lp",
                },
            ],
        )

    company_lr = env.ref("l10n_br_base.empresa_lucro_real", raise_if_not_found=False)

    # COA Generic Fiscal Operation properties
    if company_lr and env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_coa_generic"),
            ("state", "=", "installed"),
        ]
    ):
        # Load Fiscal Operation for Lucro Real
        set_journal_in_fiscal_operation(
            env.cr,
            company_lr,
            [
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_compras",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lr",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_devolucao_compras",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lr",
                },
                {
                    "fiscal_operation": "l10n_br_fiscal.fo_entrada_remessa",
                    "journal": "l10n_br_coa_generic.purchase_journal_empresa_lr",
                },
            ],
        )
