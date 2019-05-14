# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _

UTILIZACAO_EPC = [
    (0, 'Não se aplica'),
    (1, 'Não implementa'),
    (2, 'Implementa'),
]
EFICIENCIA_EPC = [
    ('S', 'Sim'),
    ('N', 'Não'),
]
UTILIZACAO_EPI = [
    (0, 'Não se aplica'),
    (1, 'Não utilizado'),
    (2, 'utilizado'),
]


class HrEquipamentoProtecaoIndividual(models.Model):
    _name = 'hr.equipamento.protecao.individual'
    _description = u'Equipamento Proteção Individual'

    name = fields.Char(
        compute='_compute_name',
    )
    utilizacao_epc = fields.Selection(
        string=u'Medidas de Proteção Coletiva (EPC)',
        selection=UTILIZACAO_EPC,
    )
    eficiencia_epc = fields.Selection(
        string=u'EPCs são eficientes?',
        selection=EFICIENCIA_EPC,
    )
    utilizacao_epi = fields.Selection(
        string=u'Utilização de EPI',
        selection=UTILIZACAO_EPI,
    )
    epi_ids = fields.Many2many(
        string=u'Equipamentos de Proteção Individual',
        comodel_name='hr.equipamento.protecao.individual.line',
        relation='hr_epc_hr_epi_rel',
        column1='hr_epc_id',
        column2='hr_epi_id'
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            if record.utilizacao_epc and record.eficiencia_epc and \
                    record.utilizacao_epi:
                utilizacao_epc = dict(UTILIZACAO_EPC)
                eficiencia_epc = dict(EFICIENCIA_EPC)
                utilizacao_epi = dict(UTILIZACAO_EPI)
                record.name = 'EPC: {} - Eficientes: {} - EPI: {}'.format(
                    utilizacao_epc[record.utilizacao_epc],
                    eficiencia_epc[record.eficiencia_epc],
                    utilizacao_epi[record.utilizacao_epi]
                )


class HrEquipamentoProtecaoIndividualLine(models.Model):
    _name = 'hr.equipamento.protecao.individual.line'
    _description = u'Equipamento Proteção Individual Linha'

    name = fields.Char(
        comodel_name='_compute_name',
    )
    certificado_aprovacao = fields.Char(
        string=u'Certificado de Aprovação',
        size=20,
    )
    desc_epi = fields.Text(
        string=u'Descrição do EPI',
        size=999,
    )
    eficiencia_epi = fields.Selection(
        string=u'Eficiência da Neutralização',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    med_protecao_coletiva = fields.Selection(
        string=u'Medida de Proteção Coletiva',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    uso_ininterrupto = fields.Selection(
        string=u'Uso Ininterrupto',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    prazo_validade_certificado_epi = fields.Selection(
        string=u'Prazo Validade do Certificado',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    periodicidade_troca = fields.Selection(
        string=u'Periodicidade de Troca',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    higienizacao = fields.Selection(
        string=u'Higienização',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            if record.certificado_aprovacao and record.desc_epi:
                record.name = '{} - {}'.format(
                    record.certificado_aprovacao, record.desc_epi
                )
