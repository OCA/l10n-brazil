# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import tempfile
from unicodedata import normalize

from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.edoc.pdf import base
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import etree
from nfelib.v4_00 import retEnviNFe as leiauteNFe
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    DENEGADO,
    CANCELADO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.spec_driven_model.models import spec_models
from odoo.exceptions import UserError
from requests import Session

from odoo import _, api, fields
from ..constants.nfe import (
    NFE_ENVIRONMENTS,
    NFE_VERSIONS,
)

_logger = logging.getLogger(__name__)


def filter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR_OCA and
            record.document_type_id.code in [
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
            ]):
        return True
    return False


class NFe(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document'
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe", "nfe.40.infadic"]
    _stacked = 'nfe.40.infnfe'
    _stack_skip = ('nfe40_veicTransp')
    _field_prefix = 'nfe40_'
    _schema_name = 'nfe'
    _schema_version = '4.0.0'
    _odoo_module = 'l10n_br_nfe'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _spec_tab_name = 'NFe'
    _stacking_points = {}
#    _concrete_skip = ('nfe.40.det',) # will be mixed in later
    _nfe_search_keys = ['nfe40_Id']

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ('infnfe.total', 'infnfe.infAdic')

    def _compute_emit(self):
        for doc in self:  # TODO if out
            doc.nfe40_emit = doc.company_id

    # emit and dest are not related fields as their related fields
    # can change depending if it's and incoming our outgoing NFe
    # specially when importing (ERP NFe migration vs supplier Nfe).
    nfe40_emit = fields.Many2one('res.company', compute='_compute_emit',
                                 readonly=True, string="Emit")

    def _compute_dest(self):
        for doc in self:  # TODO if out
            doc.nfe40_dest = doc.partner_id

    nfe40_dest = fields.Many2one('res.partner', compute='_compute_dest',
                                 readonly=True, string="Dest")

    fiscal_document_event_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.event',
        inverse_name='fiscal_document_id',
        string='Fiscal Events',
        copy=False,
    )

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS,
        string='NFe Version',
        default=lambda self: self.env.user.company_id.nfe_version,
    )

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string='NFe Environment',
        default=lambda self: self.env.user.company_id.nfe_environment,
    )

    nfe40_finNFe = fields.Selection(
        related='edoc_purpose',
    )

    nfe40_versao = fields.Char(
        related='document_version',
    )

    nfe40_nNF = fields.Char(
        related='number',
    )

    nfe40_Id = fields.Char(
        related='key',
    )

    # TODO should be done by framework?
    nfe40_det = fields.One2many(
        comodel_name='l10n_br_fiscal.document.line',
        inverse_name='document_id',
        related='line_ids',
    )

    nfe40_NFref = fields.One2many(
        related='fiscal_document_related_ids',
        comodel_name='l10n_br_fiscal.document.related',
        inverse_name='fiscal_document_id',
    )

    nfe40_dhEmi = fields.Datetime(
        related='date',
    )

    nfe40_dhSaiEnt = fields.Datetime(
        related='date_in_out',
    )

    nfe40_natOp = fields.Char(
        related='operation_name',
    )

    nfe40_serie = fields.Char(
        related='document_serie'
    )

    nfe40_indFinal = fields.Selection(
        related='ind_final',
    )

    nfe40_indPres = fields.Selection(
        related='ind_pres',
    )

    nfe40_vNF = fields.Monetary(
        related='amount_total',
    )

    nfe40_tpAmb = fields.Selection(
        related='nfe_environment',
    )

    nfe40_indIEDest = fields.Selection(
        related='partner_ind_ie_dest',
        string='Contribuinte do ICMS (NFe)'
    )

    nfe40_tpNF = fields.Selection(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_tpNF',
    )

    nfe40_tpImp = fields.Selection(
        default='1',
    )

    nfe40_modFrete = fields.Selection(
        default='9',
    )

    nfe40_tpEmis = fields.Selection(
        default='1',
    )

    nfe40_procEmi = fields.Selection(
        default='0',
    )

    nfe40_verProc = fields.Char(
        default='Odoo Brasil v12.0',  # Shound be an ir.parameter?
    )

    nfe40_CRT = fields.Selection(
        related='company_tax_framework',
        string='Código de Regime Tributário (NFe)',

    )

    nfe40_vFrete = fields.Monetary(
        related='amount_freight_value',
    )

    nfe40_vFCPUFDest = fields.Monetary(
        related='amount_icmsfcp_value',
    )

    nfe40_vDesc = fields.Monetary(
        related='amount_discount_value')

    nfe40_vTotTrib = fields.Monetary(
        related='amount_estimate_tax'
    )
    nfe40_vBC = fields.Monetary(
        related='amount_icms_base'
    )

    nfe40_vICMS = fields.Monetary(
        related='amount_icms_value'
    )

    nfe40_vPIS = fields.Monetary(
        related='amount_pis_value'
    )

    nfe40_vIPI = fields.Monetary(
        related='amount_ipi_value'
    )

    nfe40_vCOFINS = fields.Monetary(
        related='amount_cofins_value'
    )

    nfe40_infAdFisco = fields.Char(
        compute='_compute_nfe40_additional_data',
    )

    nfe40_infCpl = fields.Char(
        compute='_compute_nfe40_additional_data',
    )

    nfe40_infRespTec = fields.Many2one(
        related='company_id.technical_support_id'
    )

    @api.depends('fiscal_additional_data', 'fiscal_additional_data')
    def _compute_nfe40_additional_data(self):
        for record in self:
            if record.fiscal_additional_data:
                record.nfe40_infAdFisco = normalize(
                    'NFKD', record.fiscal_additional_data
                ).encode('ASCII', 'ignore').decode('ASCII').replace(
                    '\n', '').replace('\r', '')
            if record.customer_additional_data:
                record.nfe40_infCpl = normalize(
                    'NFKD', record.customer_additional_data
                ).encode('ASCII', 'ignore').decode('ASCII').replace(
                    '\n', '').replace('\r', '')

    @api.multi
    @api.depends('fiscal_operation_type')
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            operation_2_tpNF = {
                'out': '1',
                'in': '0',
            }
            rec.nfe40_tpNF = operation_2_tpNF[rec.fiscal_operation_type]

    def _inverse_nfe40_tpNF(self):
        for rec in self:
            if rec.nfe40_tpNF:
                tpNF_2_operation = {
                    '1': 'out',
                    '0': 'in',
                }
                rec.fiscal_operation_type = tpNF_2_operation[rec.nfe40_tpNF]

    @api.multi
    def document_number(self):
        super().document_number()
        if self.key:
            chave = ChaveEdoc(self.key)
            self.nfe40_cNF = chave.codigo_aleatorio
            self.nfe40_cDV = chave.digito_verificador

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in (self.with_context(
                       {'lang': 'pt_BR'}).filtered(filter_processador_edoc_nfe)):
            inf_nfe = record.export_ds()[0]

            tnfe = leiauteNFe.TNFe(
                infNFe=inf_nfe,
                infNFeSupl=None,
                Signature=None)
            tnfe.original_tagname_ = 'NFe'

            edocs.append(tnfe)

        return edocs

    def _processador(self):
        if not self.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao, self.company_id.state_id.ibge_code,
            versao=self.nfe_version, ambiente=self.nfe_environment
        )

    @api.multi
    def _document_export(self, pretty_print=True):
        super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfe):
            record._export_fields_pagamentos()
            edoc = record.serialize()[0]
            processador = record._processador()
            xml_file = processador.\
                _generateds_to_string_etree(edoc, pretty_print=pretty_print)[0]
            _logger.debug(xml_file)
            event_id = self._gerar_evento(xml_file, event_type="0")
            record.autorizacao_event_id = event_id

    def atualiza_status_nfe(self, infProt):
        self.ensure_one()
        # if not infProt.chNFe == self.key:
        #     self = self.search([
        #         ('key', '=', infProt.chNFe)
        #     ])

        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA

        self._change_state(state)

        self.write({
            'codigo_situacao': infProt.cStat,
            'motivo_situacao': infProt.xMotivo,
            'data_hora_autorizacao': infProt.dhRecbto,
            'protocolo_autorizacao': infProt.nProt,
        })

    def _prepare_amount_financial(self, ind_pag, t_pag, v_pag):
        return {
            'nfe40_indPag': ind_pag,
            'nfe40_tPag': t_pag,
            'nfe40_vPag': v_pag,
        }

    def _export_fields_pagamentos(self):
        if not self.amount_financial:
            self.nfe40_detPag = [
                (5, 0, 0),
                (0, 0, self._prepare_amount_financial('0', '90', 0.00))
            ]
        self.nfe40_detPag.__class__._field_prefix = 'nfe40_'

    @api.multi
    def _eletronic_document_send(self):
        super(NFe, self)._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfe):
            record._export_fields_pagamentos()
            processador = record._processador()
            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p
                    if processo.webservice == 'nfeAutorizacaoLote':
                        self.autorizacao_event_id._grava_anexo(
                            processo.envio_xml.decode('utf-8'), "xml"
                        )

            if processo.resposta.cStat in LOTE_PROCESSADO + ['100']:
                protocolos = processo.resposta.protNFe
                if type(protocolos) != list:
                    protocolos = [protocolos]
                for protocolo in protocolos:
                    nfe_proc = leiauteNFe.TNfeProc(
                        NFe=edoc,
                        protNFe=protocolo,
                    )
                    nfe_proc.original_tagname_ = 'nfeProc'
                    xml_file = \
                        processador._generateds_to_string_etree(nfe_proc)[0]
                    record.autorizacao_event_id.set_done(xml_file)
                    record.atualiza_status_nfe(protocolo.infProt)
                    if protocolo.infProt.cStat in AUTORIZADO:
                        try:
                            record.gera_pdf()
                        except Exception as e:
                            # Não devemos interromper o fluxo
                            # E dar rollback em um documento
                            # autorizado, podendo perder dados.

                            # Se der problema que apareça quando
                            # o usuário clicar no gera PDF novamente.
                            _logger.error('DANFE Error \n {}'.format(e))

            elif processo.resposta.cStat == '225':
                state = SITUACAO_EDOC_REJEITADA

                self._change_state(state)

                self.write({
                    'codigo_situacao': processo.resposta.cStat,
                    'motivo_situacao': processo.resposta.xMotivo,
                })
        return

    @api.multi
    def cancel_invoice_online(self, justificative):
        super(NFe, self).cancel_invoice_online(justificative)
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.state in ('open', 'paid'):
                processador = record._processador()

                evento = processador.cancela_documento(
                    chave=record.edoc_access_key,
                    protocolo_autorizacao=record.edoc_protocol_number,
                    justificativa=justificative
                )
                processo = processador.enviar_lote_evento(
                    lista_eventos=[evento]
                )

                for retevento in processo.resposta.retEvento:
                    if not retevento.infEvento.chNFe == record.edoc_access_key:
                        continue

                    if retevento.infEvento.cStat not in CANCELADO:
                        mensagem = 'Erro no cancelamento'
                        mensagem += '\nCódigo: ' + \
                                    retevento.infEvento.cStat
                        mensagem += '\nMotivo: ' + \
                                    retevento.infEvento.xMotivo
                        raise UserError(mensagem)

                    if retevento.infEvento.cStat == '155':
                        record.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
                        record.state_edoc = SITUACAO_EDOC_CANCELADA
                    elif retevento.infEvento.cStat == '135':
                        record.state_fiscal = SITUACAO_FISCAL_CANCELADO
                        record.state_edoc = SITUACAO_EDOC_CANCELADA

    # def cce_invoice_online(self, justificative):
    #     super(NFe, self).cce_invoice_online(justificative)
    #     for record in self.filtered(filter_processador_edoc_nfe):
    #         if record.state in ('open', 'paid'):
    #             processador = record._processador()
    #
    #             evento = processador.carta_correcao(
    #                 chave=record.edoc_access_key,
    #                 sequencia='1',
    #                 justificativa=justificative
    #             )
    #             processo = processador.enviar_lote_evento(
    #                 lista_eventos=[evento]
    #             )
    #             pass

    @api.multi
    def action_document_confirm(self):
        for record in self:
            if not record.date_in_out:
                record.date_in_out = fields.Datetime.now()
        super(NFe, self).action_document_confirm()

        for record in self.filtered(filter_processador_edoc_nfe):
            processador = record._processador()
            record.autorizacao_event_id = record._gerar_evento(
                processador._generateds_to_string_etree(
                    record.serialize()[0]
                )[0], event_type="0"
            )

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        if self.company_id.partner_id.state_id.ibge_code:
            self.nfe40_cUF = \
                self.company_id.partner_id.state_id.ibge_code
        if self.document_type_id.code:
            self.nfe40_mod = self.document_type_id.code
        if self.company_id.partner_id.state_id == \
                self.partner_id.state_id:
            self.nfe40_idDest = '1'
        elif self.company_id.partner_id.country_id == \
                self.partner_id.country_id:
            self.nfe40_idDest = '2'
        else:
            self.nfe40_idDest = '3'
        self.nfe40_cMunFG = '%s%s' % (
            self.company_id.partner_id.state_id.ibge_code,
            self.company_id.partner_id.city_id.ibge_code)
        return super(NFe, self)._export_fields(
            xsd_fields, class_obj, export_dict)

    def _export_field(self, xsd_field, class_obj, member_spec):
        if xsd_field in ('nfe40_vICMSUFDest', 'nfe40_vICMSUFRemet'):
            if self.ind_final == '1' and self.nfe40_idDest == '2' and \
                    self.nfe40_indIEDest == '9':
                self.nfe40_vICMSUFDest = sum(
                    self.line_ids.mapped('nfe40_vICMSUFDest'))
                self.nfe40_vICMSUFRemet = sum(
                    self.line_ids.mapped('nfe40_vICMSUFRemet'))
        if xsd_field == 'nfe40_tpAmb':
            self.env.context = dict(self.env.context)
            self.env.context.update({'tpAmb': self[xsd_field]})
        return super(NFe, self)._export_field(
            xsd_field, class_obj, member_spec)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        self.ensure_one()
        if field_name in self._stacking_points.keys():
            if field_name == 'nfe40_ISSQNtot' and not any(
                    t == 'issqn' for t in
                    self.nfe40_det.mapped('product_id.tax_icms_or_issqn')
            ):
                return False

            elif (not xsd_required) and field_name not in ['nfe40_enderDest']:
                comodel = self.env[self._stacking_points.get(
                    field_name).comodel_name]
                fields = [f for f in comodel._fields
                          if f.startswith(self._field_prefix)]
                sub_tag_read = self.read(fields)[0]
                if not any(v for k, v in sub_tag_read.items()
                           if k.startswith(self._field_prefix)):
                    return False

        return super(NFe, self)._export_many2one(field_name, xsd_required, class_obj)

    def _export_float_monetary(self, field_name, member_spec, class_obj,
                               xsd_required):
        if field_name == 'nfe40_vProd' and \
                class_obj._name == 'nfe.40.icmstot':
            self[field_name] = sum(
                self['nfe40_det'].mapped('nfe40_vProd'))
        return super(NFe, self)._export_float_monetary(
            field_name, member_spec, class_obj, xsd_required)

    def _export_one2many(self, field_name, class_obj=None):
        res = super(NFe, self)._export_one2many(field_name, class_obj)
        i = 0
        for field_data in res:
            i += 1
            if class_obj._fields[field_name].comodel_name == 'nfe.40.det':
                field_data.nItem = i
        return res

    def _build_attr(self, node, fields, vals, path, attr):
        key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
        value = getattr(node, attr.get_name())

        if key == 'nfe40_mod':
            vals['document_section'] = 'nfe' if value == '55' else False
            vals['document_type_id'] = \
                self.env['l10n_br_fiscal.document.type'].search([
                    ('code', '=', value)], limit=1).id

        return super(NFe, self)._build_attr(node, fields, vals, path, attr)

    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        if key == 'nfe40_emit' and self.env.context.get('edoc_type') == 'in':
            enderEmit_value = (self.env['res.partner'].build_attrs(value.enderEmit,
                               path=path))
            new_value.update(enderEmit_value)
            new_value['is_company'] = True
            new_value['cnpj_cpf'] = new_value.get('nfe40_CNPJ')
            super()._build_many2one(self.env['res.partner'],
                                    vals, new_value,
                                    'partner_id', value, path)
        elif self.env.context.get('edoc_type') == 'in'\
                and key in ['nfe40_dest', 'nfe40_enderDest']:
            # this would be the emit/company data, but we won't update it on
            # NFe import so just do nothing
            return
        elif self._name == 'account.invoice'\
                and comodel._name == 'l10n_br_fiscal.document':
            # module l10n_br_account_nfe
            # stacked m2o
            vals.update(new_value)
        else:
            super(NFe, self)._build_many2one(comodel, vals, new_value,
                                             key, value, path)

    def gera_pdf(self):
        file_pdf = self.file_pdf_id
        self.file_pdf_id = False
        file_pdf.unlink()
        output = self.autorizacao_event_id.monta_caminho(
            ambiente=self.nfe40_tpAmb,
            company_id=self.company_id,
            chave=self.key,
        )

        if self.file_xml_autorizacao_id:
            arquivo = output + self.file_xml_autorizacao_id.datas_fname
        else:
            tmp_xml = tempfile.NamedTemporaryFile()
            self.temp_xml_autorizacao(tmp_xml)
            arquivo = tmp_xml.name

        base.ImprimirXml.imprimir(caminho_xml=arquivo, output_dir=output)
        file_name = 'danfe.pdf'
        with open(output + file_name, 'rb') as f:
            arquivo_data = f.read()

        self.file_pdf_id = self.env['ir.attachment'].create(
            {
                "name": file_name,
                "datas_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(arquivo_data),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )

    def view_pdf(self):
        if not self.file_pdf_id:
            self.gera_pdf()
        return super(NFe, self).view_pdf()

    def temp_xml_autorizacao(self, tmp_xml):
        """ TODO: Migrate-me to erpbrasil.edoc.pdf ASAP"""
        xml_string = base64.b64decode(self.file_xml_id.datas).decode()
        root = etree.fromstring(xml_string)

        ns = {None: 'http://www.portalfiscal.inf.br/nfe'}
        new_root = etree.Element('nfeProc', nsmap=ns)

        protNFe_node = etree.Element('protNFe')
        infProt = etree.SubElement(protNFe_node, 'infProt')
        etree.SubElement(infProt, 'tpAmb').text = '2'
        etree.SubElement(infProt, 'verAplic').text = ''
        etree.SubElement(infProt, 'dhRecbto').text = None
        etree.SubElement(infProt, 'nProt').text = ''
        etree.SubElement(infProt, 'digVal').text = ''
        etree.SubElement(infProt, 'cStat').text = ''
        etree.SubElement(infProt, 'xMotivo').text = ''

        new_root.append(root)
        new_root.append(protNFe_node)

        tmp_xml.write(etree.tostring(new_root))
        tmp_xml.seek(0)
