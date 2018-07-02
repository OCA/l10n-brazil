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
    )
    dt_opc_fgts = fields.Date(
        string='Data de Opção do FGTS',
    )
    dsc_sal_var = fields.Char(
        string='Descr. Salário Variável',
        size=255,
    )
    tp_contr = fields.Selection(
        string='Tipo de Contrato de Trabalho',
        selection=[
            ('1', '1-Prazo indeterminado'),
            ('2', '2-Prazo determinado'),
        ],
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
    sped_s2200 = fields.Boolean(
        string='Cadastro do Vínculo',
        compute='_compute_sped_s2200',
    )
    sped_s2200_registro = fields.Many2one(
        string='Registro S-2200 - Cadastramento Inicial do Vínculo',
        comodel_name='sped.registro',
    )
    sped_s2200_situacao = fields.Selection(
        string='Situação S-2200',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_s2200_registro.situacao',
        readonly=True,
    )
    sped_s2200_data_hora = fields.Datetime(
        string='Data/Hora',
        related='sped_s2200_registro.data_hora_origem',
        readonly=True,
    )

    @api.depends('sped_s2200_registro')
    def _compute_sped_s2200(self):
        for contrato in self:
            contrato.sped_s2200 = True if contrato.sped_s2200_registro else False

    @api.multi
    def criar_s2200(self):
        self.ensure_one()
        if self.sped_s2200_registro:
            raise ValidationError('Esta contrato já registro este vínculo')

        empresa = self.company_id.id if self.company_id.eh_empresa_base else self.company_id.matriz.id

        values = {
            'tipo': 'esocial',
            'registro': 'S-2200',
            'ambiente': self.company_id.esocial_tpAmb or self.company_id.matriz.esocial_tpAmb,
            'company_id': empresa,
            'evento': 'evtAdmissao',
            'origem': ('hr.contract,%s' % self.id),
        }

        sped_s2200_registro = self.env['sped.registro'].create(values)
        self.sped_s2200_registro = sped_s2200_registro
