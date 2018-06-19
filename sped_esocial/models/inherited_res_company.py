# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.esocial import ProcessadorESocial
from openerp.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    esocial_tpAmb = fields.Selection(
        string='Ambiente de Transmissão',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
        ]
    )
    natureza_juridica_id = fields.Many2one(
        string='Tab.21-Natureza Jurídica',
        comodel_name='sped.natureza_juridica',
    )
    ind_coop = fields.Selection(
        string='Indicativo de Cooperativa',
        selection=[
            ('0', 'Não é cooperativa'),
            ('1', 'Cooperativa de Trabalho'),
            ('2', 'Cooperativa de Produção'),
            ('3', 'Outras Cooperativas'),
        ],
        default='0',
    )
    ind_constr = fields.Selection(
        string='Indicativo de Construtora',
        selection=[
            ('0', 'Não é Construtora'),
            ('1', 'Empresa Construtora'),
        ],
        default='0',
    )
    ind_opt_reg_eletron = fields.Selection(
        string='Opta por Registro Eletrônico de Empregados',
        selection=[
            ('0', 'Não optou pelo registro eletrônico de empregados'),
            ('1', 'Optou pelo registro eletrônico de empregados'),
        ],
        default='0',
    )
    ind_ent_ed = fields.Selection(
        string='Entidade sem fins lucrativos',
        selection=[
            ('N', 'Não'),
            ('S', 'Sim'),
        ],
        default='N',
    )
    ind_ett = fields.Selection(
        string='Empr.de Trab.Temporário com registro no Min.Trab.',
        selection=[
            ('N', 'Não'),
            ('S', 'Sim'),
        ],
        default='N',
    )
    nr_reg_ett = fields.Char(
        string='Nº reg. de Trab.Temp. no Min.Trab.',
        size=30,
    )
    esocial_nm_ctt = fields.Char(
        string='Contato',
        size=70,
    )
    esocial_cpf_ctt = fields.Char(
        string='CPF',
        size=11,
    )
    esocial_fone_fixo = fields.Char(
        string='Telefone',
        size=13,
    )
    esocial_fone_cel = fields.Char(
        string='Celular',
        size=13,
    )
    esocial_email = fields.Char(
        string='e-mail',
        size=60,
    )
    esocial_periodo_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
    )
    sped_s1000 = fields.Boolean(
        string='Ativação eSocial',
        compute='_compute_sped_s1000',
    )
    sped_s1000_registro = fields.Many2one(
        string='Registro S-1000 - Informações do Contribuinte',
        comodel_name='sped.transmissao',
    )
    sped_s1000_situacao = fields.Selection(
        string='Situação S-1000',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_s1000_registro.situacao',
        readonly=True,
    )
    sped_s1000_data_hora = fields.Datetime(
        string='Data/Hora',
        related='sped_s1000_registro.data_hora_origem',
        readonly=True,
    )

    @api.depends('sped_r1000_registro')
    def _compute_sped_s1000(self):
        for empresa in self:
            empresa.sped_s1000 = True if empresa.sped_s1000_registro else False

    @api.multi
    def criar_s1000(self):
        self.ensure_one()
        if self.sped_s1000_registro:
            raise ValidationError('Esta Empresa já ativou o e-Social')

        values = {
            'tipo': 'esocial',
            'registro': 'S-1000',
            'company_id': self.id,
            'evento': 'evtInfoEmpregador',
            'origem': ('res.company,%s' % self.id),
        }

        sped_s1000_registro = self.env['sped.transmissao'].create(values)
        self.sped_s1000_registro = sped_s1000_registro

    @api.multi
    def processador_esocial(self):
        self.ensure_one()

        processador = ProcessadorESocial()
        processador.versao = '2.04.02'

        if self.nfe_a1_file:
            processador.certificado = self.certificado_nfe()
