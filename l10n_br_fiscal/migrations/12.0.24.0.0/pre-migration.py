# Copyright (C) 2022 - Renato Lima - Akretion
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    field_property = env.ref("l10n_br_fiscal.field_product_template__icms_origin")

    env.cr.execute(
        "SELECT id, icms_origin FROM product_template WHERE icms_origin is not NULL"
    )
    products = env.cr.fetchall()
    companies = env["res.company"].search([])
    for company in companies:
        for product in products:
            env["ir.property"].create(
                {
                    "name": "icms_origin",
                    "fields_id": field_property.id,
                    "company_id": company.id,
                    "type": "selection",
                    "res_id": "product.template,{}".format(product[0]),
                    "value_text": product[1],
                }
            )
