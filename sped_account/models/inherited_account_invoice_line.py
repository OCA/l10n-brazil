# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


# import logging
# _logger = logging.getLogger(__name__)

# try:
# from pybrasil.valor import valor_por_extenso_item
# from pybrasil.valor.decimal import Decimal as D

# except (ImportError, IOError) as err:
# _logger.debug(err)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string=u'Item do Documento Fiscal',
        ondelete='cascade',
    )
    is_brazilian_invoice = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='invoice_id.is_brazilian_invoice',
    )

    @api.multi
    def _check_brazilian_invoice(self, operation):
        for item in self:
            if (item.is_brazilian_invoice and
                    'sped_documento_item_id' not in self._context):
                if operation == 'create':
                    raise ValidationError(
                        'This is a Brazilian Invoice! You should create it '
                        'through the proper Brazilian Fiscal Document!')
                elif operation == 'write':
                    raise ValidationError(
                        'This is a Brazilian Invoice! You should change it '
                        'through the proper Brazilian Fiscal Document!')
                elif operation == 'unlink':
                    raise ValidationError(
                        'This is a Brazilian Invoice! You should delete it '
                        'through the proper Brazilian Fiscal Document!')

    @api.multi
    def create(self, dados):
        invoice = super(AccountInvoiceLine, self).create(dados)
        invoice._check_brazilian_invoice()
        return invoice

    @api.multi
    def write(self, dados):
        self._check_brazilian_invoice()
        res = super(AccountInvoiceLine, self).write(dados)
        return res

    @api.multi
    def unlink(self):
        self._check_brazilian_invoice()
        res = super(AccountInvoiceLine, self).unlink()
        return res
