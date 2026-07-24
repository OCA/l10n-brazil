# Copyright (C) 2020 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

_logger = logging.getLogger(__name__)


def set_stock_warehouse_external_ids(env, company_external_id):
    module, external_id = company_external_id.split(".")
    company = env.ref(company_external_id, raise_if_not_found=False)
    if not company:
        return
    warehouse = env["stock.warehouse"].search(
        [("company_id", "=", company.id)], limit=1
    )
    if not warehouse:
        return

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


def ensure_demo_warehouse(env, company_external_id, partner_external_id, code):
    """Ensure a demo warehouse exists for the given company.

    The stock module auto-creates a warehouse for each company, but in some
    installation orders (e.g. OCA CI installing many modules at once) the
    warehouse may not exist yet when l10n_br_stock's hooks run. This function
    creates it if needed and is idempotent.
    """
    company = env.ref(company_external_id, raise_if_not_found=False)
    if not company:
        return
    warehouse = env["stock.warehouse"].search(
        [("company_id", "=", company.id)], limit=1
    )
    if warehouse:
        return warehouse
    partner = env.ref(partner_external_id, raise_if_not_found=False)
    vals = {
        "name": company.name,
        "code": code,
        "company_id": company.id,
    }
    if partner:
        vals["partner_id"] = partner.id
    _logger.info(
        "Creating demo warehouse %s (%s) for company %s",
        code,
        company.name,
        company_external_id,
    )
    return env["stock.warehouse"].create(vals)


def pre_init_hook(env):
    """Import XML data to change core data"""
    if env.ref("base.module_stock").demo:
        _logger.info("Loading l10n_br_stock warehouse external ids...")
        ensure_demo_warehouse(
            env,
            "l10n_br_base.empresa_simples_nacional",
            "l10n_br_base.res_partner_cliente1_sp",
            "ESN",
        )
        ensure_demo_warehouse(
            env,
            "l10n_br_base.empresa_lucro_presumido",
            "l10n_br_base.res_partner_cliente1_sp",
            "ELP",
        )
        ensure_demo_warehouse(
            env,
            "l10n_br_base.empresa_lucro_real",
            "l10n_br_base.res_partner_cliente1_sp",
            "ELR",
        )
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_simples_nacional")
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_lucro_presumido")
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_lucro_real")


def create_locations_quants(env, locations, products):
    """
    Create Quants for Inventory, use in Test and Demo Data
    :param locations: List of the Stock Locations
    :param products: List of the Products
    """
    for location in locations:
        _logger.info(f"Create Quants Inventory in {location.name} for Demo Data ...")
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


def post_init_hook(env):
    if env.ref("base.module_l10n_br_stock").demo:
        # Create external IDs for demo company warehouses (they didn't exist
        # during pre_init_hook because stock module creates them after)
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_simples_nacional")
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_lucro_presumido")
        set_stock_warehouse_external_ids(env, "l10n_br_base.empresa_lucro_real")

        # Get warehouses for demo companies
        company_sn = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )
        company_lp = env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        company_lr = env.ref(
            "l10n_br_base.empresa_lucro_real", raise_if_not_found=False
        )

        locations = []
        if company_sn:
            warehouse_sn = env["stock.warehouse"].search(
                [("company_id", "=", company_sn.id)], limit=1
            )
            if warehouse_sn:
                locations.append(warehouse_sn.lot_stock_id)
        if company_lp:
            warehouse_lp = env["stock.warehouse"].search(
                [("company_id", "=", company_lp.id)], limit=1
            )
            if warehouse_lp:
                locations.append(warehouse_lp.lot_stock_id)
        if company_lr:
            warehouse_lr = env["stock.warehouse"].search(
                [("company_id", "=", company_lr.id)], limit=1
            )
            if warehouse_lr:
                locations.append(warehouse_lr.lot_stock_id)

        if locations:
            create_locations_quants(
                env,
                locations,
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
