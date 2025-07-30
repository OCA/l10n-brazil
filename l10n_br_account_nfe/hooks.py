# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, Command, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_simples_nacional_demo(env, registry)


def load_simples_nacional_demo(env, registry):
    """
    Load demo data for company 'Simples Nacional' with
    default user company set to this company.
    """

    # Load XML file with demo data.
    company_sn = env.ref(
        "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
    )
    if company_sn:
        # Allow all companies for OdooBot user and set default user company
        companies = env["res.company"].search([])
        env.user.company_ids = [Command.set(companies.ids)]
        env.user.company_id = company_sn

        tools.convert_file(
            env.cr,
            "l10n_br_account_nfe",
            "demo/account_invoice_sn_demo.xml",
            None,
            mode="init",
            noupdate=True,
            kind="demo",
        )

    # back to the main company as the next modules to be installed
    # expect this to be the default company.
    env.user.company_id = env.ref("base.main_company")
