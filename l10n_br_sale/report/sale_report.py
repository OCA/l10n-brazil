# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
)


class SaleReport(models.Model):
    _inherit = 'sale.report'

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Fiscal Operation',
        readonly=True,
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation.line',
        string='Fiscal Operation Line',
        readonly=True,
    )

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string='Buyer Presence',
        default=NFE_IND_PRES_DEFAULT,
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}

        fields.update({
            'fiscal_operation_id':
                ', l.fiscal_operation_id as fiscal_operation_id',
            'fiscal_operation_line_id':
                ', l.fiscal_operation_line_id as fiscal_operation_line_id',
            'ind_pres': ', s.ind_pres',
        })
        groupby += """
            , l.fiscal_operation_id
            , l.fiscal_operation_line_id
            , s.ind_pres
        """
        return super()._query(with_clause=with_clause, fields=fields,
                              groupby=groupby, from_clause=from_clause)
