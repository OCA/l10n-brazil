# -*- coding: utf-8 -*-
from openerp import models, fields, api


class HrFieldRescission(models.Model):
    _name = 'hr.campos.rescisao'
    _order = 'codigo'

    codigo = fields.Integer(
        string=u'Código',
        required=True,
    )
    name = fields.Char(
        string=u'Descrição',
        required=True,
    )
    valor = fields.Float(
        string=u'Valor'
    )
    tipo = fields.Char(
        string=u'Tipo',
        required=True,
    )
    slip_id = fields.Many2one(
        comodel_name='hr.payslip',
        inverse_name='rescisao_ids',
        string=u'Holerite'
    )
