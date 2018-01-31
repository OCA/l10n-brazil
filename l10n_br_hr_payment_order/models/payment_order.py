# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import (
    TIPO_DE_FOLHA,
)


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
        states={'done': [('readonly', True)]},
    )

    hr_payslip_ids = fields.One2many(
        string='Holerites',
        comodel_name='hr.payslip',
        inverse_name='payment_order_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    mesmo_banco = fields.Boolean(
        string="Somente para Mesmo Banco ?",
        default=True,
    )

    cnab_file = fields.Binary(
        string='CNAB File',
        readonly=True,
    )

    cnab_filename = fields.Char("CNAB Filename")

    @api.multi
    def _prepare_folha_payment_line(self, line):
        self.ensure_one()
#        date_to_pay = False  # no payment date => immediate payment
        state = 'normal'
        communication = 'Holerite: ' + line.display_name or '-'
        amount_currency = line.total

        # Seta no Holerite em qual remessa esta o pagamento
        line.slip_id.payment_order_id = self.id

        if line.partner_id != line.slip_id.employee_id.address_home_id:
            banco = line.partner_id.bank_ids[0].id,
        else:
            banco = line.slip_id.employee_id.bank_account_id.id,

        res = {
            'amount_currency': amount_currency,
            'bank_id': banco,
            'order_id': self.id,
            'partner_id': line.partner_id and line.partner_id.id or False,
            # account banking
            'communication': communication,
            'state': state,
            # end account banking
            'date': self.date_scheduled,
            'payslip_id': line.slip_id.id,
        }
        return res

    @api.one
    def folha_payment_import(self):
        """ A importação de holerites nas payment orders funciona da
        seguinte maneira:

        1. Busca holerites que estão no status: "Aguardando pagamento" e
        coincidem com o tipo setado no filtro

        2. Preparar: Prepara os dados para inclusão:
            _prepare_financial_payment_line
        3. Criar
        """

        # Identifica o banco de pagamento
        banco = self.mode.bank_id.bank.id

        self.line_ids.unlink()
        self.hr_payslip_ids = False

        payslip_ids = self.env['hr.payslip'].search([
            ('tipo_de_folha', '=', self.tipo_de_folha),
            ('state', '=', 'verify'),
            ('payment_mode_id', '=', self.mode.id),
        ])

        rubricas_pagaveis = self.env['hr.salary.rule'].search([
            ('eh_pagavel', '=', True)
        ])

        payslip_line_ids = self.env['hr.payslip.line'].search([
            ('slip_id', 'in', payslip_ids.ids),
            ('salary_rule_id', 'in', rubricas_pagaveis.ids)
        ])

        # Populate the current payment with new lines:
        for line in payslip_line_ids:

            # Identifica o banco de pagamento do holerite
            if line.partner_id != line.slip_id.employee_id.address_home_id:
                if line.partner_id.bank_ids:
                    banco_holerite = line.partner_id.bank_ids[0].bank.id
                else:
                    banco_holerite = False
            else:
                banco_holerite = \
                    line.slip_id.employee_id.bank_account_id.bank.id

            if banco_holerite and banco == banco_holerite:
                vals = self._prepare_folha_payment_line(line)
                self.env['payment.line'].create(vals)

        return
