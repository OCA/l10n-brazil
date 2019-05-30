# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _

UTILIZACAO_EPC = [
    ('0', 'Não se aplica'),
    ('1', 'Não implementa'),
    ('2', 'Implementa'),
]
EFICIENCIA_EPC = [
    ('S', 'Sim'),
    ('N', 'Não'),
]
UTILIZACAO_EPI = [
    ('0', 'Não se aplica'),
    ('1', 'Não utilizado'),
    ('2', 'utilizado'),
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
        help=u'Nome Layout: utilizEPC - Tamanho: Até 1 Caracteres - '
             u'O empregador implementa medidas de proteção coletiva (EPC) '
             u'para eliminar ou reduzir a exposição dos trabalhadores '
             u'ao fator de risco?',
    )
    eficiencia_epc = fields.Selection(
        string=u'EPCs são eficientes?',
        selection=EFICIENCIA_EPC,
        help=u'Nome Layout: eficEpc - Tamanho: Até 1 Caracteres - Os EPCs são'
             u' eficazes na neutralização dos riscos ao trabalhador?',
    )
    utilizacao_epi = fields.Selection(
        string=u'Utilização de EPI',
        selection=UTILIZACAO_EPI,
        help=u'Nome Layout: utilizEPI - Tamanho: Até 1 Caracteres - Utilização'
             u' de EPI?',
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
            if record.utilizacao_epc and record.utilizacao_epi:
                utilizacao_epc = dict(UTILIZACAO_EPC)
                utilizacao_epi = dict(UTILIZACAO_EPI)
                record.name = 'EPC: {} - EPI: {} - Qtd: {}'.format(
                    utilizacao_epc[record.utilizacao_epc],
                    utilizacao_epi[record.utilizacao_epi],
                    len(record.epi_ids)
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
        help=u'Nome Layout: caEPI - Tamanho: Até 20 Caracteres - Certificado'
             u' de Aprovação do EPI.',
    )
    desc_epi = fields.Text(
        string=u'Descrição do EPI',
        size=999,
        help=u'Nome Layout: dscEPI - Tamanho: Até 999 Caracteres - Descrição'
             u' do EPI.',
    )
    eficiencia_epi = fields.Selection(
        string=u'Eficiência da Neutralização',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: eficEpi - Tamanho: Até 1 Caracteres - O EPI é '
             u'eficaz na neutralização do risco ao trabalhador?',
    )
    med_protecao_coletiva = fields.Selection(
        string=u'Medida de Proteção Coletiva',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: medProtecao - Tamanho: Até 1 Caracteres - Foi '
             u'tentada a implementação de medidas de proteção coletiva, '
             u'de caráter administrativo ou de organização, optando-se pelo '
             u'EPI por inviabilidade técnica, insuficiência ou interinidade, '
             u'ou ainda em caráter complementar ou emergencial?',
    )
    cond_funcionamento = fields.Selection(
        string=u'Condições de funcionamento ajustadas',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: condFuncto - Tamanho: Até 1 Caracteres - Foram '
             u'observadas as condições de funcionamento do EPI ao longo do '
             u'tempo, conforme especificação técnica do fabricante nacional '
             u'ou importador, ajustadas às condições de campo?',
    )
    uso_ininterrupto = fields.Selection(
        string=u'Uso Ininterrupto',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: usoInint - Tamanho: Até 1 Caracteres - Foi '
             u'observado o uso ininterrupto do EPI ao longo do tempo, '
             u'conforme especificação técnica do fabricante nacional ou '
             u'importador, ajustadas às condições de campo?',
    )
    prazo_validade_certificado_epi = fields.Selection(
        string=u'Prazo Validade do Certificado',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: przValid - Tamanho: Até 1 Caracteres - Foi '
             u'observado o prazo de validade do Certificado de Aprovação - '
             u'CA do MTb no momento da compra do EPI?',
    )
    periodicidade_troca = fields.Selection(
        string=u'Periodicidade de Troca',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: periodicTroca - Tamanho: Até 1 Caracteres - '
             u'É observada a periodicidade de troca definida pelo fabricante'
             u' nacional ou importador e/ou programas ambientais, '
             u'comprovada mediante recibo assinado pelo usuário '
             u'em época própria?',
    )
    higienizacao = fields.Selection(
        string=u'Higienização',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        help=u'Nome Layout: higienizacao - Tamanho: Até 1 Caracteres - '
             u'É observada a higienização conforme orientação do '
             u'fabricante nacional ou importador?',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            if record.certificado_aprovacao and record.desc_epi:
                record.name = '{} - {}'.format(
                    record.certificado_aprovacao, record.desc_epi
                )
