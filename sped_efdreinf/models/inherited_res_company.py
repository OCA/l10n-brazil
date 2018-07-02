# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.efdreinf import ProcessadorEFDReinf
from openerp.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    tpAmb = fields.Selection(
        string='Ambiente de Transmissão',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
        ]
    )
    classificacao_tributaria_id = fields.Many2one(
        string='Classificação Tributária',
        comodel_name='sped.classificacao_tributaria',
    )
    ind_escrituracao = fields.Selection(
        string='Escrituração Contábil Digital',
        selection=[
            ('0', 'Empresa não obrigada à ECD'),
            ('1', 'Empresa obrigada à ECD'),
        ],
    )
    ind_acordoisenmulta = fields.Selection(
        string='Acordo de isenção de multa internacional',
        selection=[
            ('0', 'Sem acordo'),
            ('1', 'Com acordo'),
        ],
    )
    nmctt = fields.Char(
        string='Contato para EFD/Reinf',
    )
    cpfctt = fields.Char(
        string='CPF do Contato',
    )
    cttfonefixo = fields.Char(
        string='Telefone fixo do Contato',
    )
    cttfonecel = fields.Char(
        string='Celular do Contato',
    )
    cttemail = fields.Char(
        string='Email do Contato',
    )
    sped_r1000 = fields.Boolean(
        string='Ativação EFD/Reinf',
        compute='_compute_sped_r1000',
    )
    sped_r1000_registro = fields.Many2one(
        string='Registro R-1000 - Informações do Contribuinte',
        comodel_name='sped.registro',
    )
    sped_r1000_situacao = fields.Selection(
        string='Situação R-1000',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_r1000_registro.situacao',
        readonly=True,
    )
    sped_r1000_data_hora = fields.Datetime(
        string='Data/Hora',
        related='sped_r1000_registro.data_hora_origem',
        readonly=True,
    )
    periodo_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
    )

    @api.depends('sped_r1000_registro')
    def _compute_sped_r1000(self):
        for empresa in self:
            empresa.sped_r1000 = True if empresa.sped_r1000_registro else False

    @api.multi
    def criar_r1000(self):
        self.ensure_one()
        if self.sped_r1000_registro:
            raise ValidationError('Esta Empresa já ativou o EFD/Reinf')

        values = {
            'tipo': 'efdreinf',
            'registro': 'R-1000',
            'ambiente': self.tpAmb,
            'company_id': self.id,
            'evento': 'evtInfoContribuinte',
            'origem': ('res.company,%s' % self.id),
        }

        sped_r1000_registro = self.env['sped.registro'].create(values)
        self.sped_r1000_registro = sped_r1000_registro

    @api.multi
    def processador_efd_reinf(self):
        self.ensure_one()

        processador = ProcessadorEFDReinf()
        processador.versao = '1.03.02'

        if self.nfe_a1_file:
            processador.certificado = self.certificado_nfe()
