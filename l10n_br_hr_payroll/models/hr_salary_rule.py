# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import fields, models, exceptions, _
from openerp.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from pybrasil.python_pt_BR import python_pt_BR
    # from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')


CALCULO_FOLHA_PT_BR = {
    u'resultado': 'result',
    u'valor': 'result',
    u'taxa': 'result_rate',
    u'aliquota': 'result_rate',
    u'alíquota': 'result_rate',
    u'quantidade': 'result_qty',
    u'quant': 'result_qty',
    u'qtd': 'result_qty',
    u'qtde': 'result_qty',
}


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    compoe_base_INSS = fields.Boolean(
        string=u'Compõe Base INSS',
    )

    compoe_base_IR = fields.Boolean(
        string=u'Compõe Base IR',
    )

    compoe_base_FGTS = fields.Boolean(
        string=u'Compõe Base FGTS',
    )

    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        rule = self.browse(cr, uid, rule_id, context=context)

        if rule.amount_select != 'code':
            return super(HrSalaryRule, self).compute_rule(cr, uid, rule_id,
                                                          localdict,
                                                          context=context)

        codigo_python = python_pt_BR(rule.amount_python_compute or '',
                                     CALCULO_FOLHA_PT_BR)

        try:
            safe_eval(codigo_python, localdict, mode='exec', nocopy=True)
            result = localdict['result']

            if 'result_qty' in localdict:
                result_qty = localdict['result_qty']
            else:
                result_qty = 1

            if 'result_rate' in localdict:
                result_rate = localdict['result_rate']
            else:
                result_rate = 100

            return result, result_qty, result_rate

        except:
            raise exceptions.UserError(
                _('Wrong python code defined for salary rule %s (%s).') % \
                (rule.name, rule.code))

    def satisfy_condition(self, cr, uid, rule_id, localdict, context=None):
        rule = self.browse(cr, uid, rule_id, context=context)

        if rule.condition_select != 'python':
            return super(HrSalaryRule, self).satisfy_condition(cr, uid, rule_id,
                                                               localdict,
                                                               context=context)

        codigo_python = python_pt_BR(rule.condition_python or '',
                                     CALCULO_FOLHA_PT_BR)

        try:
            safe_eval(codigo_python, localdict, mode='exec', nocopy=True)
            return 'result' in localdict and localdict['result'] or False

        except:
            raise exceptions.UserError(
                _('Wrong python condition defined for salary rule %s (%s).') % \
                 (rule.name, rule.code))
