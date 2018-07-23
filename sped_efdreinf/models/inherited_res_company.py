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
    sped_r1000 = fields.Many2one(
        string='Registro R-1000 - Informações do Contribuinte',
        comodel_name='sped.efdreinf.contribuinte',
    )
    sped_r1000_situacao = fields.Selection(
        string='Situação R-1000',
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        related='sped_r1000.situacao',
        readonly=True,
    )

    # Ativação do e-Social para a empresa mãe (Registro S-1000)
    reinf_periodo_inicial_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    reinf_periodo_atualizacao_id = fields.Many2one(
        string='Período da Última Atualização',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    reinf_periodo_final_id = fields.Many2one(
        string='Período Final',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )

    @api.model
    def _field_id_domain(self):
        """
        Dominio para buscar os registros maiores que 01/2017
        """
        domain = [
            ('date_start', '>=', '2017-01-01'),
            ('special', '=', False)
        ]

        return domain

    @api.multi
    def atualizar_reinf(self):
        self.ensure_one()

        # Se o registro intermediário do R-1000 não existe, criá-lo
        if not self.sped_r1000:
            self.sped_r1000 = self.env['sped.efdreinf.contribuinte'].create(
                {'company_id': self.id})

        # Processa cada tipo de operação do R-1000 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_r1000.atualizar_reinf()

    @api.multi
    def processador_efd_reinf(self):
        self.ensure_one()

        processador = ProcessadorEFDReinf()
        processador.versao = '1.03.02'

        if self.nfe_a1_file:
            processador.certificado = self.certificado_nfe()
