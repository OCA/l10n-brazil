# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.addons.l10n_br_base.constante_tributaria import (
    REGIME_TRIBUTARIO,
    MODELO_FISCAL,
    IE_DESTINATARIO,
    TIPO_EMISSAO,
    ENTRADA_SAIDA,
    TIPO_CONSUMIDOR_FINAL,
    ENTRADA_SAIDA_SAIDA,
)
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoiceLine(SpedCalculoImpostoItem, models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends(
        'price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        'invoice_id.company_id', 'invoice_id.date_invoice',
        #
        # Campos brasileiros
        #
        'produto_id',
        'quantidade',
        'vr_unitario',
        'vr_desconto',
        'unidade',
        'operacao_id',
        'operacao_item_id',
        'protocolo_id',
        # TODO: Outros campos que precisamos monitorar
    )
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        if self.is_brazilian:
             self._amount_price_brazil()

    order_id = fields.Many2one(
        #
        # Workarround para o cálculo globalizado. Devido a diferença dos
        # modelos da invoice/sale/purchase
        #
        comodel_name='account.invoice',
        related='invoice_id',
        readonly=True,
        index=True,
    )
    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string=u'Item do Documento Fiscal',
        ondelete='cascade',
    )
    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='invoice_id.is_brazilian',
    )

    vr_nf = fields.Monetary(
        compute='_amount_price_brazil'
    )
    vr_fatura = fields.Monetary(
        compute='_amount_price_brazil'
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='invoice_id.sped_empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='invoice_id.sped_participante_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        related='invoice_id.sped_operacao_produto_id',
        readonly=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='invoice_id.date_invoice',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        line = super(AccountInvoiceLine, self).create(vals)
        #
        # Não podemos verificar se empresa é brasileira aqui, pois muitas
        # vezes não temos o company_id
        #
        # if "create_brazil" not in self._context:
        #     # line._create_brazil()
        #     pass
        line.calcula_impostos()
        return line

    # def get_invoice_line_account(self, type, product, fpos, company):
    #     if not self.is_brazilian:
    #         return self.get_invoice_line_account(
    #              type, product, fpos, company)
    #
    #     if self.operacao_id.entrada_saida == ENTRADA_SAIDA_SAIDA:
    #         return self.product_id.property_account_income_id
    #     else:
    #         return self.product_id.property_account_expense_id

    @api.onchange('produto_id')
    def onchange_product_brazil(self):
        domain = {}
        if not self.invoice_id:
            return
        if not (self.invoice_id.sped_operacao_produto_id or
                self.invoice_id.sped_operacao_servico_id):
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'Por favor defina a operação'),
            }
            return {'warning': warning}

            # @api.multi
            # def _create_brazil(self):
            #     Brazil = self.env["account.invoice.line.brazil"]
            #     for item in self:
            #         related_vals = {
            #             'invoice_line_id': item.id,
            #             'vr_unitario': item.price_unit,
            #             'quantidade': item.quantity,
            #             'produto_id': item.product_id.sped_produto_id.id,
            #             'unidade_id': item.uom_id.sped_unidade_id.id
            #         }
            #         new = Brazil.create(related_vals)
            #     return True
            #
            # @api.multi
            # def _new_brazil(self):
            #     Brazil = self.env["account.invoice.line.brazil"]
            #     for item in self:
            #         related_vals = {
            #             'invoice_line_id': item.id,
            #             'vr_unitario': item.price_unit,
            #             'quantidade': item.quantity,
            #             'produto_id': item.product_id.sped_produto_id.id,
            #             'unidade_id': item.uom_id.sped_unidade_id.id
            #         }
            #         new = Brazil.new(related_vals)
            #     return True
            #
            # @api.model
            # def new(self, values={}):
            #     record = super(AccountInvoiceLine, self).new(values)
            #     if "create_brazil" not in self._context:
            #         record._new_brazil()
            #     return record

            # @api.model
            # def create(self, vals):
            #     record = super(AccountInvoiceLineBrazil, self.with_context(
            #         create_brazil=True)).create(vals)
            #     record.calcula_impostos()
            #     return record

            # @api.model
            # Funçao usada nas criação das compras através do purchase.
            # Mas ela quebra a invoice normal.
            # def new(self, values={}):
            #     record = super(AccountInvoiceLineBrazil, self.with_context(
            #         create_brazil=True)).new(values)
            #     record.calcula_impostos()
            #     return record

    @api.multi
    def _prepare_sped_line(self):
        """
        Prepare the dict of values to create the new sped.document

        converting invoice.line object into a sped.documento.item.

        """
        return self._convert_to_write(self._cache)


    @api.multi
    def sped_line_create(self, documento_id):
        """
        Create a sped.documento.

        :param invoice_id: integer
        """
        for line in self:
            vals = line._prepare_sped_line()
            vals.update({
                'documento_id': documento_id,
                'account_invoice_ids': [
                    (6, 0, [line.id])
                ]
            })
            line = self.env['sped.documento.item'].create(vals)
            line.calcula_impostos()
