# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_round as round
from openerp.exceptions import ValidationError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    # TODO: Implementar total de juros e outras despesas acessórias.
    @api.depends('line_ids', 'line_ids.amount')
    @api.multi
    def _compute_total(self):
        for record in self:
            record.total = sum(record.mapped('line_ids.amount') or [0.0])

    @api.multi
    def action_open(self):
        """
        Validacao para nao confirmar ordem de pagamento vazia
        """
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("Impossible confirm empty line!"))
        return super(PaymentOrder, self).action_open()


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    @api.model
    def _get_info_partner(self, partner_record):
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

    @api.multi
    @api.depends('percent_interest', 'amount_currency')
    def _compute_interest(self):
        for record in self:
            precision = record.env[
                'decimal.precision'].precision_get('Account')
            record.amount_interest = round(
                record.amount_currency * (
                    record.percent_interest / 100), precision)
            # self.line.mode.percent_interest

    linha_digitavel = fields.Char(string=u"Linha Digitável")
    percent_interest = fields.Float(string=u"Percentual de Juros",
                                    digits=dp.get_precision('Account'))
    amount_interest = fields.Float(string=u"Valor Juros",
                                   compute='_compute_interest',
                                   digits=dp.get_precision('Account'))

    #
    # # TODO: Implementar total de juros e outras despesas acessórias.
    # @api.depends('line_ids', 'line_ids.amount')
    # @api.one
    # def _compute_total(self):
    #     self.total = sum(self.mapped('line_ids.amount') or [0.0])
