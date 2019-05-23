# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning

TIP_VINC = [
    ('1', 'Profissional empregado do declarante'),
    ('2', 'Profissional sem vínculo de emprego/estatutário com o declarante'),
]

NACIONALIDADE = [
    ('1', 'Brasileiro'),
    ('2', 'Estrangeiro'),
]


class HrProfessorTreinamento(models.Model):
    _name = 'hr.professor.treinamento'
    _description = u'Identificação do Professor do Treinamento ou Capacitação'

    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
    )
    cpf = fields.Char(
        string=u'CPF',
        size=11,
    )
    nome = fields.Char(
        string=u'Nome',
        size=70,
    )
    tipo_vinculo = fields.Selection(
        string=u'Tipo de vínculo',
        selection=TIP_VINC,
    )
    formacao = fields.Text(
        string=u'Formação',
        size=255,
    )
    cod_CBO = fields.Char(
        string=u'Classificação Brasileira de Ocupação (CBO)',
        size=6,
    )
    nacionalidade = fields.Selection(
        string=u'Nacionalidade',
        selection=NACIONALIDADE,
    )

    @api.model
    def _compute_name(self):
        for record in self:
            record.name = 'Professor: {}'.format(record.nome)
