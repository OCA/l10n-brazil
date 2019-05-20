# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import fields, models, api

SIM_NAO = [
    ('S', 'Sim'),
    ('N', 'Não'),
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

IDE_OC = [
    (1, 'Conselho Regional de Medicina (CRM)'),
    (4, 'Conselho Regional de Engenharia e Agronomia (CREA)'),
    (9, 'Outros'),
]


class HrAtestadoMedico(models.Model):
    _name = 'hr.atestado.medico'
    _order = 'data_atendimento'
    _sql_constraints = [
        ('data_atendimento_contract_id_descricao_lesao_id',
         'unique(data_atendimento, contract_id, descricao_lesao_id)',
         'Este contrato já possiu um atestado com esta data!'
         )
    ]

    name = fields.Char(
        compute='_compute_name',
    )
    acidente_trabalho_id = fields.Many2one(
        comodel_name='hr.comunicacao.acidente.trabalho',
    )
    contract_id = fields.Many2one(
        string=u'Contrato de Trabalho',
        comodel_name='hr.contract',
    )
    cod_cnes = fields.Char(
        string=u'Código CNES',
        size=7,
    )
    data_atendimento = fields.Datetime(
        string=u'Data Atendimento',
    )
    duracao_tratamento = fields.Integer(
        string=u'Duração do Tratamento',
        size=4,
    )
    indicativo_internacao = fields.Selection(
        string=u'Indicativo Internação',
        selection=SIM_NAO,
    )
    descricao_lesao_id = fields.Many2one(
        string=u'Descrição da Lesão',
        comodel_name='sped.natureza_lesao',
    )
    desc_complementar_lesao = fields.Text(
        string=u'Descrição Complementar da Lesão',
        size=200,
    )
    diagnostico_provavel = fields.Char(
        string=u'Diagnóstico Provável',
        size=100,
    )
    cod_cid = fields.Char(
        string=u'Código CID',
        size=4,
    )
    observacoes = fields.Char(
        string=u'Observações',
        size=255,
    )
    nome_emitente = fields.Char(
        string=u'Nome do Emitente',
        size=70,
    )
    identidade_orgao_classe = fields.Selection(
        string=u'Identificação do Orgão',
        selection=IDE_OC,
    )
    num_inscricao_orgao = fields.Char(
        string=u'Número Inscrição do Orgão',
        size=14,
    )
    uf_orgao_classe = fields.Selection(
        string=u'UF do Orgão',
        selection=UF,
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - {} - {}'.format(
                record.data_atendimento, record.descricao_lesao,
                record.contract_id
            )
