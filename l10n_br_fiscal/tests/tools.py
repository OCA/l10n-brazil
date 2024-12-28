# Copyright (C) 2024 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files


def load_fiscal_fixture_files(env):
    # the following data is a minimal set of fixtures for the demo partners
    # of the base module when it's installed without demo data.
    partner_fixtures = {
        "res_partner_1": {},
        "res_partner_2": {},
        "res_partner_3": {},
        "res_partner_4": {},
        "res_partner_10": {},
        "res_partner_12": {},
        "res_partner_18": {},
    }
    for key, partner_data in partner_fixtures.items():
        if not env.ref(f"base.{key}", raise_if_not_found=False):
            if not partner_data.get("name"):
                partner_data["name"] = f"fixture_{key}"

            rec = env["res.partner"].create(partner_data)
            env["ir.model.data"].create(
                {
                    "name": key,
                    "res_id": rec.id,
                    "noupdate": True,
                    "module": "base",
                    "model": "res.partner",
                }
            )

    # the following data is a minimal set of fixtures for the demo products
    # of the product module when it's installed without demo data.
    product_fixtures = {
        "product_product_1": {},
        "product_product_2": {},
        "product_product_3": {},
        "product_product_4": {},
        "product_product_4b": {},
        "product_product_4c": {},
        "product_product_11b": {},
        "product_product_5": {},
        "product_product_6": {},
        "product_product_7": {},
        "product_product_8": {},
        "product_product_9": {},
        "product_product_10": {},
        "product_product_11": {},
        "product_product_12": {},
        "product_product_13": {},
        "product_product_16": {},
        "product_product_20": {},
        "product_product_22": {},
        "product_product_24": {},
        "product_product_25": {},
        "product_product_27": {},
        "expense_product": {},
        "expense_hotel": {},
        "product_delivery_01": {},
        "product_delivery_02": {},
        "product_delivery_03": {},
        "consu_delivery_01": {},
        "consu_delivery_02": {},
        "consu_delivery_03": {},
        "product_order_01": {},
    }
    for key, product_data in product_fixtures.items():
        if not env.ref(f"product.{key}", raise_if_not_found=False):
            if not product_data.get("name"):
                product_data["name"] = f"fixture_{key}"
            prod = env["product.product"].create(product_data)
            env["ir.model.data"].create(
                {
                    "name": key,
                    "res_id": prod.id,
                    "noupdate": True,
                    "module": "product",
                    "model": "product.product",
                }
            )
            if not env.ref(f"product.{key}_product_template", raise_if_not_found=False):
                env["ir.model.data"].create(
                    {
                        "name": f"{key}_product_template",
                        "res_id": prod.product_tmpl_id.id,
                        "noupdate": True,
                        "module": "product",
                        "model": "product.template",
                    }
                )
    if not env.ref("base.user_demo", raise_if_not_found=False):
        user_demo = env["res.users"].create(
            {
                "name": "Demo User",
                "login": "demo",
                "password": "demo",
                "email": "demo@yourcompany.com",
            }
        )
        env["ir.model.data"].create(
            {
                "name": "user_demo",
                "res_id": user_demo.id,
                "noupdate": True,
                "module": "base",
                "model": "res.users",
            }
        )

    load_fixture_files(
        env,
        "l10n_br_base",
        file_names=[
            "l10n_br_base_demo.xml",
            "res_company_demo.xml",
        ],
    )
    load_fixture_files(
        env,
        "l10n_br_fiscal",
        file_names=[
            "company_demo.xml",
            "partner_demo.xml",
            #            "l10n_br_fiscal.ncm-demo.csv",
            #            "l10n_br_fiscal.cest-demo.csv",
            "fiscal_operation_demo.xml",
            "icms_tax_definition_demo.xml",
            "product_demo.xml",
            "fiscal_document_demo.xml",
        ],
    )
