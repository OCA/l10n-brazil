# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning

TP_EXAME = [
    ('0', 'Exame médico admissional'),
    ('1', 'Exame médico periódico, conforme NR7 do MTb e/ou planejamento do PCMSO'),
    ('2', 'Exame médico de retorno ao trabalho'),
    ('3', 'Exame médico de mudança de função'),
    ('4', 'Exame médico de monitoração pontual, não enquadrado nos demais casos'),
    ('9', 'Exame médico demissional'),
]

RESULT_ASO = [
    ('1', 'Apto'),
    ('2', 'Inapto'),
]

UF = [
    ('AC', 'Acre'),
    ('AL', 'Alagoas'),
    ('AP', 'Amapá'),
    ('AM', 'Amazonas'),
    ('BA', 'Bahia'),
    ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'),
    ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'),
    ('PA', 'Pará'),
    ('PB', 'Paraíba'),
    ('PR', 'Paraná'),
    ('PE', 'Pernambuco'),
    ('PI', 'Piauí'),
    ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grando do Norte'),
    ('RS', 'Rio Grando do Sul'),
    ('RO', 'Rondônioa'),
    ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'),
    ('SE', 'Sergipe'),
    ('TO', 'Tocantins'),
]


class HrSaudeTrabalhador(models.Model):
    _name = 'hr.saude.trabalhador'
    _description = u'Monitoramento Saúde do Trabalhador'
    _order = 'contract_id'
    _sql_constraints = [
        ('inicio_condicao_contract_id',
         'unique(inicio_condicao, contract_id)',
         'Este contrato já possiu um relatório de '
         'Condições Ambientais de Trabalho com esta data de início!'
         )
    ]

    state = fields.Selection(
        string='Situação',
        selection=[
            ('0', 'Inativo'),
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        default='0',
        compute='_compute_state',
    )
    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
    )
    contract_id = fields.Many2one(
        string=u'Contrato de Trabalho',
        comodel_name='hr.contract',
        domain=[('situacao_esocial', '=', 1)]
    )
    tipo_exame_ocup = fields.Selection(
        string=u'Tipo de Exame Ocupacional',
        selection=TP_EXAME,
        help=u'Nome layout: tpExameOcup - Tamanho: Até 1 Caracteres - Tipo do'
             u' exame médico ocupacional, conforme opções abaixo: '
             u'0 - Exame médico admissional; '
             u'1 - Exame médico periódico, conforme NR7 do MTb e/ou '
             u'planejamento do PCMSO; '
             u'2 - Exame médico de retorno ao trabalho; '
             u'3 - Exame médico de mudança de função; '
             u'4 - Exame médico de monitoração pontual, '
             u'não enquadrado nos demais casos; '
             u'9 - Exame médico demissional. ',
    )
    data_aso = fields.Date(
        string=u'Data emissão',
        help=u'Nome layout: dtAso - Data de emissão do ASO. Validação: Deve ser'
             u' uma data válida, igual ou anterior à data atual e '
             u'igual ou posterior à data de início da obrigatoriedade '
             u'deste evento para o empregador no eSocial.',
    )
    result_aso = fields.Selection(
        string=u'Resultado do Aso',
        selection=RESULT_ASO,
        help=u'Nome layout: resAso - Tamanho: Até 1 Caracteres - Resultado '
             u'do ASO, conforme opções abaixo: 1 - Apto; 2 - Inapto.',
    )
    exame_aso_ids = fields.One2many(
        string=u'Exames ASO',
        comodel_name='hr.exame.aso',
        inverse_name='hr_saude_trabalhador_id',
    )
    cpf_medico = fields.Char(
        string=u'CPF',
        size=11,
        help=u'Nome layout: cpfMed - Tamanho: Até 11 Caracteres - Preencher '
             u'com o CPF do médico emitente do ASO.',
    )
    nis_medico = fields.Char(
        string=u'Número de Identificação Social - NIS',
        size=11,
        help=u'Nome layout: nisMed - Tamanho: Até 11 Caracteres - Preencher '
             u'com o Número de Identificação Social - NIS do médico emitente '
             u'do ASO, o qual pode ser o PIS, PASEP ou NIT.',
    )
    nome_medico = fields.Char(
        string=u'Nome',
        size=70,
        help=u'Nome layout: nmMed - Tamanho: Até 70 Caracteres - Preencher '
             u'com o nome do médico emitente do ASO.',
    )
    num_crm = fields.Char(
        string=u'Número do CRM',
        size=8,
        help=u'Nome layout: nrCRM - Tamanho: Até 8 Caracteres - Número de '
             u'inscrição do médico emitente do ASO no '
             u'Conselho Regional de Medicina (CRM).',
    )
    uf_crm = fields.Selection(
        string=u'UF do CRM',
        selection=UF,
        help=u'Nome layout: ufCRM - Tamanho: Até 2 Caracteres - Preencher '
             u'com a sigla da UF de expedição do CRM.',
    )
    cpf_resp_pcmso = fields.Char(
        string=u'CPF do Responsável do PCMSO',
        size=11,
        help=u'Nome layout: cpfResp - Tamanho: Até 11 Caracteres - Preencher '
             u'com o CPF do médico responsável/coordenador do PCMSO.',
    )
    nome_resp_pcmso = fields.Char(
        string=u'Nome',
        size=70,
        help=u'Nome layout: nmResp - Tamanho: Até 70 Caracteres - Preencher '
             u'com o nome do médico responsável/coordenador do PCMSO.',
    )
    num_crm_pcmso = fields.Char(
        string=u'Número do CRM do PCMSO',
        size=8,
        help=u'Nome layout: nrCRM - Tamanho: Até 8 Caracteres - Número de '
             u'inscrição do médico responsável/coordenador do PCMSO no CRM.',
    )
    uf_crm_pcmso = fields.Selection(
        string=u'UF do CRM do PCMSO',
        selection=UF,
        help=u'Nome layout: ufCRM - Tamanho: Até 2 Caracteres - Preencher '
             u'com a sigla da UF de expedição do CRM.',
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.saude.trabalhador',
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.saude.trabalhador',
    )

    @api.model
    def _compute_name(self):
        for record in self:
            if record.tipo_exame_ocup and record.contract_id:
                tp_exame = dict(TP_EXAME)

                record.name = '{} - {}'.format(
                    record.contract_id.name, tp_exame[record.tipo_exame_ocup]
                )

    @api.multi
    def _compute_state(self):
        for record in self:
            if not record.sped_intermediario_id:
                record.state = 0
            else:
                record.state = record.sped_intermediario_id.situacao_esocial

    def gerar_intermediario(self):
        if not self.sped_intermediario_id:
            vals = {
                'company_id': self.contract_id.company_id.id if
                self.contract_id.company_id.eh_empresa_base else
                self.contract_id.company_id.matriz.id,
                'hr_saude_trabalhador_id': self.id,
            }
            self.sped_intermediario_id = self.env[
                'sped.hr.saude.trabalhador'].create(vals)
            self.sped_intermediario_id.gerar_registro()

    @api.multi
    def button_enviar_esocial(self):
        self.gerar_intermediario()

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.contract_id.employee_id

    @api.multi
    def unlink(self):
        for record in self:
            for registro in record.sped_intermediario_id.sped_inclusao:
                if registro.situacao == '4':
                    raise Warning(
                        'Não é possível excluír um registro '
                        'que foi transmitido para o e-Social!'
                    )
            record.sped_intermediario_id.unlink()
            super(HrSaudeTrabalhador, record).unlink()
