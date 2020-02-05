# Copyright 2019 Akretion
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from nfelib.v4_00 import leiauteNFe
from requests import Session
from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.edoc import NFe as edoc_nfe
from erpbrasil.base.misc import punctuation_rm


from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.addons.spec_driven_model.models import spec_models
from datetime import datetime
from odoo.addons.l10n_br_nfe.sped.nfe.validator import txt
from odoo.addons.l10n_br_fiscal.constants.edoc import (
    AUTORIZADO,
    AUTORIZADO_OU_DENEGADO,
    DENEGADO,
    CANCELADO,
    LOTE_EM_PROCESSAMENTO,
    LOTE_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
    SITUACAO_FISCAL_REGIME_ESPECIAL,
    SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU,
    SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA,
)
from .res_company import PROCESSADOR, PROCESSADOR_ERPBRASIL_EDOC


def fiter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR_ERPBRASIL_EDOC and
            record.document_type_id.code in [
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
            ]):
        return True
    return False


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        result = super(IrAttachment, self)._search(
            args, offset, limit, order, count, access_rights_uid
        )
        data = {}
        for arg in args:
            if type(arg) == list:
                field, expression, values = arg
                if field in ("res_model", "res_id"):
                    data[field] = values

        if data.get("res_model") == "l10n_br_fiscal.document":
            res_id = data.get("res_id")
            if res_id:
                invoice_ids = self.env["l10n_br_fiscal.document"].browse(res_id)
                result += (
                    invoice_ids.mapped("file_xml_autorizacao_id").ids +
                    invoice_ids.mapped(
                        "file_xml_autorizacao_cancelamento_id").ids +
                    invoice_ids.mapped("file_pdf_id").ids
                )
        return result


class NFe(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document'
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe",
                "l10n_br_fiscal.document.eletronic"]
    _stacked = 'nfe.40.infnfe'
    _stack_skip = ('nfe40_veicTransp')
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
#    _concrete_skip = ('nfe.40.det',) # will be mixed in later
    _nfe_search_keys = ['nfe40_Id']

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ('infnfe.total',)

    nfe40_versao = fields.Char(related='number')
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
    def edoc_check(self):
        super(NFe, self).edoc_check()
        to_check = self.filtered(
            lambda inv: self.document_type_id.code == '55'
        )
        if to_check:
            result = txt.validate(to_check)
            return result

    def gera_nova_chave(self):
        company = self.company_id.partner_id
        chave = str(company.state_id and
                    company.state_id.ibge_code or '').zfill(2)

        chave += self.date.strftime('%y%m').zfill(4)

        chave += str(punctuation_rm(
            self.company_id.partner_id.cnpj_cpf)).zfill(14)
        chave += str(self.document_type_id.code or '').zfill(2)
        chave += str(self.document_serie or '').zfill(3)
        chave += str(self.number or '').zfill(9)

        #
        # A inclusão do tipo de emissão na chave já torna a chave válida também
        # para a versão 2.00 da NF-e
        #
        chave += str(1).zfill(1)

        #
        # O código numério é um número aleatório
        #
        # chave += str(random.randint(0, 99999999)).strip().rjust(8, '0')

        #
        # Mas, por segurança, é preferível que esse número não seja
        # aleatório de todo
        #
        soma = 0
        for c in chave:
            soma += int(c) ** 3 ** 2

        codigo = str(soma)
        if len(codigo) > 8:
            codigo = codigo[-8:]
        else:
            codigo = codigo.rjust(8, '0')

        chave += codigo

        soma = 0
        m = 2
        for i in range(len(chave) - 1, -1, -1):
            c = chave[i]
            soma += int(c) * m
            m += 1
            if m > 9:
                m = 2

        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0

        chave += str(digito)
        self.key = chave

    def _serialize(self, edocs):
        edocs = super(NFe, self)._serialize(edocs)
        for record in self.filtered(fiter_processador_edoc_nfe):
            edocs.append(record.serialize_nfe())
        return edocs

    def _procesador(self):
        if not self.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = Certificado(
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
    def _edoc_export(self):
        super(NFe, self)._edoc_export()
        for record in self.filtered(fiter_processador_edoc_nfe):
            inf_nfe = record.export_ds()[0]

            tnfe = leiauteNFe.TNFe(
                infNFe=inf_nfe,
                infNFeSupl=None,
                Signature=None)
            tnfe.original_tagname_ = 'NFe'

            procesador = record._procesador()
            xml_file = procesador._generateds_to_string_etree(tnfe)[0]
            event_id = self._gerar_evento(xml_file, type="0")
            record.autorizacao_event_id = event_id
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def atualiza_status_nfe(self, infProt):
        self.ensure_one()
        documento = self
        if not infProt.chNFe == self.edoc_access_key:
            documento = self.search([
                ('edoc_access_key', '=', infProt.chNFe)
            ])

        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA

        self._change_state(state)

        documento.write({
            'edoc_access_key': infProt.chNFe,
            'edoc_status_code': infProt.cStat,
            'edoc_status_message': infProt.xMotivo,
            'edoc_date': infProt.dhRecbto,
            'edoc_protocol_number': infProt.nProt,
            # 'nfe_access_key': infProt.tpAmb,
            # 'nfe_access_key': infProt.digVal,
            # 'nfe_access_key': infProt.xMsg,
        })

    @api.multi
    def _edoc_send(self):
        super(NFe, self)._edoc_send()
        for record in self.filtered(fiter_processador_edoc_nfe):
            procesador = record._procesador()
            for edoc in record.serialize():
                processo = None
                for p in procesador.processar_documento(edoc):
                    processo = p

            if processo.resposta.cStat in LOTE_PROCESSADO:
                for protocolo in processo.resposta.protNFe:
                    record.atualiza_status_nfe(protocolo.infProt)
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

    def cce_invoice_online(self, justificative):
        super(NFe, self).cce_invoice_online(justificative)
        for record in self.filtered(fiter_processador_edoc_nfe):
            if record.state in ('open', 'paid'):
                processador = record._procesador()

                evento = processador.carta_correcao(
                    chave=record.edoc_access_key,
                    sequencia='1',
                    justificativa=justificative
                )
                processo = processador.enviar_lote_evento(
                    lista_eventos=[evento]
                )
                pass


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
    nfe40_uCom = fields.Char(related='product_id.uom_id.name')
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
