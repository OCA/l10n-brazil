# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


@openupgrade.migrate()
def migrate(env, version):
    with api.Environment.manage():
        env = api.Environment(env.cr, SUPERUSER_ID, {})
        Company = env["res.company"]
        NCM = env["l10n_br_fiscal.ncm"]
        NBS = env["l10n_br_fiscal.nbs"]
        TaxEstimate = env["l10n_br_fiscal.tax.estimate"]
        companies = Company.search([])
        for company in companies:
            for ncm in NCM.search([]):
                last_estimated = TaxEstimate.search(
                    [("company_id", "=", company.id), ("ncm_id", "=", ncm.id)],
                    order="create_date DESC",
                    limit=1,
                )
                ncm.with_company(company).update_estimated_taxes(last_estimated)
            for nbs in NBS.search([]):
                last_estimated = TaxEstimate.search(
                    [("company_id", "=", company.id), ("nbs_id", "=", nbs.id)],
                    order="create_date DESC",
                    limit=1,
                )
                nbs.with_company(company).update_estimated_taxes(last_estimated)
        env.cr.commit()
