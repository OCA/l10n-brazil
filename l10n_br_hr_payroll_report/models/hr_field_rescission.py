# -*- coding: utf-8 -*-
from openerp import models, fields, api


class HrFieldRescission(models.Model):
    _name = 'hr.field.rescission'
    _order = 'codigo ASC'

    codigo = fields.Float(
        string=u'Código',
        required=True,
    )
    codigo_fmt = fields.Char(
        string=u'Código',
        compute="_calcula_codigo_fmt",
        store=True,
    )
    descricao = fields.Char(
        string=u'descrição',
        required=True,
    )
    variaveis = fields.Char(
        string=u'Variáveis disponíveis',
        readonly=True,
        default='${DIAS_BASE} - ${DIAS_UTEIS} - ${FERIAS} - ${'
                'ABONO_PECUNIARIO} - ${DIAS_TRABALHADOS} - '
                '${PERIODO_FERIAS_VENCIDAS} - ${AVOS}'
    )
    rule = fields.One2many(
        string=u'Regras de Salário',
        comodel_name='hr.salary.rule',
        inverse_name='campo_rescisao',
        readonly=True,
    )
    name = fields.Char(
        string=u'Nome',
        compute="name_get",
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

    @api.one
    def name_get(self):
        name = ''
        if self.codigo_fmt:
            name += str(self.codigo_fmt)
        if self.descricao:
            if self.codigo_fmt:
                name += '-'
            name += self.descricao
        return self.id, name
