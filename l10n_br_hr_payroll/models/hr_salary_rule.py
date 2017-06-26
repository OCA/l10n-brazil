# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

import openerp.addons.decimal_precision as dp
from openerp import api
from openerp import fields, models, _
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from pybrasil.python_pt_BR import python_pt_BR
    from pybrasil.valor.decimal import Decimal

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

    sequence = fields.Float(
        string=u'Sequence',
    )
    compoe_base_INSS = fields.Boolean(
        string=u'Compõe Base INSS',
    )

    compoe_base_IR = fields.Boolean(
        string=u'Compõe Base IR',
    )

    compoe_base_FGTS = fields.Boolean(
        string=u'Compõe Base FGTS',
    )

    calculo_nao_padrao = fields.Boolean(
        string=u'Usar Cálculo Não Padrão'
    )

    custom_amount_select = fields.Selection(
        selection=[('percentage', 'Percentage (%)'),
                   ('fix', 'Fixed Amount'),
                   ('code', 'Python Code')],
        default='code'
    )

    custom_amount_fix = fields.Float(
        digits_compute=dp.get_precision('Payroll'),
    )

    custom_amount_percentage = fields.Float(
        digits_compute=dp.get_precision('Payroll Rate'),
        help='For example, enter 50.0 to apply a percentage of 50%'
    )
    custom_quantity = fields.Char(
        help="It is used in computation for percentage and fixed amount."
             "For e.g. A rule for Meal Voucher having fixed amount of 1€ per "
             "worked day can have its quantity defined in expression like "
             "worked_days.WORK100.number_of_days."
    )

    custom_amount_python_compute = fields.Text('Python Code')

    custom_amount_percentage_base = fields.Char(
        required=False,
        readonly=False,
        help='result will be affected to a variable'
    )

    @api.multi
    def compute_rule(self, rule_id, localdict):
        rule = self.browse(rule_id)
        if not rule.calculo_nao_padrao:
            if rule.amount_select != 'code':
                return super(HrSalaryRule, self).compute_rule(rule_id,
                                                              localdict)

            codigo_python = python_pt_BR(rule.amount_python_compute or '',
                                         CALCULO_FOLHA_PT_BR)
        else:
            if rule.custom_amount_select == 'code':
                codigo_python = python_pt_BR(
                    rule.custom_amount_python_compute or '',
                    CALCULO_FOLHA_PT_BR)
            elif rule.custom_amount_select == 'fix':
                try:
                    return rule.custom_amount_fix, Decimal(
                        safe_eval(rule.custom_quantity, localdict)), 100.0
                except:
                    raise osv.except_osv(_('Error!'), _(
                        'Wrong quantity defined for salary rule %s (%s).') % (
                            rule.name, rule.code))
            elif rule.custom_amount_select == 'percentage':
                try:
                    return (
                        Decimal(
                            safe_eval(
                                rule.custom_amount_percentage_base, localdict
                            )
                        ), float(
                            safe_eval(rule.custom_quantity, localdict)
                        ), rule.custom_amount_percentage
                    )
                except:
                    raise osv.except_osv(
                        _('Error!'), _(
                            'Wrong percentage base or quantity defined for '
                            'salary rule %s (%s).') % (rule.name, rule.code)
                    )

        if codigo_python:
            if True:  # try:
                for variavel in localdict:
                    if isinstance(localdict[variavel], float):
                        localdict[variavel] = Decimal(localdict[variavel] or 0)
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
            # except:
            #     msg = _('Wrong python code defined for salary rule %s (%s).')
            #     raise ValidationError(msg % (rule.name, rule.code))

    @api.multi
    def satisfy_condition(self, rule_id, localdict):
        rule = self.browse(rule_id)

        if rule.condition_select != 'python':
            return super(HrSalaryRule, self).satisfy_condition(rule_id,
                                                               localdict)

        codigo_python = python_pt_BR(rule.condition_python or '',
                                     CALCULO_FOLHA_PT_BR)

        try:
            safe_eval(codigo_python, localdict, mode='exec', nocopy=True)
            return 'result' in localdict and localdict['result'] or False

        except:
            msg = _('Wrong python condition defined for salary rule %s (%s).')
            raise UserError(msg % (rule.name, rule.code))

    tipo_media = fields.Selection(
        selection=[
            ('valor', 'Valor'),
            ('quantidade', 'Quantidade'),
        ],
        string='Tipo de Média da Rubrica',
    )
