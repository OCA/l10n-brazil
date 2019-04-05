# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class SpedRegistro(models.Model):
    _inherit = 'sped.registro'

    sped_s3000 = fields.Many2one(
        string='Registro de Exclusão (S-3000)',
        comodel_name='sped.registro',
    )
    motivo_s3000 = fields.Text(
        string='Motivo da Exclusão',
    )
    situacao_s3000 = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        related='sped_s3000.situacao',
    )
    pode_excluir = fields.Boolean(
        string='Pode Excluir?',
        compute='compute_pode_excluir',
    )
    sped_s5001 = fields.Many2one(
        string='Totalizador da base do INSS (S-5001)',
        comodel_name='sped.contribuicao.inss',
    )

    @api.depends('registro')
    def compute_pode_excluir(self):
        for registro in self:
            registro.pode_excluir = True if registro.registro in [
                'S-1200', 'S-1202', 'S-1207', 'S-1210', 'S-1250', 'S-1260', 'S-1270', 'S-1280', 'S-1295', 'S-1300',
                'S-2190', 'S-2200', 'S-2205', 'S-2206', 'S-2210', 'S-2220', 'S-2230', 'S-2240', 'S-2241', 'S-2250',
                'S-2260', 'S-2298', 'S-2299', 'S-2300', 'S-2306', 'S-2399'] else False

    # Método que permite a exclusão de registros e-Social (S-3000)
    # Este método só pode ser usado por registros S-1200 a S-2399 com exceção de S-1299 e S-1298
    @api.multi
    def excluir_registro(self):
        self.ensure_one()

        # Valida se a exclusão deste registro é possível
        if self.situacao != '4':
            raise ValidationError("Somente um registro que foi transmitido com sucesso pode ser Excluído!")
        if self.registro not in ['S-1200', 'S-1202', 'S-1207', 'S-1210', 'S-1250', 'S-1260',
                                 'S-1270', 'S-1280', 'S-1295', 'S-1300', 'S-2190', 'S-2200',
                                 'S-2205', 'S-2206', 'S-2210', 'S-2220', 'S-2230', 'S-2240',
                                 'S-2241', 'S-2250', 'S-2260', 'S-2298', 'S-2299', 'S-2300',
                                 'S-2306', 'S-2399']:
            raise ValidationError("Este registro não pode ser Excluído usando o S-3000! "
                                  "Somente registros S-1200 a S-2399 com exceção de "
                                  "S-1298 e S-1299")

        # Verifica se o registro intermediário já existe
        domain = [
            ('company_id', '=', self.company_id.id),
            ('sped_registro_id', '=', self.id),
        ]
        sped_intermediario = self.env['sped.esocial.exclusao'].search(domain, limit=1)
        if not sped_intermediario:
            # Cria o registro Intermediário
            values = {
                'company_id': self.company_id.id,
                'sped_registro_id': self.id,
            }
            sped_intermediario = self.env['sped.esocial.exclusao'].create(values)

        # Verifica se o registro S-3000 já existe
        domain = [
            ('tipo', '=', 'esocial'),
            ('registro', '=', 'S-3000'),
            ('operacao', '=', 'na'),
            ('ambiente', '=', self.company_id.esocial_tpAmb),
            ('company_id', '=', self.company_id.id),
            ('origem', '=', ('sped.registro,%s' % self.id)),
        ]
        sped_s3000 = self.env['sped.registro'].search(domain, limit=1)
        if not sped_s3000:
            # Cria o registro S-3000 relacionado
            values = {
                'tipo': 'esocial',
                'registro': 'S-3000',
                'operacao': 'na',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'evento': 'evtExclusão',
                'origem': ('sped.registro,%s' % self.id),
                'origem_intermediario': ('sped.esocial.exclusao,%s' % sped_intermediario.id),
            }
            sped_s3000 = self.env['sped.registro'].create(values)

        # Relaciona o registro S-3000 neste registro
        self.sped_s3000 = sped_s3000

        # Popula o registro de transmissão na tabela intermediária
        sped_intermediario.sped_transmissao_id = sped_s3000

        return sped_s3000

    # Método que transmite o registro S-3000 relacionado
    @api.multi
    def transmitir_s3000(self):
        self.ensure_one()

        # Valida se o registro S-3000 existe e pode ser transmitido
        if not self.sped_s3000:
            raise ValidationError("Não existe um registro S-3000 relacionado que permita a exclusão!")
        if self.sped_s3000.situacao not in ['1', '3']:
            raise ValidationError("O registro S-3000 relacionado não pode ser transmitido !")

        # Transmite o registro
        self.sped_s3000.transmitir_lote()

    # Método que consulta a transmissão do registro S-3000 relacionado
    @api.multi
    def consultar_s3000(self):
        self.ensure_one()

        # Valida se o registro S-3000 existe e pode ser consultado
        if not self.sped_s3000:
            raise ValidationError("Não existe um registro S-3000 relacionado que permita a exclusão!")
        if self.sped_s3000.situacao not in ['2', '4']:
            raise ValidationError("O registro S-3000 relacionado não pode ser consultado!")

        # Consulta o registro
        self.sped_s3000.consulta_lote()
