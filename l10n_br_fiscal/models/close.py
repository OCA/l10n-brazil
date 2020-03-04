# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
import os
import base64
import zipfile
import io
import logging

from odoo import models, fields, _
from pybrasil.inscricao import limpa_formatacao
from odoo.exceptions import RedirectWarning
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
    MODELO_FISCAL_NFSE,
    MODELO_FISCAL_RL,
    #AMBIENTE_NFE_PRODUCAO,
    #AMBIENTE_NFE_HOMOLOGACAO,
    # SITUACAO_NFE_REJEITADA,
    # SITUACAO_NFE_AUTORIZADA,
    # SITUACAO_NFE_CANCELADA,
    # SITUACAO_NFE_DENEGADA,
    # SITUACAO_NFE_INUTILIZADA,
)

_logger = logging.getLogger(__name__)

PATH_MODELO = {
    MODELO_FISCAL_NFE: 'nfe',
    MODELO_FISCAL_NFCE: 'nfce',
    MODELO_FISCAL_CFE: 'cfe',
    MODELO_FISCAL_CUPOM_FISCAL_ECF: 'cfe_ecf',
    MODELO_FISCAL_NFSE: 'nfse',
    MODELO_FISCAL_RL: 'rl',
}
#
# SITUACOES_COM_XML = [
#     SITUACAO_NFE_REJEITADA,
#     SITUACAO_NFE_AUTORIZADA,
#     SITUACAO_NFE_CANCELADA,
#     SITUACAO_NFE_DENEGADA,
#     SITUACAO_NFE_INUTILIZADA,
# ]
#
# PATH_AMBIENTE = {
#     AMBIENTE_NFE_HOMOLOGACAO: 'homologacao',
#     AMBIENTE_NFE_PRODUCAO: 'producao',
# }

XMLS_IMPORTANTES = [
    'arquivo_xml_autorizacao_id',
    'arquivo_xml_autorizacao_cancelamento_id',
    'arquivo_xml_autorizacao_inutilizacao_id',
]


class SpedDocumentoExportar(models.Model):
    _name = 'sped.documento.exportar.xml'
    _description = 'Export NFes'

    name = fields.Char(
        string='Nome',
        size=255
    )
    date_start = fields.Date(
        string='Data Inicial'
    )
    date_stop = fields.Date(
        comodel_name='account.period',
        string='Data Final'
    )
    zip_file = fields.Binary(
        string='Zip Files',
        readonly=True
    )
    state = fields.Selection(
        selection=[('init', 'init'),
                   ('done', 'done')],
        string='state',
        default='init',
        readonly=True
    )
    export_type = fields.Selection(
        selection=[('periodo', 'Por período'),
                   ('all', 'Tudo')],
        string='Exportar',
        default='periodo',
        required=True
    )
    pasta_individual = fields.Boolean(
        string='Pasta individual para documento',
        default=False
    )
    raiz = fields.Char(
        string='Caminho da estrutura de pastas',
        default=''
    )

    def monta_caminho(self, documento):
        path_documento = '/'.join([
            PATH_AMBIENTE[documento.ambiente_nfe],
            limpa_formatacao(documento.empresa_id.cnpj_cpf),
            PATH_MODELO[documento.modelo],
            documento.data_emissao[:7],
            documento.serie.zfill(3) +
            ('-' + limpa_formatacao(str(documento.numero)).zfill(9)
             if self.pasta_individual else '')
        ])
        if self.raiz:
            if not os.path.exists(self.raiz + '/' + path_documento):
                try:
                    os.makedirs(self.raiz + '/' + path_documento)
                except OSError:
                    raise RedirectWarning(
                        _('Erro!'),
                        _('Verifique as permissões de '
                          'escrita e o caminho da pasta'))
        return path_documento

    def _prepara_arquivos(self, periodic_export=False):
        domain = [('modelo', 'in', MODELO_FISCAL_EMISSAO_PRODUTO +
                   MODELO_FISCAL_EMISSAO_SERVICO),
                  ('situacao_nfe', 'in', SITUACOES_COM_XML)]
        domain += [
            ('data_emissao', '>=', self.date_start),
            ('data_emissao', '<=', self.date_stop),
        ] if self.export_type == 'periodo' else []

        domain += [
            ('xmls_exportados', '=', False)
        ] if periodic_export else []

        documentos = self.env['sped.documento'].search(domain)

        arquivos = {}
        for documento in documentos:
            anexos = [getattr(documento, campo) for campo in XMLS_IMPORTANTES
                      if getattr(documento, campo)]
            if not anexos:
                continue
            path_documento = self.monta_caminho(documento)
            try:
                for anexo in anexos:
                    arquivos[path_documento + '/' + anexo.datas_fname] = \
                        base64.b64decode(anexo.datas)
                if periodic_export:
                    documento.xmls_exportados = True
            except Exception:
                _logger.error(_('Falha na replicação: anexos do documento '
                                '[id=%s] não está presente no banco de dados.'
                                % documento.id))
        return arquivos

    def periodic_export(self):
        export = self.new()
        export.criar_arquivo_zip = False
        export.export_type = 'all'
        export.raiz = self.env['ir.values'].get_default(
            'base.config.settings', 'pasta_contabilidade')
        arquivos = export._prepara_arquivos(periodic_export=True)
        for nome in arquivos.keys():
            f = open(export.raiz + '/' + nome, 'w')
            f.write(arquivos[nome])
            f.close()

    def export(self):
        arquivos = self._prepara_arquivos()
        order_file = io.BytesIO()
        order_zip = zipfile.ZipFile(
            order_file, mode="w", compression=zipfile.ZIP_DEFLATED
        )
        for arquivo in arquivos.keys():
            order_zip.writestr(
                arquivo,
                arquivos[arquivo]
            )
        order_zip.close()
        self.write({
            'zip_file': base64.b64encode(order_file.getvalue()),
            'name': 'xmls.zip',
            'state': 'done'
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def done(self):
        return True
