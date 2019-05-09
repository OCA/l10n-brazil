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
        help=u'Nome layout: codAmb - Tamanho: Até 30 Caracteres - '
             'Preencher com o código atribuído pela empresa ao Ambiente '
             'de Trabalho. Validação: O código atribuído não pode conter '
             'a expressão "eSocial" nas 7(sete) primeiras posições.',
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
        help=u'Nome layout: iniValid - Tamanho: Até 7 Caracteres - Preencher '
             u'com o mês e ano de início da validade das informações '
             u'prestadas no evento, no formato AAAA-MM.',
    )
    data_fim = fields.Many2one(
        string=u'Data de Fim',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        help=u'Nome layout: fimValid - Tamanho: Até 7 Caracteres - Preencher '
             u'com o mês e ano de término da validade das informações, '
             u'se houver.',
    )
    nova_data_inicio = fields.Many2one(
        string=u'Data de início',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        help=u'Nome layout: iniValid - Tamanho: Até 7 Caracteres - Preencher '
             u'com o mês e ano de início da validade das informações '
             u'prestadas no evento, no formato AAAA-MM.',
    )
    nova_data_fim = fields.Many2one(
        string=u'Data de Fim',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        help=u'Nome layout: fimValid - Tamanho: Até 7 Caracteres - Preencher '
             u'com o mês e ano de término da validade das informações, '
             u'se houver.',
    )
    nome_ambiente = fields.Char(
        string='Nome do Ambiente',
        size=100,
        help=u'Nome layout: nmAmb - Tamanho: Até 100 Caracteres - Informar o '
             u'nome do ambiente de trabalho.',
    )
    desc_ambiente = fields.Text(
        string='Descrição',
        size=8000,
        help=u'Nome layout: dscAmb - Tamanho: Até 8000 Caracteres - Descrição '
             u'do ambiente de trabalho.',
    )
    local_ambiente = fields.Selection(
        string='Tipo do local',
        selection=[
            (1, 'Estabelecimento do próprio empregador'),
            (2, 'Estabelecimento de terceiros'),
            (3, 'Prestação de serviços em instalações de terceiros '
                'não consideradas como lotações'),
        ],
        default=1,
        help=u'Nome layout: localAmb - Tamanho: Até 1 Caracteres - Preencher '
             u'com uma das opções: 1 - Estabelecimento do próprio empregador; '
             u'2 - Estabelecimento de terceiros; '
             u'3 - Prestação de serviços em instalações de terceiros não '
             u'consideradas como lotações dos tipos 03 a 09 da Tabela 10.',
    )
    tipo_inscricao = fields.Many2one(
        string='Tipo de Inscrição',
        comodel_name='sped.tipos_inscricao',
        help=u'Nome layout: tpInsc - Tamanho: Até 1 Caracteres - Preencher '
             u'com o código correspondente ao tipo de inscrição, '
             u'conforme Tabela 05. Validação: Preenchimento obrigatório e '
             u'exclusivo se {local_ambiente} = [1, 3].',
    )
    num_inscricao = fields.Char(
        string='Número de Inscrição',
        size=15,
        help=u'Nome layout: nrInsc - Tamanho: Até 15 Caracteres - Número de '
             u'inscrição onde está localizado o ambiente.',
    )
    cod_lotacao = fields.Char(
        string='Código de Lotação Tributária',
        size=30,
        compute='_compute_lotacao_tributaria',
        help=u'Nome layout: codLotacao - Tamanho: Até 30 Caracteres - Informar '
             u'o código atribuído pela empresa para a lotação tributária. '
             u'Se informado, deve ser um código existente '
             u'em S-1020 - Tabela de Lotações Tributárias.',
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
                'company_id': self.company_id.id if
                self.company_id.eh_empresa_base else self.company_id.matriz.id,
                'hr_ambiente_trabalho_id': self.id,
            }
            self.sped_intermediario_id = \
                self.env['sped.hr.ambiente.trabalho'].create(vals)
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
