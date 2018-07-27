# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrContract(models.Model):

    _inherit = 'hr.contract'

    # Criar campos que faltam para o eSocial
    tp_reg_prev = fields.Selection(
        string='Tipo de Regime Previdenciário',
        selection=[
            ('1', 'Regime Geral da Previdência Social - RGPS'),
            ('2', 'Regime Próprio de Previdência Social - RPPS'),
            ('3', 'Remige de Previdência Social no Exterior'),
        ],
    )
    cad_ini = fields.Selection(
        string='Cadastro Inicial de Vínculo',
        selection=[
            ('N', 'Não (Admissão)'),
            ('S', 'Sim (Cadastramento Inicial)'),
        ],
        default='N',
        help='Indicar se o evento se refere a cadastramento inicial de vínculo'
             ' (o ingresso do trabalhador no empregador declarante, por '
             'admissão ou transferência, é anterior à data de início da '
             'obrigatoriedade de envio de seus eventos não periódicos) ou se '
             'refere a uma admissão (o ingresso do trabalhador no empregador'
             ' declarante é igual ou posterior à data de início de '
             'obrigatoriedade de envio de seus eventos não periódicos)',
    )
    tp_reg_jor = fields.Selection(
        string='Regime de Jornada',
        selection=[
            ('1', '1-Submetidos a Horário de Trabalho (Cap. II da CLT)'),
            ('2', '2-Atividade Externa especifica no Inciso I do Art. 62 da CLT'),
            ('3', '3-Funções especificadas no Inciso II do Art. 62 da CLT'),
            ('4', '4-Teletrabalho, previsto no Inciso III do Art. 62 da CLT'),
        ],
    )
    nat_atividade = fields.Selection(
        string='Natureza da Atividade',
        selection=[
            ('1', '1-Trabalho Urbano'),
            ('2', '2-Trabalho Rural'),
        ]
    )
    opc_fgts = fields.Selection(
        string='Optante do FGTS',
        selection=[
            ('1', '1-Optante'),
            ('2', '2-Não Optante'),
        ],
        help='e-Social: S-2200/S-2300 - opcFGTS',
    )
    dt_opc_fgts = fields.Date(
        string='Data de Opção do FGTS',
        help='e-Social: S-2200/S-2300 - dtOpcFgts',
    )
    dsc_sal_var = fields.Char(
        string='Descrição Salário Variável',
        size=255,
        help="e-Social: S-2200/S-2300 - dscSalVar"
             "\nDescrição do salário por tarefa ou variável e como este é "
             "calculado. "
             "\nEx.: Comissões pagas no percentual de 10% sobre as vendas.",
    )
    tp_contr = fields.Selection(
        string='Tipo de Contrato de Trabalho',
        selection=[
            ('1', '1-Prazo indeterminado'),
            ('2', '2-Prazo determinado'),
        ],
        help='e-Social: S-2200 - tpContr',
    )
    clau_assec = fields.Selection(
        string='Contém Cláusula Assecuratória',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    tp_jornada = fields.Selection(
        string='Tipo da Jornada',
        selection=[
            ('1', '1-Jornada com horário diário e folga fixos'),
            ('2', '2-Jornada 12x36 (12 horas de trabalho seguidas de 36 horas ininterruptas de descanso'),
            ('3', '3-Jornada com horário diário fixo e folga variável'),
            ('9', '9-Demais tipos de jornada'),
        ],
    )
    dsc_tp_jorn = fields.Char(
        string='Descrição da Jornada',
        size=100,
    )
    tmp_parc = fields.Selection(
        string='Código Tipo Contrato em Tempo Parcial',
        selection=[
            ('0', '0-Não é contrato em tempo parcial'),
            ('1', '1-Limitado a 25 horas semanais'),
            ('2', '2-Limitado a 30 horas semanais'),
            ('3', '3-Limitado a 26 horas semanais'),
        ],
    )
    resignation_cause_id = fields.Many2one(
        comodel_name='sped.motivo_desligamento',
        string='Resignation cause'
    )
    resignation_code = fields.Char(
        related='resignation_cause_id.codigo',
    )
    nr_cert_obito = fields.Char(
        string='Certidão de Óbito',
        size=32,
    )

    evento_esocial = fields.Char(
        string='Evento no esocial',
        help='Definição do Evento do esocial de acordo com a categoria.',
        compute='_compute_evento_esocial',
    )
    salary_unit_code = fields.Char(
        string='Cod. unidade de salario',
        related='salary_unit.code',
    )

    # Registro S-2200
    sped_contrato_id = fields.Many2one(
        string='SPED Contrato',
        comodel_name='sped.esocial.contrato',
    )
    # Registro S-2206
    sped_esocial_alterar_contrato_id = fields.Many2one(
        string='Alterar Contrato',
        comodel_name='sped.esocial.alteracao.contrato',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        related='sped_esocial_alterar_contrato_id.precisa_atualizar',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        string='Situação no e-Social',
        related='sped_contrato_id.situacao_esocial',
        readonly=True,
    )
    situacao_esocial_alteracao = fields.Selection(
        selection=[
            ('1', 'Precisa Atualizar'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Situação no e-Social',
        related='sped_esocial_alterar_contrato_id.situacao_esocial',
        readonly=True,
    )

    # Registro S-2300
    sped_contrato_autonomo_id = fields.Many2one(
        string='SPED Contrato',
        comodel_name='sped.esocial.contrato.autonomo',
    )
    # Registro S-2306
    sped_esocial_alterar_contrato_autonomo_id = fields.Many2one(
        string='Alterar Contrato',
        comodel_name='sped.esocial.alteracao.contrato.autonomo',
    )
    situacao_esocial_autonomo = fields.Selection(
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        string='Situação no e-Social',
        related='sped_contrato_autonomo_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar_autonomo = fields.Boolean(
        string='Precisa atualizar dados?',
        related='sped_esocial_alterar_contrato_autonomo_id.precisa_atualizar',
    )
    admission_type_code = fields.Char(
        string='Código do tipo da admissão',
        related='admission_type_id.code'
    )

    @api.multi
    def ativar_contrato(self):
        self.ensure_one()

        # Se o registro intermediário do S-2200 não existe, criá-lo
        if not self.sped_contrato_id:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            self.sped_contrato_id = \
                self.env['sped.esocial.contrato'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })

        # Processa cada tipo de operação do S-2200 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_contrato_id.gerar_registro()

    @api.multi
    def write(self, vals):

        if self.evento_esocial == 's2200':
            self._gerar_tabela_intermediaria_alteracao(vals)

        if self.evento_esocial == 's2300':
            self._gerar_tabela_intermediaria_alteracao_autonomo(vals)

        return super(HrContract, self).write(vals)

    @api.multi
    def _gerar_tabela_intermediaria_alteracao(self, vals={}):
        # Se o registro intermediário do S-2206 não existe, criá-lo
        if not self.sped_esocial_alterar_contrato_id and not \
                vals.get('sped_esocial_alterar_contrato_id'):
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            esocial_alteracao = \
                self.env['sped.esocial.alteracao.contrato'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })
            self.sped_esocial_alterar_contrato_id = esocial_alteracao

    @api.multi
    def _gerar_tabela_intermediaria_alteracao_autonomo(self, vals={}):
        """
        Duplicada
        """
        if not self.sped_esocial_alterar_contrato_autonomo_id and not \
                vals.get('sped_esocial_alterar_contrato_autonomo_id'):
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            esocial_alteracao = \
                self.env['sped.esocial.alteracao.contrato.autonomo'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })
            self.sped_esocial_alterar_contrato_autonomo_id = esocial_alteracao

    @api.multi
    def alterar_contrato(self):
        self.ensure_one()

        # Se o registro intermediário do S-2206 não existe, criá-lo
        if not self.sped_esocial_alterar_contrato_id:
            self._gerar_tabela_intermediaria_alteracao()

        # Processa cada tipo de operação do S-2206 (Alteração)
        # O que realmente precisará ser feito é tratado no método do
        # registro intermediário
        self.sped_esocial_alterar_contrato_id.gerar_registro()

        # Enviar o ultimo registro
        # self.sped_esocial_alterar_contrato_id[0].sped_s2200_registro_retificacao[0].transmitir_lote()

    @api.multi
    def atualizar_contrato_autonomo(self):
        """
        Função Duplicada =\
        """
        self.ensure_one()

        sped_esocial_contrato_obj = self.env['sped.esocial.contrato.autonomo']

        # Se o registro intermediário não existe, criá-lo
        if not self.sped_contrato_autonomo_id:

            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            esocial_contrato_autonomo_id = \
                self.env['sped.esocial.contrato.autonomo'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })

            self.sped_contrato_autonomo_id = esocial_contrato_autonomo_id

        # Processa cada tipo de operação do S-2200 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_contrato_autonomo_id.gerar_registro()

    @api.multi
    def alterar_contrato_autonomo(self):
        self.ensure_one()

        # Se o registro intermediário do S-2206 não existe, criá-lo
        if not self.sped_esocial_alterar_contrato_autonomo_id:
            self._gerar_tabela_intermediaria_alteracao_autonomo()

        # Processa cada tipo de operação do S-2206 (Alteração)
        # O que realmente precisará ser feito é tratado no método do
        # registro intermediário
        self.sped_esocial_alterar_contrato_autonomo_id.gerar_registro()

    @api.multi
    @api.depends('categoria')
    def _compute_evento_esocial(self):
        """
        Validar de acordo com a categoria para definir qual tipo de registro
        sera criado e enviado ao esocial.
        Futuramente será atributo da tabela de categorias.
        """
        categoria_do_s2300 = ['201', '202', '401', '410', '721', '722', '723',
                              '731', '734', '738', '761', '771', '901', '902']
        for record in self:
            if record.categoria in categoria_do_s2300:
                record.evento_esocial = 's2300'
            else:
                record.evento_esocial = 's2200'

    @api.multi
    def transmitir_contrato_s2200(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_contrato_id.transmitir()

    @api.multi
    def consultar_contrato_s2200(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_contrato_id.consultar()