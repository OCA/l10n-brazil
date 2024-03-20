# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round as round
from .account_payment_mode import OPERATION_TYPE


class PaymentLine(models.Model):
    _inherit = 'account.payment.line'

    @api.model
    def _get_info_partner(self, partner_record):
        if not partner_record:
            return False
        st = partner_record.street or ''
        n = partner_record.street_number or ''
        st1 = partner_record.street2 or ''
        zip = partner_record.zip or ''
        city = partner_record.city_id.name or ''
        uf = partner_record.state_id.code or ''
        zip_city = city + '-' + uf + '\n' + zip
        cntry = partner_record.country_id and \
            partner_record.country_id.name or ''
        cnpj = partner_record.cnpj_cpf or ''
        return partner_record.legal_name or '' + "\n" + cnpj + "\n" + st \
            + ", " + n + "  " + st1 + "\n" + zip_city + "\n" + cntry

    @api.multi
    @api.depends('percent_interest', 'amount_currency')
    def _compute_interest(self):
        for record in self:
            precision = record.env[
                'decimal.precision'].precision_get('Account')
            record.amount_interest = round(
                record.amount_currency * (
                    record.percent_interest / 100), precision)

    linha_digitavel = fields.Char(string="Linha Digitável")
    percent_interest = fields.Float(string="Percentual de Juros",
                                    digits=dp.get_precision('Account'))
    amount_interest = fields.Float(string="Valor Juros",
                                   compute='_compute_interest',
                                   digits=dp.get_precision('Account'))

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        string='Tipo de Operação',
        related='order_id.operation_type',
        store=True
    )
