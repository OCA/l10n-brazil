# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
import os
import base64
import re
import tempfile
import zipfile
import io
import logging
from datetime import datetime
import calendar


from odoo import api, models, fields, _
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

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")

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


class FiscalClose(models.Model):
    _name = 'l10n_br_fiscal.close'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Fechamento Fiscal'
    _sql_constraints = [('fiscal_close_unique',
                         'unique (company_id, month, year, export_type)',
                         "The closing must be unique for the company in a "
                         "period of time.")]

    @api.depends('month', 'year', 'export_type')
    def _compute_name(self):
        for record in self:
            if record.export_type == 'period':
                record.name = "{}/{}".format(record.month, record.year)
                record.file_name = "{}-{}".format(record.month, record.year) + '.zip'
            else:
                now = fields.Datetime.tostring(fields.Datetime.now())
                record.name = now
                record.file_name = now + '.zip'

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='state',
        default='draft',
        readonly=True
    )

    name = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
        size=7,
        index=True,
    )

    file_name = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
        size=11,
        index=True,
    )
    year = fields.Char(string='Year', size=4, index=True)
    month = fields.Char(string='Month', size=2,index=True)
    zip_file = fields.Binary(
        string='Zip Files',
        readonly=True
    )
    export_type = fields.Selection(
        selection=[('period', 'Por período'),
                   ('all', 'Tudo')],
        string='Export',
        default='period',
        required=True
    )
    group_folder = fields.Boolean(
        string='Group documents',
    )
    raiz = fields.Char(
        string='Folder structure path',
        default=''
    )

    document_nfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string=" NFe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '55')]
    )

    document_nfce_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFCe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '65')]
    )

    document_cfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '59')]
    )

    document_cfeecf_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe ECF Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', '60')]
    )

    document_nfse_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFce Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', 'SE')]
    )

    document_rl_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="RL Documents",
        inverse_name="close_id",
        domain=[('document_type', '=', 'RL')]
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Other accountant files",
    )

    company_id = fields.Many2one(
        'res.company',
        string="Empresas"
    )

    file_icms = fields.Binary(string='ICMS')
    file_icms_st = fields.Binary(string='ICMS ST')
    file_ipi = fields.Binary(string='IPI')
    file_iss = fields.Binary(string='ISS')
    file_pis = fields.Binary(string='PIS')
    file_cofins = fields.Binary(string='COFINS')
    file_csll = fields.Binary(string='CSLL')
    file_irpj = fields.Binary(string='IRPJ')
    file_simples = fields.Binary(string='Simples')
    file_honorarios = fields.Binary(string='Accountant Fee')

    block = fields.Boolean(string='Block period', help="Avoid new fiscal moves")

    notes = fields.Text(string="Accountant notes")

    def monta_caminho(self, document):
        document_path = '/'.join([
            # TODO: Colocar ambiente
            # PATH_AMBIENTE[documento.nfe_environment],
            misc.punctuation_rm(document.company_cnpj_cpf),
            PATH_MODELO[document.document_type_id.code],
            document.date.strftime("%m-%Y"),
            document.document_serie_id.code.zfill(3) +
            ('-' + misc.punctuation_rm(str(document.number)).zfill(9)
             if self.group_folder else '')
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

    def _prepara_arquivos(self, temp_dir, periodic_export=False):
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

        domain += [
            ('company_id', '=', self.company_id.ids)
        ] if self.company_id else []

        documents = self.env['l10n_br_fiscal.document'].search(domain)
        # documents += self.env['l10n_br_fiscal.document_correction'].search(domain)
        # documents += self.env['l10n_br_fiscal.document_cancel'].search(domain)


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
                    document_path = document_path + '/' + anexo.datas_fname
                    filename = os.path.join(temp_dir.name, document_path)

                    if not os.path.exists(os.path.dirname(filename)):
                        try:
                            os.makedirs(os.path.dirname(filename))
                        except OSError as exc:
                            raise

                        with open(filename, 'wb') as file:
                            file.write(base64.b64decode(anexo.datas))

            except Exception:
                _logger.error(_('Replication failed: document attachments '
                                '[id =% s] is not present in the database.'
                                % document.id))
        return temp_dir.name

    def zipdir(self, path, ziph):
        for root, dirs, files in os.walk(path):
            for file in files:
                zip_path = re.sub(".*/odoo/.*?/.", "/", root)
                ziph.writestr(os.path.join(zip_path, file), file)

    def action_export(self):
        temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd())

        files_dir = self._prepara_arquivos(temp_dir)
        order_file = io.BytesIO()
        order_zip = zipfile.ZipFile(
            order_file, mode="w", compression=zipfile.ZIP_DEFLATED
        )

        self.zipdir(files_dir, order_zip)
        temp_dir.cleanup()

        order_zip.close()
        self.write({
            'zip_file': base64.b64encode(order_file.getvalue()),
            'state': 'open'
        })

    def action_close(self):
        """ Sobrescrever este método para, notificar seguidores,
        processar documentos anexos, criar contas a pagar"""
        self.state = 'closed'
