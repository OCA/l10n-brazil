# -*- coding: utf-8 -*-
from openerp import models, fields, api


class HrFieldRescission(models.Model):
    _name = 'hr.campos.rescisao'
    _order = 'codigo'

    codigo = fields.Float(
        string=u'Código',
        required=True,
    )
    codigo_fmt = fields.Char(
        string=u'Código',
        compute="_calcula_codigo_fmt",
        store=True,
    )

    @api.multi
    @api.depends('codigo')
    def _calcula_codigo_fmt(self):
        for registro in self:
            if registro.codigo == int(registro.codigo):
                registro.codigo_fmt = "%.0f" % registro.codigo
            else:
                registro.codigo_fmt = "%.1f" % registro.codigo

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
