# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning

TP_CAT = [
    ('1', 'Inicial'),
    ('2', 'Reabertura'),
    ('3', 'Comunicação de Óbito'),
]

SIM_NAO = [
    ('S', 'Sim'),
    ('N', 'Não'),
]

EMISSOR_CAT = [
    ('1', 'Iniciativa do Empregador'),
    ('2', 'Ordem Judicial'),
    ('3', 'Determinação de Órgão Fiscalizador'),
]

TP_LOCAL = [
    ('1', 'Estabelecimento do Empregador no Brasil'),
    ('2', 'Estabelecimento do Empregador no Exterior'),
    ('3', 'Estabelecimento de Terceiros onde o Empregador presta Serviços'),
    ('4', 'Via Pública'),
    ('5', 'Área Rural'),
    ('6', 'Embarcação'),
    ('9', 'Outros'),
]


class HrComunicacaoAcidenteTrabalho(models.Model):
    _name = 'hr.comunicacao.acidente.trabalho'
    _description = u'Comunicação de Acidente de Trabalho'
    _order = 'data_acidente'
    _sql_constraints = [
        ('data_acidente_contract_id_tipo_acidente_id',
         'unique(data_acidente, contract_id, tipo_acidente)',
         'Este contrato já possiu um relatório com este '
         'acidente de trabalho com esta data!'
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
    data_acidente = fields.Datetime(
        string=u'Data do Acidente',
        help=u'Nome Layout: dtAcid - Data do Acidente.',
    )
    tipo_acidente = fields.Many2one(
        string=u'Tipo do Acidente',
        comodel_name='sped.codificacao_acidente_trabalho',
    )
    horas_trab_antes_acidente = fields.Char(
        string=u'Horas Trabalhadas Antes',
        size=4,
        help=u'Nome Layout: hrsTrabAntesAcid - Tamanho: Até 4 Caracteres - '
             u'Horas trabalhadas antes da ocorrência do acidente, '
             u'no formato HHMM.',
    )
    tipo_cat = fields.Selection(
        string='Tipo de CAT',
        selection=TP_CAT,
        help=u'Nome Layout: tpCat - Tamanho: Até 1 Caracteres - Tipo de CAT, '
             u'conforme opções abaixo: 1 - Inicial; 2 - Reabertura;'
             u' 3 - Comunicação de Óbito.',
    )
    ind_cat_obito = fields.Selection(
        string=u'Houve Óbito',
        selection=SIM_NAO,
        help=u'Nome Layout: indCatObito - Tamanho: Até 1 Caracteres - '
             u'Houve Óbito? S - Sim; N - Não.',
    )
    data_obito = fields.Date(
        string=u'Data do Óbito',
        help=u'Nome Layout: dtObito - Data do óbito.',
    )
    ind_comunicacao_policia = fields.Selection(
        string=u'Houve comunicação com a Polícia',
        selection=SIM_NAO,
        help=u'Nome Layout: indComunPolicia - Tamanho: Até 1 Caracteres - '
             u'Houve comunicação à autoridade policial? S - Sim; N - Não.',
    )
    cod_geradora_acidente = fields.Many2one(
        string=u'Código da Situação Geradora do Acidente',
        comodel_name='sped.situacao_geradora_acidente',
    )
    emissao_cat = fields.Selection(
        string=u'Emissor da CAT',
        selection=EMISSOR_CAT,
        help=u'Nome Layout: iniciatCat - Tamanho: Até 1 Caracteres - A CAT foi'
             u' emitida por: 1 - Iniciativa do empregador; 2 - Ordem judicial;'
             u' 3 - Determinação de órgão fiscalizador.',
    )
    obs = fields.Text(
        string=u'Observações',
        size=999,
        help=u'Nome Layout: obsCAT - Tamanho: Até 999 Caracteres - Observação',
    )
    tipo_local = fields.Selection(
        string=u'Tipo do Local',
        selection=TP_LOCAL,
        help=u'Nome Layout: tpLocal - Tamanho: Até 1 Caracteres - Tipo de '
             u'local do acidente: 1 - Estabelecimento do empregador no Brasil;'
             u' 2 - Estabelecimento do empregador no Exterior; '
             u'3 - Estabelecimento de terceiros onde o empregador'
             u' presta serviços; 4 - Via pública; 5 - Área rural; '
             u'6 - Embarcação; 9 - Outros.',
    )
    desc_local = fields.Text(
        string=u'Descrição',
        size=255,
        help=u'Nome Layout: dscLocal - Tamanho: Até 255 Caracteres - '
             u'Especificação do local do acidente (pátio, rampa de acesso,'
             u' posto de trabalho, etc.).',
    )
    cod_ambiente = fields.Many2one(
        string=u'Código do Ambiente',
        comodel_name='hr.ambiente.trabalho',
    )
    tipo_logradouro = fields.Many2one(
        string=u'TIpo do Logradouro',
        comodel_name='sped.tipo_logradouro',
    )
    desc_logradouro = fields.Char(
        string=u'Descrição do Logradouro',
        size=100,
        help=u'Nome Layout: dscLograd - Tamanho: Até 100 Caracteres - '
             u'Descrição do logradouro.',
    )
    num_logradouro = fields.Char(
        string=u'Número do Logradouro',
        size=10,
        help=u'Nome Layout: 10 - Tamanho: Até 10 Caracteres - Número do '
             u'logradouro. Se não houver número a ser informado, '
             u'preencher com "S/N".',
    )
    complemento = fields.Char(
        string=u'Complemento',
        size=30,
        help=u'Nome Layout: complemento - Tamanho: Até 30 Caracteres - '
             u'Complemento do logradouro',
    )
    bairro = fields.Char(
        string=u'Bairro',
        size=90,
        help=u'Nome Layout: bairro - Tamanho: Até 90 Caracteres - '
             u'Nome do bairro/distrito',
    )
    cep = fields.Char(
        string=u'CEP',
        size=8,
        help=u'Nome Layout: cep - Tamanho: Até 8 Caracteres - Código de '
             u'Endereçamento Postal - CEP.',
    )
    country_id = fields.Many2one(
        string=u'País',
        comodel_name='res.country',
        help=u'Nome Layout: pais - Tamanho: Até 3 Caracteres - Preencher com '
             u'o código do país, conforme Tabela 06.',
    )
    uf_id = fields.Many2one(
        string=u'UF',
        comodel_name='res.country.state',
        domain="[('country_id', '=', country_id)]",
        help=u'Nome Layout: uf - Tamanho: Até 2 Caracteres - Preencher com '
             u'a sigla da Unidade da Federação.',
    )
    city_id = fields.Many2one(
        string=u'Municipio',
        comodel_name='l10n_br_base.city',
        domain="[('state_id','=', uf_id)]",
        help=u'Nome Layout: codMunic - Tamanho: Até 7 Caracteres - Preencher '
             u'com o código do município, conforme tabela do IBGE.',
    )
    cod_postal = fields.Char(
        string=u'Código Postal',
        size=12,
        help=u'Nome Layout: codPostal - Tamanho: Até 12 Caracteres - Código de '
             u'Endereçamento Postal.',
    )
    tipo_inscricao_local = fields.Many2one(
        string=u'Tipo Inscrição do Local',
        comodel_name='sped.tipos_inscricao',
    )
    num_inscricao = fields.Char(
        string=u'Número Inscrição do Estabelecimento',
        size=15,
        help=u'Nome Layout: nrInsc - Tamanho: Até 15 Caracteres - Informar o'
             u' número de inscrição do estabelecimento, de acordo com o tipo'
             u' de inscrição indicado no campo {Tipo Inscrição do Local}. '
             u'Se o acidente ou a doença ocupacional ocorreu em local onde'
             u' o trabalhador presta serviços, deve ser um número de '
             u'inscrição pertencente à contratante dos serviços.',
    )
    parte_atingida_ids = fields.One2many(
        string=u'Parte Atingida',
        comodel_name='hr.acidente.parte.atingida',
        inverse_name='acidente_trabalho_id',
    )
    agente_causador_ids = fields.One2many(
        string=u'Agente Causador',
        comodel_name='hr.agente.causador',
        inverse_name='acidente_trabalho_id',
    )
    atestado_medico_id = fields.Many2one(
        string=u'Atestado Médico',
        comodel_name='hr.atestado.medico',
    )
    num_recibo_cat_original = fields.Char(
        string=u'Número Recibo CAT Original',
        size=40,
        help=u'Nome Layout: nrRecCatOrig - Tamanho: Até 40 Caracteres - '
             u'Informar o número do recibo da CAT de origem. Validação: '
             u'Deve corresponder ao número do recibo do arquivo relativo à '
             u'CAT informada anteriormente, pertencente ao mesmo trabalhador.',
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.comunicacao.acidente.trabalho',
    )
    @api.model
    def _compute_name(self):
        for record in self:
            record.name = '{} - {} - {}'.format(
                record.data_acidente, record.contract_id.name,
                record.tipo_acidente.nome
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
                'hr_comunicacao_acidente_trabalho_id': self.id,
            }
            self.sped_intermediario_id = self.env[
                'sped.hr.comunicacao.acidente.trabalho'].create(vals)
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
            super(HrComunicacaoAcidenteTrabalho, record).unlink()
