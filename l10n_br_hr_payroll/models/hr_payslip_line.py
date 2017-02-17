# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.valor import formata_valor

except ImportError:
    _logger.info('Cannot import pybrasil')


class HrPayslipeLine(models.Model):
    _inherit = "hr.payslip.line"

    quantity_fmt = fields.Char(
        string=u'Quantidade',
        compute='_compute_valores',
    )
    valor_provento = fields.Float(
        string=u'Provento',
        compute='_compute_valores',
    )
    valor_provento_fmt = fields.Char(
        string=u'Provento',
        compute='_compute_valores',
    )
    valor_deducao = fields.Float(
        string=u'Dedução',
        compute='_compute_valores',
    )
    valor_deducao_fmt = fields.Char(
        string=u'Dedução',
        compute='_compute_valores',
    )
    quantidade = fields.Float(
        string=u'Quantidade',
        compute='_compute_valores',
    )
    quantidade_fmt = fields.Char(
        string=u'Quantidade',
        compute='_compute_valores',
    )
    base = fields.Float(
        string=u'Base',
        compute='_compute_valores',
    )
    base_fmt = fields.Char(
        string=u'Base',
        compute='_compute_valores',
    )
    percentual = fields.Float(
        string=u'Percentual',
        compute='_compute_valores',
    )
    percentual_fmt = fields.Char(
        string=u'Percentual',
        compute='_compute_valores',
    )
    valor = fields.Float(
        string=u'Valor',
        compute='_compute_valores',
    )
    valor_fmt = fields.Char(
        string=u'Valor',
        compute='_compute_valores',
    )

    @api.model
    def _compute_valores(self):
        for linha in self:
            linha.quantidade = D(linha.quantity or 0)
            linha.base = D(linha.amount or 0)
            linha.percentual = D(linha.rate or 0)
            linha.valor = D(linha.total or 0)

            linha.quantidade_fmt = formata_valor(linha.quantidade)
            linha.base_fmt = formata_valor(linha.base)
            linha.percentual_fmt = formata_valor(linha.percentual)
            linha.valor_fmt = formata_valor(linha.valor)

            linha.quantity_fmt = linha.quantidade_fmt
            linha.quantity_fmt = linha.quantidade_fmt

            linha.valor_provento = D(0)
            linha.valor_provento_fmt = ''
            linha.valor_deducao = D(0)
            linha.valor_deducao_fmt = ''

            if linha.salary_rule_id.category_id.code == "PROVENTO":
                linha.valor_provento = linha.valor
                linha.valor_provento_fmt = linha.valor_fmt

            elif linha.salary_rule_id.category_id.code in ["DEDUCAO"] \
                    or linha.salary_rule_id.code == "INSS" \
                    or linha.salary_rule_id.code == "IRPF":
                linha.valor_deducao = linha.valor
                linha.valor_deducao_fmt = linha.valor_fmt
