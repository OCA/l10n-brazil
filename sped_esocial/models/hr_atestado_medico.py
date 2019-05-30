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
        help=u'Nome Layout: codCNES - Tamanho: Até 7 Caracteres - Código da'
             u' unidade de atendimento médico no Cadastro Nacional de'
             u' Estabelecimento de Saúde.',
    )
    data_atendimento = fields.Datetime(
        string=u'Data Atendimento',
        help=u'Nome Layout: dtAtendimento - Data do atendimento.',
    )
    duracao_tratamento = fields.Integer(
        string=u'Duração do Tratamento',
        size=4,
        help=u'Nome Layout: durTrat - Tamanho: Até 4 Caracteres - Duração '
             u'estimada do tratamento, em dias.',
    )
    indicativo_internacao = fields.Selection(
        string=u'Indicativo Internação',
        selection=SIM_NAO,
        help=u'Nome Layout: indAfast - Tamanho: Até 1 Caracteres - Indicativo'
             u' de afastamento do trabalho durante o tratamento: '
             u'S - Sim; N - Não.',
    )
    descricao_lesao_id = fields.Many2one(
        string=u'Descrição da Lesão',
        comodel_name='sped.natureza_lesao',
    )
    desc_complementar_lesao = fields.Text(
        string=u'Descrição Complementar da Lesão',
        size=200,
        help=u'Nome Layout: dscCompLesao - Tamanho: Até 200 Caracteres - '
             u'Descrição complementar da lesão.',
    )
    diagnostico_provavel = fields.Char(
        string=u'Diagnóstico Provável',
        size=100,
        help=u'Nome Layout: diagProvavel - Tamanho: Até 100 Caracteres - '
             u'Diagnóstico Provável.',
    )
    cod_cid = fields.Char(
        string=u'Código CID',
        size=4,
        help=u'Nome Layout: codCID - Tamanho: Até 4 Caracteres - Informar o'
             u' código na tabela de Classificação Internacional de Doenças - '
             u'CID. Validação: Deve ser preenchido com caracteres '
             u'alfanuméricos conforme opções constantes na tabela CID.',
    )
    observacoes = fields.Char(
        string=u'Observações',
        size=255,
        help=u'Nome Layout: observacao - Tamanho: Até 255 Caracteres - '
             u'Observação',
    )
    nome_emitente = fields.Char(
        string=u'Nome do Emitente',
        size=70,
        help=u'Nome Layout: nmEmit - Tamanho: Até 70 Caracteres - '
             u'Nome do médico/dentista que emitiu o atestado.',
    )
    identidade_orgao_classe = fields.Selection(
        string=u'Identificação do Orgão',
        selection=IDE_OC,
        help=u'Nome Layout: ideOC - Tamanho: Até 1 Caracteres - '
             u'Órgão de classe: 1 - Conselho Regional de Medicina (CRM); '
             u'2 - Conselho Regional de Odontologia (CRO); '
             u'3 - Registro do Ministério da Saúde (RMS).',
    )
    num_inscricao_orgao = fields.Char(
        string=u'Número Inscrição do Orgão',
        size=14,
        help=u'Nome Layout: nrOC - Tamanho: Até 14 Caracteres - Número de '
             u'Inscrição no órgão de classe.',
    )
    uf_orgao_classe = fields.Selection(
        string=u'UF do Orgão',
        selection=UF,
        help=u'Nome Layout: ufOC - Tamanho: Até 2 Caracteres - Sigla da UF '
             u'do órgão de classe',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - {} - {}'.format(
                record.data_atendimento, record.descricao_lesao_id.nome,
                record.contract_id.name
            )
