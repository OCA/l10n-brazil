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
        string='Cad.Inicial de Vínculo',
        selection=[
            ('N', 'Não (Admissão)'),
            ('S', 'Sim (Cadastramento Inicial)'),
        ],
        default='N',
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

    # Registro S-2200
    sped_contrato_id = fields.Many2one(
        string='SPED Contrato',
        comodel_name='sped.esocial.contrato',
    )

    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='sped_contrato_id.situacao_esocial',
        readonly=True,
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
        self._gerar_tabela_intermediaria_alteracao(vals)
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
    def alterar_contrato(self):
        self.ensure_one()

        # Se o registro intermediário do S-2206 não existe, criá-lo
        if not self.sped_esocial_alterar_contrato_id:
            self._gerar_tabela_intermediaria_alteracao()

        # Processa cada tipo de operação do S-2206 (Alteração)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_esocial_alterar_contrato_id.gerar_registro()
