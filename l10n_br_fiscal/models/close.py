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
from datetime import datetime
import calendar

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
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
)

from odoo.addons.l10n_br_nfe.constants.nfe import (
    NFE_ENVIRONMENTS
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

PATH_AMBIENTE = dict(NFE_ENVIRONMENTS)

SITUACAO_EDOC = [
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
]

XMLS_IMPORTANTES = [
    'file_xml_autorizacao_id',
    'file_xml_autorizacao_cancelamento_id',
    'file_xml_autorizacao_inutilizacao_id',
    'file_pdf_id',
]


class Close(models.Model):
    _name = 'close'
    _description = 'Export NFes'

    name = fields.Char(
        string='Nome',
        size=255
    )
    year = fields.Char(
        string='Year',
    )
    month = fields.Char(
        string='Month',
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
        selection=[('period', 'Por período'),
                   ('all', 'Tudo')],
        string='Export',
        default='period',
        required=True
    )
    pasta_individual = fields.Boolean(
        string='Individual document folder',
        default=False
    )
    raiz = fields.Char(
        string='Folder structure path',
        default=''
    )

    document_nfe_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string=" NFe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '55')]
    )

    document_nfce_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFCe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '65')]
    )

    document_cfe_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '59')]
    )

    document_cfeecf_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe ECF Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '60')]
    )

    document_nfse_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFce Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', 'SE')]
    )

    document_rl_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="RL Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', 'RL')]
    )



    def monta_caminho(self, document):
        document_path = '/'.join([
            # TODO: Colocar ambiente
            # PATH_AMBIENTE[documento.nfe_environment],
            limpa_formatacao(document.company_cnpj_cpf),
            PATH_MODELO[document.document_type_id.code],
            document.date.strftime("%m-%Y"),
            document.document_serie_id.code.zfill(3) +
            ('-' + limpa_formatacao(str(document.number)).zfill(9)
             if self.pasta_individual else '')
        ])
        if self.raiz:
            if not os.path.exists(self.raiz + '/' + document_path):
                try:
                    os.makedirs(self.raiz + '/' + document_path)
                except OSError:
                    raise RedirectWarning(
                        _('Error!'),
                        _('Check write permissions and folder path'))
        return document_path

    def _prepara_arquivos(self, periodic_export=False):
        domain = [('document_type', 'in', MODELO_FISCAL_EMISSAO_PRODUTO +
                   MODELO_FISCAL_EMISSAO_SERVICO),
                  ('state_edoc', 'in', SITUACAO_EDOC)]

        if self.export_type == 'period':
            date_range = calendar.monthrange(int(self.year), int(self.month))
            date_min = '-'.join((self.year, self.month, str(date_range[0])))
            date_min = datetime.strptime(date_min, '%Y-%m-%d')

            date_max = '-'.join((self.year, self.month, str(date_range[1])))
            date_max = datetime.strptime(date_max, '%Y-%m-%d')

        domain += [
            ('date', '>=', date_min),
            ('date', '<=', date_max),
        ] if self.export_type == 'period' else []

        domain += [
            ('close_id', '=', False)
        ] if periodic_export else []

        documents = self.env['l10n_br_fiscal.document'].search(domain)
        # documents += self.env['l10n_br_fiscal.document_correction'].search(domain)
        # documents += self.env['l10n_br_fiscal.document_cancel'].search(domain)

        files = {}
        for document in documents:
            anexos = [getattr(document, campo) for campo in XMLS_IMPORTANTES
                      if hasattr(document, campo)
                      and getattr(document, campo).id is not False]

            document.close_id = self.id

            if not anexos:
                continue
            document_path = self.monta_caminho(document)
            try:
                for anexo in anexos:
                    files[document_path + '/' + anexo.datas_fname] = \
                        base64.b64decode(anexo.datas)
                if periodic_export:
                    document.close_id = self.id
            except Exception:
                _logger.error(_('Replication failed: document attachments '
                                '[id =% s] is not present in the database.'
                                % document.id))
        return files

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
        files = self._prepara_arquivos()
        order_file = io.BytesIO()
        order_zip = zipfile.ZipFile(
            order_file, mode="w", compression=zipfile.ZIP_DEFLATED
        )
        for file in files.keys():
            order_zip.writestr(
                file,
                files[file]
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
