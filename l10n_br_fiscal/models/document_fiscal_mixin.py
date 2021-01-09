# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    FINAL_CUSTOMER,
    FINAL_CUSTOMER_YES,
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
    FISCAL_COMMENT_DOCUMENT,
)


class FiscalDocumentMixin(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin'
    _inherit = 'l10n_br_fiscal.document.mixin.methods'
    _description = 'Document Fiscal Mixin'

    def _date_server_format(self):
        return fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_operation(self):
        return False

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved'),
                  '|', ('company_id', '=', self.env.user.company_id.id),
                  ('company_id', '=', False)]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operation',
        domain=lambda self: self._operation_domain(),
        default=_default_operation,
    )

    #
    # Company and Partner are defined here to avoid warnings on runbot
    #
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )

    fiscal_operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='fiscal_operation_id.fiscal_operation_type',
        string='Fiscal Operation Type',
        readonly=True,
    )

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string='Buyer Presence',
        default=NFE_IND_PRES_DEFAULT,
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='l10n_br_fiscal_document_mixin_comment_rel',
        column1='document_mixin_id',
        column2='comment_id',
        string='Comments',
        domain=[('object', '=', FISCAL_COMMENT_DOCUMENT)],
    )

    fiscal_additional_data = fields.Text(
        string='Fiscal Additional Data',
    )

    customer_additional_data = fields.Text(
        string='Customer Additional Data',
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string='Final Consumption Operation',
        default=FINAL_CUSTOMER_YES,
    )
