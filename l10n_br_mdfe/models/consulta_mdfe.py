# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import tempfile

from odoo import models, fields, api
from pynfe.processamento.mdfe import ComunicacaoMDFe
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class ConsultaMDFe(models.Model):
    _name = 'consulta.mdfe'

    tipo_consulta = fields.Selection(
        selection=[
            ('nao_encerrados', 'Não encerrados'),
            ('outra', 'Outra'),
        ],
        string='Tipo de consulta',
    )

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        default=lambda self: self.env.user.company_id.sped_empresa_id.id,
        inverse='_inverse_empresa_id',
    )

    certificado_id = fields.Many2one(
        comodel_name='sped.certificado',
        string='Certificado digital',
        default=lambda self: self.empresa_id.certificado_id.id,
    )

    mensagem_consulta = fields.Text(
        string='Retorno Consulta'
    )

    mdfe_nao_encerrados = fields.Many2many(
        comodel_name='sped.documento',
        string='MDF-e não encerrados',
    )

    def _inverse_empresa_id(self):
        if self.empresa_id:
            self.certificado_id = self.empresa_id.certificado_id

    @api.multi
    def consultar(self):
        if not (self.empresa_id and self.certificado_id):
            return {}
        if self.tipo_consulta == 'nao_encerrados':
            caminho = tempfile.gettempdir() + '/certificado.pfx'
            f = open(caminho, 'wb')
            f.write(self.certificado_id.arquivo.decode('base64'))
            f.close()

            mdfe = ComunicacaoMDFe(self.empresa_id.estado, caminho,
                                   self.certificado_id.senha, True)
            processo = mdfe.consulta_nao_encerrados(
                punctuation_rm(self.empresa_id.cnpj_cpf_numero))
            mensagem = 'Código de retorno: ' + \
                       processo.resposta.cStat
            mensagem += '\nMensagem: ' + \
                        processo.resposta.xMotivo.encode('utf-8')
            self.mensagem_consulta = mensagem
            self.mdfe_nao_encerrados = [(5, 0, 0)]
            for infMDFe in processo.resposta.infMDFe:
                doc = self.env['sped.documento'].search([
                    ('chave', '=', infMDFe.chMDFe)])
                if doc:
                    doc.protocolo_autorizacao = infMDFe.nProt
                self.mdfe_nao_encerrados += doc
            if processo.resposta.cStat == '112':
                self.mdfe_nao_encerrados = [(5, 0, 0)]
