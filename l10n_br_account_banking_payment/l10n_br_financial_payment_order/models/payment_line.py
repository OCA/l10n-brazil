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

    financial_id = fields.Many2one(
        comodel_name='financial.move',
        string="Financeiro",
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

