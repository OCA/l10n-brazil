# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from openerp import api, fields, models, _
from openerp.addons.l10n_br_financial_payment_order.models.bank_payment_line \
    import STATE




class PaymentLine(models.Model):
    _inherit = b'payment.line'

    # @api.one
    # @api.depends('percent_interest', 'amount_currency')
    # def _compute_interest(self):
    #     precision = self.env['decimal.precision'].precision_get('Account')
    #     self.amount_interest = round(self.amount_currency *
    #                                  (self.percent_interest / 100),
    #                                  precision)

    def _get_payment_line_reference(self):
        return [
            (
                self.env['financial.move']._name,
                self.env['financial.move']._description
             ),
        ]

    @api.multi
    @api.depends('financial_id')
    def _compute_reference_id(self):

        for record in self:
            if record.financial_id:
                record.reference_id = (
                    record.financial_id._name +
                    ',' +
                    str(record.financial_id.id)
                )

    amount_other_discounts = fields.Float(
        string='Valor Abatimento',
    )
    amount_discount = fields.Float(
        string='Valor Desconto',
    )
    amount_interest = fields.Float(
        string='Valor Mora',
    )
    amount_penalty = fields.Float(
        string='Valor Multa',
    )
    #  TODO: Definir campos do segmento P/Q/R/T/U
    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )
    linha_digitavel = fields.Char(string=u"Linha Digitável")
    state2 = fields.Selection(
        related="bank_line_id.state2",
        selection=STATE,
        default="draft",
    )

    reference_id = fields.Reference(
        compute='_compute_reference_id',
        selection=_get_payment_line_reference,
        string='Origem'
    )

    financial_id = fields.Many2one(
        comodel_name='financial.move',
        string="Financeiro",
    )
    fn_date_document = fields.Date(
        related='financial_id.date_document',
        string="Criação",
        readonly=True,
    )
    fn_date_maturity = fields.Date(
        related='financial_id.date_maturity',
        string='Vencimento',
        readonly=True,
    )
    fn_date_business_maturity = fields.Date(
        related='financial_id.date_business_maturity',
        string='Vencimento útil',
        readonly=True,
    )
    fn_boleto_linha_digitavel = fields.Char(
        related='financial_id.boleto_linha_digitavel',
        string='Linha digitável',
        readonly=True,
    )
    fb_boleto_codigo_barras = fields.Char(
        related='financial_id.boleto_codigo_barras',
        string='Código de barras',
        readonly=True,
    )
    fn_nosso_numero = fields.Float(
        string='Nosso número',
        related='financial_id.nosso_numero',
    )


    def _get_info_partner(self, cr, uid, partner_record, context=None):
        # TODO: Melhorar este método
        if not partner_record:
            return False
        st = partner_record.street or ''
        n = partner_record.number or ''
        st1 = partner_record.street2 or ''
        zip = partner_record.zip or ''
        city = partner_record.l10n_br_city_id.name or ''
        uf = partner_record.state_id.code or ''
        zip_city = city + '-' + uf + '\n' + zip
        cntry = partner_record.country_id and \
            partner_record.country_id.name or ''
        cnpj = partner_record.cnpj_cpf or ''
        return partner_record.legal_name or '' + "\n" + cnpj + "\n" + st \
            + ", " + n + "  " + st1 + "\n" + zip_city + "\n" + cntry

