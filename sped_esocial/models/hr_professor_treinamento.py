# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models

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
        help=u'Nome Layout: cpfProf - Tamanho: Até 11 Caracteres - Preencher '
             u'com o CPF do profissional responsável pelo '
             u'treinamento/capacitação/exercício simulado.',
    )
    nome = fields.Char(
        string=u'Nome',
        size=70,
        help=u'Nome Layout: nmProf - Tamanho: Até 70 Caracteres - Nome do '
             u'profissional responsável pelo '
             u'treinamento/capacitação/exercício simulado.',
    )
    tipo_vinculo = fields.Selection(
        string=u'Tipo de vínculo',
        selection=TIP_VINC,
        help=u'Nome Layout: ptProf - Tamanho: Até 1 Caracteres - '
             u'O treinamento/capacitação/exercício simulado foi ministrado por',
    )
    formacao = fields.Text(
        string=u'Formação',
        size=255,
        help=u'Nome Layout: formProf - Tamanho: Até 255 Caracteres - Formação '
             u'do profissional responsável pelo '
             u'treinamento/capacitação/exercício simulado '
             u'(seja acadêmica, prática ou outra forma).',
    )
    cod_CBO = fields.Char(
        string=u'Classificação Brasileira de Ocupação (CBO)',
        size=6,
        help=u'Nome Layout: codCBO - Tamanho: Até 6 Caracteres - Informar a '
             u'Classificação Brasileira de Ocupação - CBO referente à formação'
             u' do profissional responsável pelo '
             u'treinamento/capacitação/exercício simulado. '
             u'Validação: Deve ser um código existente na tabela de CBO, '
             u'com 6 (seis) posições.',
    )
    nacionalidade = fields.Selection(
        string=u'Nacionalidade',
        selection=NACIONALIDADE,
        help=u'Nome Layout: nacProf - Tamanho: Até 1 Caracteres - Indicativo '
             u'da nacionalidade do profissional responsável pelo '
             u'treinamento/capacitação/exercício simulado',
    )

    @api.model
    def _compute_name(self):
        for record in self:
            record.name = 'Professor: {}'.format(record.nome)
