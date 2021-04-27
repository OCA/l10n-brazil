# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from requests import Session
import logging

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.base import misc
from erpbrasil.edoc.provedores.cidades import NFSeFactory

from odoo import api, fields, models
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    TAX_FRAMEWORK_SIMPLES_ALL,
    DOCUMENT_ISSUER_COMPANY,
    PROCESSADOR_OCA,
)
from ..constants.nfse import (
    NFSE_ENVIRONMENTS,
    OPERATION_NATURE,
    RPS_TYPE,
    TAXATION_SPECIAL_REGIME,
)

_logger = logging.getLogger(__name__)


def filter_processador_edoc_nfse(record):
    if (record.processador_edoc == PROCESSADOR_OCA and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor(record):
    if record.company_id.provedor_nfse:
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    edoc_error_message = fields.Text(
        readonly=True,
        copy=False,
    )

    rps_number = fields.Char(
        string='RPS Number',
        copy=False,
        index=True,
    )
    rps_type = fields.Selection(
        string='RPS Type',
        selection=RPS_TYPE,
        default='1',
    )
    operation_nature = fields.Selection(
        string='Operation Nature',
        selection=OPERATION_NATURE,
        default='1',
    )
    taxation_special_regime = fields.Selection(
        string='Taxation Special Regime',
        selection=TAXATION_SPECIAL_REGIME,
        default='1',
    )
    verify_code = fields.Char(
        string='Verify Code',
        readonly=True,
        copy=False,
    )
    nfse_environment = fields.Selection(
        selection=NFSE_ENVIRONMENTS,
        string="NFSe Environment",
        default=lambda self: self.env.user.company_id.nfse_environment,
    )

    @api.multi
    def document_date(self):
        super().document_date()
        for record in self.filtered(filter_processador_edoc_nfse):
            if not record.date_in_out:
                record.date_in_out = fields.Datetime.now()

    def document_number(self):
        for record in self.filtered(filter_processador_edoc_nfse):
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                if record.document_serie_id:
                    record.document_serie = record.document_serie_id.code
                    if not record.rps_number and record.date:
                        record.rps_number = record.document_serie_id.\
                            next_seq_number()
                        record.number = record.rps_number
        super(Document, self - self.filtered(filter_processador_edoc_nfse)
              ).document_number()

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_nfse):
            return super().make_pdf()
        pdf = self.env.ref(
            'l10n_br_nfse.report_br_nfse_danfe').render_qweb_pdf(self.ids)[0]
        self.file_pdf_id.unlink()
        self.file_pdf_id = self.env['ir.attachment'].create(
            {
                "name": "self.rps_number or self.number",
                "datas_fname": "self.rps_number or self.number",
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(pdf),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )

    def _processador_erpbrasil_nfse(self):
        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return NFSeFactory(
            transmissao=transmissao,
            ambiente=self.nfse_environment,
            cidade_ibge=int('%s%s' % (
                self.company_id.partner_id.state_id.ibge_code,
                self.company_id.partner_id.city_id.ibge_code
            )),
            cnpj_prestador=misc.punctuation_rm(
                self.company_id.partner_id.cnpj_cpf),
            im_prestador=misc.punctuation_rm(
                self.company_id.partner_id.inscr_mun or ''),
        )

    @api.multi
    def _document_export(self, pretty_print=True):
        super(Document, self)._document_export()
        for record in self.filtered(filter_processador_edoc_nfse):
            edoc = record.serialize()[0]
            processador = record._processador_erpbrasil_nfse()
            xml_file = processador.\
                _generateds_to_string_etree(edoc, pretty_print=pretty_print)[0]
            event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment='prod' if self.nfse_environment == '1' else 'hml',
                event_type="0",
                xml_file=xml_file,
                document_id=self,
            )
            _logger.debug(xml_file)
            record.authorization_event_id = event_id

    def _prepare_dados_servico(self):
        self.line_ids.ensure_one()
        result = {

        }
        result.update(self.line_ids.prepare_line_servico())
        result.update(self.company_id.prepare_company_servico())

        return result

    def _prepare_dados_tomador(self):
        result = self.partner_id.prepare_partner_tomador(
            self.company_id.country_id.id)

        result.update(
            {'complemento': self.partner_shipping_id.street2 or None})

        return result

    def _prepare_lote_rps(self):
        num_rps = self.rps_number
        return {
            'cnpj': misc.punctuation_rm(self.company_id.partner_id.cnpj_cpf),
            'inscricao_municipal': misc.punctuation_rm(
                self.company_id.partner_id.inscr_mun or '') or None,
            'id': 'rps' + str(num_rps),
            'numero': num_rps,
            'serie': self.document_serie_id.code or '',
            'tipo': self.rps_type,
            'data_emissao': fields.Datetime.context_timestamp(
                self, fields.Datetime.from_string(self.date)
            ).strftime('%Y-%m-%dT%H:%M:%S'),
            'date_in_out': fields.Datetime.context_timestamp(
                self, self.date_in_out).strftime('%Y-%m-%dT%H:%M:%S'),
            'natureza_operacao': self.operation_nature,
            'regime_especial_tributacao': self.taxation_special_regime,
            'optante_simples_nacional': '1'
            if self.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
            else '2',
            'incentivador_cultural': '1'
            if self.company_id.cultural_sponsor else '2',
            'status': '1',
            'rps_substitiuido': None,
            'intermediario_servico': None,
            'construcao_civil': None,
            'carga_tributaria': self.amount_tax,
            'total_recebido': self.amount_total,
        }

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ''
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get('type', '').\
                    replace('xsd:', '')
                break

        if value_type in ('int', 'byte', 'nonNegativeInteger'):
            return int(value)
        elif value_type == 'decimal':
            return float(value)
        elif value_type == 'string':
            return str(value)
        else:
            return value
