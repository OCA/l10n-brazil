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
    data_acidente = fields.Date(
        string=u'Data do Acidente',
    )
    tipo_acidente = fields.Many2one(
        string=u'Tipo do Acidente',
        comodel_name='sped.codificacao_acidente_trabalho',
    )
    hora_acidente = fields.Char(
        string='Hora e Minuto',
        size=4,
    )
    tipo_cat = fields.Selection(
        string='Tipo de CAT',
        selection=TP_CAT,
    )
    ind_cat_obito = fields.Selection(
        string=u'Houve Óbito',
        selection=SIM_NAO,
    )
    data_obito = fields.Date(
        string=u'Data do Óbito',
    )
    ind_comunicacao_policia = fields.Selection(
        string=u'Houve comunicação com a Polícia',
        selection=SIM_NAO,
    )
    cod_geradora_acidente = fields.Many2one(
        string=u'Código da Situação Geradora do Acidente',
        comodel_name='sped.situacao_geradora_acidente',
    )
    emissao_cat = fields.Selection(
        string=u'Emissor da CAT',
        selection=EMISSOR_CAT,
    )
    obs = fields.Text(
        string=u'Observações',
        size=999,
    )
    tipo_local = fields.Selection(
        string=u'Tipo do Local',
        selection=TP_LOCAL,
    )
    desc_local = fields.Text(
        string=u'Descrição',
        size=255,
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
    )
    num_logradouro = fields.Char(
        string=u'Número do Logradouro',
        size=10,
    )
    complemento = fields.Char(
        string=u'Complemento',
        size=30,
    )
    bairro = fields.Char(
        string=u'Bairro',
        size=90,
    )
    cep = fields.Char(
        string=u'CEP',
        size=8,
    )
    country_id = fields.Many2one(
        string=u'País',
        comodel_name='res.country',
    )
    uf_id = fields.Many2one(
        string=u'UF',
        comodel_name='res.country.state',
        domain="[('country_id', '=', country_id)]",
    )
    city_id = fields.Many2one(
        string=u'Municipio',
        comodel_name='l10n_br_base.city',
        domain="[('state_id','=', uf_id)]"
    )
    cod_postal = fields.Char(
        string=u'Código Postal',
        size=12,
    )
    tipo_inscricao_local = fields.Many2one(
        string=u'Tipo Inscrição do Local',
        comodel_name='sped.tipos_inscricao',
    )
    num_inscricao = fields.Char(
        string=u'Número Inscrição do Estabelecimento',
        size=15,
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
    num_recibo_cat_original = fields.Char(
        string=u'Número Recibo CAT Original',
        size=40,
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.saude.trabalhador',
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
            super(HrComunicacaoAcidenteTrabalho, record).unlink()
