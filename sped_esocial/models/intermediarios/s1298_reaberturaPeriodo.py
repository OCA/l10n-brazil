# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
import pysped


class SpedEsocialFechamento(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.reabertura"
    _rec_name = "codigo"
    _order = "company_id,periodo_id"

    codigo = fields.Char(
        string='Código',
        compute='_compute_codigo',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )

    @api.depends('company_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
            if esocial.company_id:
                codigo += esocial.company_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '('
                codigo += esocial.periodo_id.code or ''
                codigo += ')'
            esocial.codigo = codigo

    # Campos de controle e-Social, registros Periódicos
    sped_registro = fields.Many2one(
        string='Registro SPED',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_registro.situacao',
        store=True,
    )

    sped_fechamento_id = fields.Many2one(
        comodel_name='sped.esocial.fechamento',
        string=u'Fechamento de Período',
    )

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_esocial(self):
        # Criar o registro S-1298
        if not self.sped_registro:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1298',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'na',
                'evento': 'evtReabreEvPer',
                'origem': ('sped.esocial.fechamento,%s' % self.sped_fechamento_id.id),
                'origem_intermediario': ('sped.esocial.reabertura,%s' % self.id),
            }

            sped_registro = self.env['sped.registro'].create(values)
            self.sped_registro = sped_registro

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S1298 = pysped.esocial.leiaute.S1298_2()
        S1298.tpInsc = '1'
        S1298.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        S1298.evento.ideEvento.indApuracao.valor = '1'

        S1298.evento.ideEvento.perApur.valor = \
            self.periodo_id.code[3:7] + '-' + \
            self.periodo_id.code[0:2]

        S1298.evento.ideEvento.tpAmb.valor = ambiente
        S1298.evento.ideEvento.procEmi.valor = '1'
        S1298.evento.ideEvento.verProc.valor = 'SAB 8.0'

        # Popula ideEmpregador (Dados do Empregador)
        S1298.evento.ideEmpregador.tpInsc.valor = '1'
        S1298.evento.ideEmpregador.nrInsc.valor = \
            limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        return S1298, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
        pass
