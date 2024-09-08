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

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        company_sn = env.ref(
            "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
        )
        if company_sn:
            _logger.info(_("Loading l10n_br_stock warehouse external ids..."))
            set_stock_warehouse_external_ids(
                env, "l10n_br_base.empresa_simples_nacional"
            )
            set_stock_warehouse_external_ids(
                env, "l10n_br_base.empresa_lucro_presumido"
            )
