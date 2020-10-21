# Copyright (C) 2020 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import SUPERUSER_ID, api
from odoo import _, tools

_logger = logging.getLogger(__name__)


def set_stock_warehouse_external_ids(env, company_external_id):
    module, external_id = company_external_id.split('.')
    warehouse = env['stock.warehouse'].search([
        ('company_id', '=', env.ref(company_external_id).id)
    ], limit=1)

    data_list = [{
        'xml_id': 'l10n_br_stock.wh_{}'.format(external_id),
        'record': warehouse,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_loc_stock_id'.format(external_id),
        'record': warehouse.lot_stock_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_view_location'.format(external_id),
        'record': warehouse.view_location_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_input_location'.format(external_id),
        'record': warehouse.wh_input_stock_loc_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_quality_control_location'.format(external_id),
        'record': warehouse.wh_qc_stock_loc_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_pack_location'.format(external_id),
        'record': warehouse.wh_pack_stock_loc_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_output_location'.format(external_id),
        'record': warehouse.wh_pack_stock_loc_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_picking_type_in'.format(external_id),
        'record': warehouse.in_type_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_picking_type_internal'.format(external_id),
        'record': warehouse.int_type_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_pick_type_internal'.format(external_id),
        'record': warehouse.pick_type_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_pack_type_internal'.format(external_id),
        'record': warehouse.pack_type_id,
        'noupdate': True,
    }, {
        'xml_id': 'l10n_br_stock.wh_{}_picking_type_out'.format(external_id),
        'record': warehouse.out_type_id,
        'noupdate': True,
    }]
    env['ir.model.data']._update_xmlids(data_list)


def pre_init_hook(cr):
    """Import XML data to change core data"""

    if not tools.config["without_demo"]:
        _logger.info(_("Loading l10n_br_stock warehouse external ids..."))
        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})
            set_stock_warehouse_external_ids(
                env, 'l10n_br_base.empresa_simples_nacional')
            set_stock_warehouse_external_ids(
                env, 'l10n_br_base.empresa_lucro_presumido')
