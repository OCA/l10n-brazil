# Copyright (C) 2022 - Renato Lima - Akretion
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    field_property = env.ref("l10n_br_fiscal.field_product_template__icms_origin")

    companies = env["res.company"].search([])
    for company in companies:
        products = env["product.template"].search(
            [
                "|",
                ("company_id", "=", company.id),
                ("company_id", "=", False),
                ("icms_origin", "!=", False),
            ]
        )
        for product in products:
            env["ir.property"].create(
                {
                    "name": "icms_origin",
                    "fields_id": field_property.id,
                    "company_id": company.id,
                    "type": "selection",
                    "res_id": "{},{}".format(product._name, product.id),
                    "value_text": product.icms_origin,
                }
            )
