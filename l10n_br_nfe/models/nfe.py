# Copyright 2019 Akretion
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.v4_00 import leiauteNFe
from odoo import api, fields, models, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    DENEGADO,
    CANCELADO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_nfe.sped.nfe.validator import txt
from odoo.addons.spec_driven_model.models import spec_models
from odoo.exceptions import UserError
from requests import Session

from .res_company import PROCESSADOR, PROCESSADOR_ERPBRASIL_EDOC


def fiter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR_ERPBRASIL_EDOC and
            record.document_type_id.code in [
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
            ]):
        return True
    return False


class NFe(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document'
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe",
                "l10n_br_fiscal.document.electronic"]
    _stacked = 'nfe.40.infnfe'
    _stack_skip = ('nfe40_veicTransp')
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
#    _concrete_skip = ('nfe.40.det',) # will be mixed in later
    _nfe_search_keys = ['nfe40_Id']

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ('infnfe.total',)

    nfe40_versao = fields.Char(related='document_version')
    nfe40_nNF = fields.Char(related='number')
    nfe40_Id = fields.Char(related='key')

    nfe40_emit = fields.Many2one(
        related="company_id",
        comodel_name="res.company",
        original_spec_model="nfe.40.emit",
    )

    nfe40_dest = fields.Many2one(
        related='partner_id',
        comodel_name='res.partner'
    )  # TODO in invoice

    # TODO should be done by framework?
    nfe40_det = fields.One2many(related='line_ids',
                                comodel_name='l10n_br_fiscal.document.line',
                                inverse_name='document_id')

    processador_edoc = fields.Selection(
        selection_add=PROCESSADOR,
        related='company_id.processador_edoc',
    )

    fiscal_document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document_event",
        inverse_name="fiscal_document_event_id",
        string=u"Eventos",
        copy=False,
    )

    # cce_document_ids = fields.One2many(
    #     comodel_name="l10n_br_account.invoice.cce",
    #     inverse_name="fiscal_document_event_ids",
    #     string=u"Carta de correção",
    #     copy=False,
    # )

    @api.multi
    def document_check(self):
        super(NFe, self).document_check()
        to_check = self.filtered(
            lambda inv: self.document_type_id.code == '55'
        )
        if to_check:
            txt.validate(to_check)

    def _serialize(self, edocs):
        edocs = super(NFe, self)._serialize(edocs)
        for record in self.filtered(fiter_processador_edoc_nfe):
            inf_nfe = record.export_ds()[0]

            tnfe = leiauteNFe.TNFe(
                infNFe=inf_nfe,
                infNFeSupl=None,
                Signature=None)
            tnfe.original_tagname_ = 'NFe'

            edocs.append(tnfe)

        return edocs

    def _procesador(self):
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
            versao='4.00', ambiente='2'
        )

    @api.multi
    def _document_export(self):
        super(NFe, self)._document_export()
        for record in self.filtered(fiter_processador_edoc_nfe):
            edoc = record.serialize()[0]
            procesador = record._procesador()
            xml_file = procesador._generateds_to_string_etree(edoc)[0]
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
            'key': infProt.chNFe,
            'codigo_situacao': infProt.cStat,
            'motivo_situacao': infProt.xMotivo,
            'data_hora_autorizacao': infProt.dhRecbto,
            'protocolo_autorizacao': infProt.nProt,
        })

    @api.multi
    def _eletronic_document_send(self):
        super(NFe, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfe):
            procesador = record._procesador()
            for edoc in record.serialize():
                processo = None
                for p in procesador.processar_documento(edoc):
                    processo = p

            if processo.resposta.cStat in LOTE_PROCESSADO:
                for protocolo in processo.resposta.protNFe:
                    record.atualiza_status_nfe(protocolo.infProt)
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
        for record in self.filtered(fiter_processador_edoc_nfe):
            if record.state in ('open', 'paid'):
                processador = record._procesador()

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
    #     for record in self.filtered(fiter_processador_edoc_nfe):
    #         if record.state in ('open', 'paid'):
    #             processador = record._procesador()
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


class NFeLine(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document.line'
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = 'nfe.40.det'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _stack_skip = 'nfe40_det_infNFe_id'
    # all m2o below this level will be stacked even if not required:
    _force_stack_paths = ('det.imposto',)
    _rec_name = 'nfe40_xProd'

    nfe40_cProd = fields.Char(related='product_id.default_code')
    nfe40_xProd = fields.Char(related='product_id.name')
    nfe40_cEAN = fields.Char(related='product_id.barcode')
    nfe40_cEANTrib = fields.Char(related='product_id.barcode')
    nfe40_uCom = fields.Char(related='product_id.uom_id.code')
    nfe40_vUnCom = fields.Float(related='price')  # TODO sure?
    nfe40_vUnTrib = fields.Float(related='fiscal_price')  # TODO sure?

    nfe40_choice9 = fields.Selection([
        ('normal', 'Produto Normal'),  # overriden to allow normal product
        ('nfe40_veicProd', 'Veículo'),
        ('nfe40_med', 'Medicamento'),
        ('nfe40_arma', 'Arma'),
        ('nfe40_comb', 'Combustível'),
        ('nfe40_nRECOPI', 'Número do RECOPI')],
        "Típo de Produto",
        default="normal")

    def _export_field(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == 'nfe.40.icms':
            xsd_fields = [self.nfe40_choice11]
        elif class_obj._name == 'nfe.40.tipi':
            xsd_fields = [f for f in xsd_fields if f not in [
                i[0] for i in class_obj._fields['nfe40_choice3'].selection]]
            xsd_fields += [self.nfe40_choice3]
        elif class_obj._name == 'nfe.40.pis':
            xsd_fields = [self.nfe40_choice12]
        elif class_obj._name == 'nfe.40.cofins':
            xsd_fields = [self.nfe40_choice15]
        return super(NFeLine, self)._export_field(
            xsd_fields, class_obj, export_dict)


class ResCity(models.Model):
    _inherit = "res.city"
    _nfe_search_keys = ['ibge_code']

    # TODO understand why this is still required
    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        "if city not found, break hard, don't create it"
        if parent_dict.get('nfe40_cMun') or parent_dict.get('nfe40_cMunFG'):
            ibge_code = parent_dict.get('nfe40_cMun',
                                        parent_dict.get('nfe40_cMunFG'))
            ibge_code = ibge_code[2:8]
            domain = [('ibge_code', '=', ibge_code)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False


class Uom(models.Model):
    _inherit = "uom.uom"

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        "if uom not found, break hard, don't create it"
        if rec_dict.get('name'):
            # TODO FIXME where are the BR unit names supposed to live?
            BR2ODOO = {'UN': 'Unit(s)', 'LU': 'Liter(s)'}
            name = BR2ODOO.get(rec_dict['name'], rec_dict['name'])
            domain = [('name', '=', name)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _nfe_search_keys = ['ibge_code', 'code']
    _nfe_extra_domain = [('ibge_code', '!=', False)]
