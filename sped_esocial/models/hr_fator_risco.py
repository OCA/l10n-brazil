# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _

TP_AVAL = [
    (1, u'Critério Quantitativo'),
    (2, u'Critério Qualitativo'),
]

UN_MED = [
    (1, u'dose diária de ruído (número adimensional) Q=5'),
    (2, u'decibel linear(dB(linear))'),
    (3, u'decibel(C)(dB(C))'),
    (4, u'decibel(A)(dB(A))'),
    (5, u'quilocaloria por hora(kcal / h)'),
    (6, u'gray(Gy)'),
    (7, u'sievert(Sv)'),
    (8, u'quilograma - força por centímetro quadrado(kgf / cm2)'),
    (9, u'metro por segundo ao quadrado(m / s2)'),
    (10, u'metro por segundo elevado a 1,75(m/s1,75)'),
    (11, u'parte de vapor ou gás por milhão de partes de ar contaminado(ppm)'),
    (12, u'miligrama por metro cúbico de ar(mg / m3)'),
    (13, u'fibra por centímetro cúbico(f / cm3)'),
    (14, u'grau Celsius(oC)'),
    (15, u'metro por segundo(m / s) Página'),
    (16, u'porcentual( %)'),
    (17, u'lux(lx)'),
    (18, u'unidade formadora de colônias por metro cúbico(ufc / m3)'),
    (19, u'dose diária'),
    (20, u'dose mensal'),
    (21, u'dose trimestral'),
    (22, u'dose anual'),
    (23, u'hertz(Hz)'),
    (24, u'gigahertz(GHz)'),
    (25, u'quilohertz(kHz)'),
    (26, u'watt por metro quadrado(W / m2)'),
    (27, u'ampère por metro(A / m)'),
    (28, u'militesla(mT)'),
    (29, u'microtesla(μT)'),
    (30, u'miliampère(mA)'),
    (31, u'quilovolt por metro(kV / m)'),
    (32, u'volt por metro(V / m)'),
    (33, u'minuto(min)'),
    (34, u'hora(h)'),
    (35, u'joule por metro quadrado(J / m2)'),
    (36, u'milijoule por centímetro quadrado(mJ / cm2)'),
    (37, u'milisievert(mSv) - dose efetiva anual - corpo inteiro'),
    (38, u'atmosfera(atm)'),
    (39, u'milhão de partículas por decímetro cúbico(mppdc)'),
    (40, u'nanômetro(nm)'),
    (41, u'miliwatt(mW)'),
    (42, u'watt(W)'),
    (43, u'umidade relativa do ar(UR( %))'),
    (44, u'decibel(A)(dB(A)) NEN Q = 3'),
    (45, u'milisievert(mSv) - dose equivalente anual - cristalino'),
    (46, u'milisievert(mSv) - dose equivalente anual - pele'),
    (47, u'milisievert(mSv) - dose equivalente anual - mãos e pés.'),
]


class HrFatorRisco(models.Model):
    _name = 'hr.fator.risco'
    _description = u'Fatores de Risco no Trabalho'

    name = fields.Char(
        compute='_compute_name'
    )
    cod_fator_risco_id = fields.Many2one(
        string=u'Código do Fator de Risco',
        comodel_name='sped.fatores_meio_ambiente',
    )
    tp_avaliacao = fields.Selection(
        strin=u'Tipo de Avaliação',
        selection=TP_AVAL,
    )
    intensidade_concentracao = fields.Integer(
        string=u'Intensidade ou Concentração',
        size=10,
    )
    limite_tolerancia = fields.Integer(
        string=u'Limite de Tolerância',
        size=10,
    )
    unidade_medida = fields.Selection(
        string=u'Unidade de Medida',
        selection=UN_MED,
    )
    tec_medicao = fields.Char(
        string=u'Técnica Medição',
        size=40,
    )
    insalubridade = fields.Selection(
        string=u'Insalubridade',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    periculosidade = fields.Selection(
        string=u'Periculosidade',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    aposentadoria_especial = fields.Selection(
        string=u'Aposentadoria Especial',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    epc_id = fields.Many2one(
        string='Equipamentos de Proteção Coletiva',
        comodel_name='hr.equipamento.protecao.individual',
    )

    @api.model
    def _compute_name(self):
        for record in self:
            if record.cod_fator_risco_id and record.tp_avaliacao:
                tp_aval = dict(TP_AVAL)

                record.name = '{} - {}'.format(
                    record.cod_fator_risco_id.name, tp_aval[record.tp_avaliacao]
                )
