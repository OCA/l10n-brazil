# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

import os
import base64

from odoo.tools import config
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from erpbrasil.base import misc
from erpbrasil.base.fiscal import edoc

from ..constants.fiscal import (
    EVENT_ENVIRONMENT,
    EVENT_ENVIRONMENT_PROD,
    EVENT_ENVIRONMENT_HML,
)

_logger = logging.getLogger(__name__)

CODIGO_NOME = {"55": "nf-e", "SE": "nfs-e", "65": "nfc-e"}


def caminho_empresa(company_id):
    db_name = company_id._cr.dbname
    cnpj = misc.punctuation_rm(company_id.cnpj_cpf)

    filestore = config.filestore(db_name)
    path = "/".join([filestore, "edoc", cnpj])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            raise UserError(
                _("Erro!"),
                _(
                    """Verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            )
    return path


class Event(models.Model):
    _name = 'l10n_br_fiscal.event'
    _description = 'Fiscal Event'

    create_date = fields.Datetime(
        string='Create Date',
        readonly=True,
        index=True,
    )

    write_date = fields.Datetime(
        string='Write Date',
        readonly=True,
        index=True,
    )

    type = fields.Selection(
        selection=[
            ('-1', 'Exception'),
            ('0', 'Envio Lote'),
            ('1', 'Consulta Recibo'),
            ('2', 'Cancelamento'),
            ('3', 'Inutilização'),
            ('4', 'Consulta NFE'),
            ('5', 'Consulta Situação'),
            ('6', 'Consulta Cadastro'),
            ('7', 'DPEC Recepção'),
            ('8', 'DPEC Consulta'),
            ('9', 'Recepção Evento'),
            ('10', 'Download'),
            ('11', 'Consulta Destinadas'),
            ('12', 'Distribuição DFe'),
            ('13', 'Manifestação'),
            ('14', 'Carta de Correção'),
        ],
        string='Service',
    )

    origin = fields.Char(
        string='Source Document',
        size=64,
        readonly=True,
        help='Document reference that generated this event.',
    )

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        index=True,
    )

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string='Fiscal Document Type',
        index=True,
        required=True,
    )

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.serie',
        required=True,
    )

    document_number = fields.Char(
        required=True,
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        index=True,
    )

    invalidate_number_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.invalidate.number',
        string='Invalidate Number',
        index=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        index=True,
        required=True,
    )

    sequence = fields.Char(
        string='Sequence',
        help='Fiscal Document Event Sequence',
    )

    justification = fields.Char(
        string='Justification',
        size=255,
    )

    display_name = fields.Char(
        string='name',
        compute='_compute_display_name',
    )

    file_request_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML',
        copy=False,
        readony=True,
    )

    file_response_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML Response',
        copy=False,
        readony=True,
    )

    path_file_request = fields.Char(
        string='Request File Path',
        readonly=True,
    )

    path_file_response = fields.Char(
        string='Response File Path',
        readonly=True,
    )

    status_code = fields.Char(
        string='Status Code',
        readonly=True,
    )

    response = fields.Char(
        string='Response Message',
        readonly=True,
    )

    message = fields.Char(
        string='Message',
        readonly=True,
    )

    protocol_date = fields.Datetime(
        string='Protocol Date',
        readonly=True,
        index=True,
    )

    protocol_number = fields.Char(
        string='Protocol Number',
    )

    state = fields.Selection(
        selection=[
            ('draft', _('Draft')),
            ('send', _('Sending')),
            ('wait', _('Waiting Response')),
            ('done', _('Response received')),
        ],
        string='Status',
        readonly=True,
        index=True,
        default='draft',
    )

    environment = fields.Selection(
        selection=EVENT_ENVIRONMENT,
    )

    @api.multi
    @api.constrains('justification')
    def _check_justification(self):
        if len(self.justification) < 15:
            raise UserError(_('Justification must be at least 15 characters.'))
        return True

    @api.model
    def create(self, values):
        values['date'] = fields.Datetime.now()
        return super().create(values)

    @api.multi
    @api.depends(
        'document_id.number',
        'document_id.partner_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.document_id:
                names = [
                    _('Fiscal Document'),
                    record.document_id.number,
                    record.document_id.partner_id.name,
                ]

                record.display_name = " / ".join(filter(None, names))
            else:
                record.display_name = ''

    @staticmethod
    def monta_caminho(
            company_id, ambiente, tipo_documento, ano, mes, serie=False, numero=False):
        caminho = caminho_empresa(company_id)

        if ambiente not in (EVENT_ENVIRONMENT_PROD, EVENT_ENVIRONMENT_HML):
            _logger.error(
                'Ambiente não informado, salvando na pasta de Homologação!')

        if ambiente == EVENT_ENVIRONMENT_PROD:
            caminho = os.path.join(caminho, "producao/")
        else:
            caminho = os.path.join(caminho, "homologacao/")

        caminho = os.path.join(caminho, tipo_documento)
        caminho = os.path.join(caminho, ano + "-" + mes + "/")
        if serie and numero:
            caminho = os.path.join(caminho, serie + "-" + numero + "/")

        try:
            os.makedirs(caminho)
        except:
            pass
        return caminho

    def _grava_arquivo_disco(self, arquivo, file_name, tipo_documento, ano, mes, serie, numero):
        save_dir = self.monta_caminho(
            ambiente=self.environment,
            company_id=self.company_id,
            tipo_documento=tipo_documento,
            ano=ano,
            mes=mes,
            serie=serie,
            numero=numero,
        )
        file_path = os.path.join(save_dir, file_name)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            f = open(file_path, "w")
        except IOError:
            raise UserError(
                _("Erro!"),
                _(
                    """Não foi possível salvar o arquivo
                    em disco, verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            )
        else:
            f.write(arquivo)
            f.close()
        return file_path

    def _grava_anexo(
        self, arquivo, extensao_sem_ponto, autorizacao=False, sequencia=False
    ):
        self.ensure_one()

        if self.document_id and self.document_id.key and self.document_id.document_electronic:
            chave = edoc.detectar_chave_edoc(self.document_id.key)
            tipo_documento = chave.prefixo
            ano = chave.ano_emissao
            mes = chave.mes_emissao
            serie = chave.numero_serie
            numero = chave.numero_documento
            file_name = self.document_id.key

        else:
            tipo_documento = self.document_type_id.prefix
            serie = self.document_serie_id.code
            numero = self.document_number
            file_name = numero

            if self.document_id:
                ano = self.document_id.date.strftime("%Y")
                mes = self.document_id.date.strftime("%m")
            elif self.invalidate_number_id:
                ano = self.invalidate_number_id.date.strftime("%Y")
                mes = self.invalidate_number_id.date.strftime("%m")

        if autorizacao:
            file_name += "-proc"
        if sequencia:
            file_name += str(sequencia) + "-"

        if extensao_sem_ponto:
            file_name += ('.' + extensao_sem_ponto)

        file_path = self._grava_arquivo_disco(
            arquivo,
            file_name,
            tipo_documento=tipo_documento,
            ano=str(ano).zfill(4),
            mes=str(mes).zfill(2),
            serie=str(serie),
            numero=str(numero),
        )

        ir_attachment_id = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=", file_name),
            ]
        )
        ir_attachment_id.unlink()

        attachment_id = ir_attachment_id.create(
            {
                "name": file_name,
                "datas_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(arquivo.encode("utf-8")),
                "mimetype": "application/" + extensao_sem_ponto,
                "type": "binary",
            }
        )

        if autorizacao:
            vals = {
                "path_file_response": file_path,
                "file_response_id": attachment_id.id
            }
        else:
            vals = {
                "path_file_request": file_path,
                "file_request_id": attachment_id.id
            }
        self.write(vals)
        return attachment_id

    @api.multi
    def set_done(self, status_code, response, protocol_date,
                 protocol_number, file_response_xml):
        self._grava_anexo(file_response_xml, 'xml', autorizacao=True)
        self.write({
            'state': 'done',
            'status_code': status_code,
            'response': response,
            'protocol_date': protocol_date,
            'protocol_number': protocol_number,
        })

    def gerar_evento(
            self, company_id, environment, event_type, xml_file,
            document_id=False, invalidate_number_id=False, sequence=False):
        event_obj = self.env["l10n_br_fiscal.event"]
        vals = {
            "company_id": company_id.id,
            "environment": environment,
            "type": event_type,
            "create_date": fields.Datetime.now(),
        }
        if sequence:
            vals['sequence'] = sequence
        if document_id:
            #
            #  Aplicado para envio, cancelamento, carta de correcao
            # e outras operações em que o documento esta presente.
            #
            vals['document_id'] = document_id.id
            vals['document_type_id'] = document_id.document_type_id.id
            vals['document_serie_id'] = document_id.document_serie_id.id
            vals['document_number'] = document_id.number

        if invalidate_number_id:
            #
            #  Aplicado para inutilização
            #
            vals['invalidate_number_id'] = invalidate_number_id.id
            vals['document_type_id'] = invalidate_number_id.document_type_id.id
            vals['document_serie_id'] = invalidate_number_id.document_serie_id.id
            if invalidate_number_id.number_end != invalidate_number_id.number_start:
                vals['document_number'] = \
                    str(invalidate_number_id.number_start) + \
                    '-' + str(invalidate_number_id.number_end)
            else:
                vals['document_number'] = invalidate_number_id.number_start

        event_id = event_obj.create(vals)
        event_id._grava_anexo(xml_file, "xml")
        return event_id