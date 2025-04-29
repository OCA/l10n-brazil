# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    """Relate fiscal taxes to account taxes."""
    for company in env["res.company"].with_context(active_test=False).search([]):
        if "br_oca" in env["account.chart.template"]._get_parent_template(
            company.chart_template
        ):
            env["account.chart.template"].try_loading(company.chart_template, company)
