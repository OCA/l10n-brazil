# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor
    from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')


class HrPayslipeLine(models.Model):
    _inherit = "hr.payslip.line"

    round_amount = fields.Float(
        string=u'Valor',
        store=True,
        digits=(10, 2),
        compute='_compute_arredondamento'
    )

    round_total = fields.Float(
        string=u'Total',
        store=True,
        digits=(10, 2),
        compute='_compute_arredondamento'
    )

    round_total_fmt = fields.Char(
        string=u'Total',
        default='',
        compute='_compute_arredondamento'
    )

    #sequence = fields.Integer(
    #    string=u'Sequence',
    #)

    rate = fields.Float(
        digits=(18, 11),
    )

    amount = fields.Float(
        digits=(18, 11),
    )

    quantity = fields.Float(
        digits=(18, 11),
    )

    total = fields.Float(
        digits=(18, 2),
        compute='_compute_total',
        store=True,
    )

    # A slip de autonomo, utiliza esse modelo, entretanto nao eh um model
    # payslip, como todos os processos no odoo setam esse campo por código
    # nao tem necessidade de ser obrigatorio e caso esse campo for pra view,
    # deve ser tratado na visao a obrigatoriedade ndo campo
    slip_id = fields.Many2one(
        comodel_name='hr.payslip',
        required=False,
    )

    slip_autonomo_id = fields.Many2one(
        string=u'Holerite do Autonomo',
        comodel_name='hr.payslip.autonomo',
    )

    @api.depends('rate', 'amount', 'quantity')
    def _compute_total(self):
        for linha in self:
            total = Decimal(linha.amount or 0)
            total *= Decimal(linha.quantity or 0)
            total *= Decimal(linha.rate or 0)
            total /= 100
            total = total.quantize(Decimal('0.01'))
            linha.total = total

    @api.depends('total')
    def _compute_arredondamento(self):
        for linha in self:
            linha.round_amount = linha.amount
            linha.round_total = linha.total
            linha.round_total_fmt = valor.formata_valor(linha.round_total)

    @api.multi
    @api.depends('category_id', 'total', 'amount')
    def _compute_valor_provento(self):
        for line in self:
            line.quantity_fmt = valor.formata_valor(line.quantity)
            if line.category_id.code in ['PROVENTO', 'FERIAS']:
                line.valor_provento = line.total
                line.valor_provento_fmt = \
                    valor.formata_valor(line.valor_provento)
            else:
                line.valor_provento = 0.00
                line.valor_provento_fmt = ''

    @api.multi
    @api.depends('category_id', 'total', 'amount')
    def _compute_valor_deducao(self):
        for line in self:
            if line.category_id.code in ['DEDUCAO', 'INSS', 'IRPF']:
                line.valor_deducao = line.total
                line.valor_deducao_fmt = \
                    valor.formata_valor(line.valor_deducao)
            else:
                line.valor_deducao = 0.00
                line.valor_deducao_fmt = ''

    @api.onchange('salary_rule_id')
    def _onchange_salary_rule_id(self):
        for line in self:
            if line.salary_rule_id and line.salary_rule_id.code:
                line.code = line.salary_rule_id.code
                line.category_id = line.salary_rule_id.category_id
            else:
                line.code = ''
                line.category_id = False

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        """
        Setar o employee na linha baseado no contrato
        """
        for line in self:
            if line.contract_id and line.contract_id.employee_id:
                line.employee_id = line.contract_id.employee_id

    quantity_fmt = fields.Char(
        string=u'Quantidade',
        compute=_compute_valor_provento,
        default='',
    )

    valor_provento = fields.Float(
        string=u'Provento',
        compute=_compute_valor_provento,
        default=0.00,
    )

    valor_provento_fmt = fields.Char(
        string=u'Provento',
        compute=_compute_valor_provento,
        default='',
    )

    valor_deducao = fields.Float(
        string=u'Dedução',
        compute=_compute_valor_deducao,
        default=0.00,
    )

    valor_deducao_fmt = fields.Char(
        string=u'Dedução',
        compute=_compute_valor_deducao,
        default='',
    )

    partner_id = fields.Many2one(
        string=u'Beneficiário',
        comodel_name='res.partner',
    )

    reference = fields.Char(
        string=u'Referência',
    )
