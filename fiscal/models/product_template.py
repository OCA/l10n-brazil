# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .constants.fiscal import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    NCM_FOR_SERVICE)

from .constants.icms import ICMS_ORIGIN


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string='Fiscal Type')

    origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem',
        default='0')

    ncm_id = fields.Many2one(
        comodel_name='fiscal.ncm',
        index=True,
        string='NCM')

    fiscal_genre_id = fields.Many2one(
        comodel_name='fiscal.product.genre',
        string='Fiscal Genre')

    fiscal_genre_code = fields.Char(
        related='fiscal_genre_id.code',
        store=True,
        string='Fiscal Genre Code')

    nbs_id = fields.Many2one(
        comodel_name='fiscal.nbs',
        index=True,
        string='NBS')

    cest_id = fields.Many2one(
        comodel_name='fiscal.cest',
        index=True,
        string='CEST',
        domain="[('ncm_ids', '=', ncm_id)]")

    # TODO add percent of estimate taxes

    @api.onchange('ncm_id', 'fiscal_genre_id')
    def _onchange_ncm_id(self):
        for r in self:
            if r.ncm_id:
                r.fiscal_genre_id = self.env['fiscal.product.genre'].search(
                    [('code', '=', r.ncm_id.code[0:2])])

            if r.fiscal_genre_id.code == PRODUCT_FISCAL_TYPE_SERVICE:
                r.ncm_id = self.env['fiscal.ncm'].search(
                    [('code', '=', NCM_FOR_SERVICE)])
