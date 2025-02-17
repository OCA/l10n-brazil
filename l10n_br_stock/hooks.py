# Copyright (C) 2020 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)


def set_stock_warehouse_external_ids(env, company_external_id):
    module, external_id = company_external_id.split(".")
    warehouse = env["stock.warehouse"].search(
        [("company_id", "=", env.ref(company_external_id).id)], limit=1
    )

    data_list = [
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}",
            "record": warehouse,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_loc_stock_id",
            "record": warehouse.lot_stock_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_view_location",
            "record": warehouse.view_location_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_input_location",
            "record": warehouse.wh_input_stock_loc_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_quality_control_location",
            "record": warehouse.wh_qc_stock_loc_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_pack_location",
            "record": warehouse.wh_pack_stock_loc_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_output_location",
            "record": warehouse.wh_pack_stock_loc_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_picking_type_in",
            "record": warehouse.in_type_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_picking_type_internal",
            "record": warehouse.int_type_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_pick_type_internal",
            "record": warehouse.pick_type_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_pack_type_internal",
            "record": warehouse.pack_type_id,
            "noupdate": True,
        },
        {
            "xml_id": f"l10n_br_stock.wh_{external_id}_picking_type_out",
            "record": warehouse.out_type_id,
            "noupdate": True,
        },
    ]
    env["ir.model.data"]._update_xmlids(data_list)


def pre_init_hook(cr):
    """Import XML data to change core data"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_stock").demo:
        _logger.info(_("Loading l10n_br_stock warehouse external ids..."))
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_simples_nacional")
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_lucro_presumido")


def create_locations_quants(cr, locations, products):
    """
    Create Quants for Inventory, use in Test and Demo Data
    :param locations: List of the Stock Locations
    :param products: List of the Products
    """
    for location in locations:
        _logger.info(f"Create Quants Inventory in {location.name} for Demo Data ...")
        env = api.Environment(cr, SUPERUSER_ID, {})
        quants = env["stock.quant"]
        for product in products:
            quants |= (
                env["stock.quant"]
                .with_context(inventory_mode=True)
                .create(
                    {
                        "product_id": product.id,
                        "inventory_quantity": 500,
                        "location_id": location.id,
                    }
                )
            )
        quants.action_apply_inventory()


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_stock").demo:
        create_locations_quants(
            cr,
            [
                env.ref("l10n_br_stock.wh_empresa_simples_nacional").lot_stock_id,
                env.ref("l10n_br_stock.wh_empresa_lucro_presumido").lot_stock_id,
            ],
            [
                env.ref("product.product_product_24"),
                env.ref("product.product_product_7"),
                env.ref("product.product_product_6"),
                env.ref("product.product_product_9"),
                env.ref("product.product_product_10"),
                env.ref("product.product_product_11"),
                env.ref("product.product_product_11b"),
                env.ref("product.product_product_4"),
                env.ref("product.product_product_4b"),
                env.ref("product.product_product_4c"),
                env.ref("product.product_product_12"),
                env.ref("product.product_product_13"),
                env.ref("product.product_product_27"),
                env.ref("product.product_product_3"),
                env.ref("product.product_product_25"),
            ],
        )
