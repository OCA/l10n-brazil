# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrPayslipeLine(models.Model):
    _inherit = "hr.payslip.line"

    @api.model
    def _valor_provento(self):
        for record in self:
            record.quantity_fmt = valor.formata_valor(record.quantity)
            if record.salary_rule_id.category_id.code \
                    in ['PROVENTO', 'FERIAS']:
                record.valor_provento = record.total
                record.valor_provento_fmt = \
                    valor.formata_valor(record.valor_provento)
            else:
                record.valor_provento = 0.00
                record.valor_provento_fmt = ''

    @api.model
    def _valor_deducao(self):
        for record in self:
            if record.salary_rule_id.category_id.code in ["DEDUCAO"] \
                    or record.salary_rule_id.code == "INSS" \
                    or record.salary_rule_id.code == "IRPF":
                record.valor_deducao = record.total
                record.valor_deducao_fmt = \
                    valor.formata_valor(record.valor_deducao)
            else:
                record.valor_deducao = 0.00
                record.valor_deducao_fmt = ''

    quantity_fmt = fields.Char(
        string=u'Quantidade',
        compute=_valor_provento,
        default='',
    )

    valor_provento = fields.Float(
        string=u'Provento',
        compute=_valor_provento,
        default=0.00,
    )

    valor_provento_fmt = fields.Char(
        string=u'Provento',
        compute=_valor_provento,
        default='',
    )
    valor_deducao = fields.Float(
        string=u'Dedução',
        compute=_valor_deducao,
        default=0.00,
    )

    valor_deducao_fmt = fields.Char(
        string=u'Dedução',
        compute=_valor_deducao,
        default='',
    )
