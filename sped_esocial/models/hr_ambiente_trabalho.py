# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class AmbienteTrabalho(models.Model):
    _name = 'hr.ambiente.trabalho'
    _rec_name = 'cod_ambiente'
    _description = u'Ambiente de Trabalho'
    _order = 'cod_ambiente'
    _sql_constraints = [
        ('cod_ambiente',
         'unique(cod_ambiente)',
         'Este código já existe !'
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
    cod_ambiente = fields.Char(
        string=u'Código do Ambiente',
        size=30,
    )
    company_id = fields.Many2one(
        string=u'Localidade',
        comodel_name='res.company',
        domain=[('situacao_esocial', '=', 1)]
    )
    data_inicio = fields.Many2one(
        string=u'Data de início',
        comodel_name='account.period',
        domain=[('special', '=', False)],
    )
    data_fim = fields.Many2one(
        string=u'Data de Fim',
        comodel_name='account.period',
        domain=[('special', '=', False)],
    )
    nova_data_inicio = fields.Many2one(
        string=u'Data de início',
        comodel_name='account.period',
        domain=[('special', '=', False)],
    )
    nova_data_fim = fields.Many2one(
        string=u'Data de Fim',
        comodel_name='account.period',
        domain=[('special', '=', False)],
    )
    nome_ambiente = fields.Char(
        string='Nome do Ambiente',
        size=100,
    )
    desc_ambiente = fields.Text(
        string='Descrição',
        size=8000,
    )
    local_ambiente = fields.Selection(
        string='Tipo do local',
        selection=[
            (1, 'Estabelecimento do próprio empregador'),
            (2, 'Estabelecimento de terceiros'),
            (3, 'Prestação de serviços em instalações de terceiros não consideradas como lotações'),
        ],
        default=1,
    )
    tipo_inscricao = fields.Many2one(
        string='Tipo de Inscrição',
        comodel_name='sped.tipos_inscricao',
    )
    num_inscricao = fields.Char(
        string='Número de Inscrição',
        size=15,
    )
    cod_lotacao = fields.Char(
        string='Código de Lotação Tributária',
        size=30,
        compute='_compute_lotacao_tributaria',
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediario S-1060',
        comodel_name='sped.hr.ambiente.trabalho',
    )

    @api.multi
    def _compute_state(self):
        for record in self:
            if not record.sped_intermediario_id:
                record.state = 0
            else:
                record.state = record.sped_intermediario_id.situacao_esocial

    @api.multi
    @api.depends('local_ambiente')
    def _compute_lotacao_tributaria(self):
        for record in self:
            record.cod_lotacao = record.company_id.cod_lotacao

    def gerar_intermediario(self):
        if not self.sped_intermediario_id:
            vals = {
                'company_id': self.company_id.id if self.company_id.eh_empresa_base else self.company_id.matriz.id,
                'hr_ambiente_trabalho_id': self.id,
            }
            self.sped_intermediario_id = self.env['sped.hr.ambiente.trabalho'].create(vals)
            self.sped_intermediario_id.gerar_registro('I')

    @api.multi
    def button_enviar_esocial(self):
        self.gerar_intermediario()

    @api.multi
    def gerar_atualizacao(self):
        for record in self:
            record.sped_intermediario_id.gerar_registro('A')

    @api.multi
    def gerar_exclusao(self):
        for record in self:
            record.sped_intermediario_id.gerar_registro('E')

    @api.multi
    def button_alterar_esocial(self):
        self.gerar_atualizacao()

    @api.multi
    def button_exclusao_esocial(self):
        self.gerar_exclusao()
