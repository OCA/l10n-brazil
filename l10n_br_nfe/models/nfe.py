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
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe"]
    _stacked = 'nfe.40.infnfe'
    _stack_skip = ('nfe40_veicTransp')
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
#    _concrete_skip = ('nfe.40.det',) # will be mixed in later
    _nfe_search_keys = ['nfe40_Id']

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ('infnfe.total',)

    nfe40_finNFe = fields.Selection(
        related='edoc_purpose',
    )

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

    nfe40_dhEmi = fields.Datetime(
        related='date'
    )

    nfe40_dhSaiEnt = fields.Datetime(
        related='date_in_out'
    )

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

    nfe40_natOp = fields.Char(
        related='operation_name'
    )

    nfe40_serie = fields.Char(
        related='document_serie'
    )

    nfe40_indFinal = fields.Selection(
        related='ind_final'
    )

    nfe40_indPres = fields.Selection(
        related='ind_pres'
    )

    nfe40_vNF = fields.Monetary(
        related='amount_total'
    )
    nfe40_tpNF = fields.Selection(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_tpNF',
    )

    @api.depends('operation_type')
    @api.multi
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            operation_2_tpNF = {
                'out': '1',
                'in': '0',
            }
            rec.nfe40_tpNF = operation_2_tpNF[rec.operation_type]

    def _inverse_nfe40_tpNF(self):
        for rec in self:
            if rec.nfe40_tpNF:
                tpNF_2_operation = {
                    '1': 'out',
                    '0': 'in',
                }
                rec.operation_type = tpNF_2_operation[rec.nfe40_tpNF]

    # cce_document_ids = fields.One2many(
    #     comodel_name="l10n_br_account.invoice.cce",
    #     inverse_name="fiscal_document_event_ids",
    #     string=u"Carta de correção",
    #     copy=False,
    # )

    def _generate_key(self):
        key = super()._generate_key()
        if self.document_type_id.code == MODELO_FISCAL_NFE:
            # TODO Deveria estar no erpbrasil.base.fiscal
            company = self.company_id.partner_id
            chave = str(company.state_id and
                        company.state_id.ibge_code or "").zfill(2)

            chave += self.date.strftime("%y%m").zfill(4)

            chave += str(misc.punctuation_rm(
                self.company_id.partner_id.cnpj_cpf)).zfill(14)
            chave += str(self.document_type_id.code or "").zfill(2)
            chave += str(self.document_serie or "").zfill(3)
            chave += str(self.number or "").zfill(9)

            #
            # A inclusão do tipo de emissão na chave já torna a chave válida
            # também para a versão 2.00 da NF-e
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
                codigo = codigo.rjust(8, "0")

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
            # FIXME: Fazer sufixo depender do modelo
            key = 'NFe' + chave
        return key

    @api.multi
    def document_number(self):
        super(NFe, self).document_number()
        if len(self.key) == 47:
            self.nfe40_cNF = self.key[38:-1]
            self.nfe40_cDV = self.key[-1]

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

            if processo.resposta.cStat in LOTE_PROCESSADO + ['100']:
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

    @api.multi
    def action_document_confirm(self):
        for record in self:
            if record.company_id.partner_id.state_id.ibge_code:
                record.nfe40_cUF = \
                    record.company_id.partner_id.state_id.ibge_code
            if record.document_type_id.code:
                record.nfe40_mod = record.document_type_id.code
            record.date = fields.Datetime.now()
            record.date_in_out = fields.Datetime.now()
            if record.operation_id.operation_type == 'in':
                record.nfe40_tpNF = '0'
            else:
                record.nfe40_tpNF = '1'
            if record.company_id.partner_id.state_id == \
                    record.partner_id.state_id:
                record.nfe40_idDest = '1'
            elif record.company_id.partner_id.country_id == \
                    record.partner_id.country_id:
                record.nfe40_idDest = '2'
            else:
                record.nfe40_idDest = '3'
            record.nfe40_cMunFG = '%s%s' % (
                record.company_id.partner_id.state_id.ibge_code,
                record.company_id.partner_id.city_id.ibge_code)
            record.nfe40_tpImp = '1'
            record.nfe40_tpEmis = '1'
            record.nfe40_tpAmb = '2'
            record.nfe40_procEmi = '0'
            record.nfe40_verProc = 'Odoo Brasil v12.0'
            record.nfe40_vBC = sum(record.line_ids.mapped('nfe40_vBC'))
            record.nfe40_vICMS = sum(record.line_ids.mapped('nfe40_vICMS'))
            record.nfe40_vPIS = sum(record.line_ids.mapped('nfe40_vPIS'))
            record.nfe40_vIPI = record.amount_ipi_value
            record.nfe40_vCOFINS = sum(
                record.line_ids.mapped('nfe40_vCOFINS'))
            for line in record.line_ids:
                line.nfe40_NCM = line.ncm_id.code.replace('.', '')
                line.nfe40_CEST = line.cest_id and line.cest_id.code.replace('.', '') or False
                line.nfe40_CFOP = line.cfop_id.code
                line.nfe40_qCom = line.quantity
                line.nfe40_qTrib = line.quantity
                line.nfe40_indTot = '1'
                line.nfe40_pICMS = line.icms_percent
                line.nfe40_pIPI = line.ipi_percent
                line.nfe40_vIPI = line.ipi_value
                line.nfe40_cEnq = str(line.ipi_guideline_id.code or '999'
                                      ).zfill(3)
                line.nfe40_pPIS = line.pis_percent
                line.nfe40_pCOFINS = line.cofins_percent
                if record.ind_final == '1' and record.nfe40_idDest == '2' and \
                        record.partner_id.nfe40_indIEDest == '9':
                    line.nfe40_vBCUFDest = line.nfe40_vBC
                    if record.partner_id.state_id.code in [
                            'AC', 'CE', 'ES', 'GO', 'MT', 'MS', 'PA',
                            'PI', 'RR', 'SC']:
                        line.nfe40_pICMSUFDest = 17.0
                    elif record.partner_id.state_id.code == 'RO':
                        line.nfe40_pICMSUFDest = 17.5
                    elif record.partner_id.state_id.code in [
                            'AM', 'AP', 'BA', 'DF', 'MA', 'MG', 'PB', 'PR',
                            'PE', 'RN', 'RS', 'SP', 'SE', 'TO']:
                        line.nfe40_pICMSUFDest = 18.0
                    elif record.partner_id.state_id.code == 'RJ':
                        line.nfe40_pICMSUFDest = 20.0
                    line.nfe40_pICMSInter = '7.00'
                    line.nfe40_pICMSInterPart = 100.0
                    line.nfe40_vICMSUFDest = (
                        line.nfe40_vBCUFDest * (
                            (line.nfe40_pICMSUFDest - float(
                                line.nfe40_pICMSInter)
                             ) / 100) * (line.nfe40_pICMSInterPart / 100))
                    line.nfe40_vICMSUFRemet = (
                        line.nfe40_vBCUFDest * (
                            (line.nfe40_pICMSUFDest - float(
                                line.nfe40_pICMSInter)
                             ) / 100) * ((100 - line.nfe40_pICMSInterPart
                                          ) / 100))
            if record.ind_final == '1' and record.nfe40_idDest == '2' and \
                    record.partner_id.nfe40_indIEDest == '9':
                record.nfe40_vICMSUFDest = sum(
                    record.line_ids.mapped('nfe40_vICMSUFDest'))
                record.nfe40_vICMSUFRemet = sum(
                    record.line_ids.mapped('nfe40_vICMSUFRemet'))

        super(NFe, self).action_document_confirm()


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
    nfe40_uTrib = fields.Char(related='product_id.uom_id.code')
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

    nfe40_choice11 = fields.Selection(
        compute='_compute_choice11',
        store=True,
    )

    nfe40_choice12 = fields.Selection(
        compute='_compute_choice12',
        store=True,
    )

    nfe40_choice15 = fields.Selection(
        compute='_compute_choice15',
        store=True,
    )

    nfe40_choice3 = fields.Selection(
        compute='_compute_choice3',
        store=True,
    )

    nfe40_choice20 = fields.Selection(
        compute='_compute_nfe40_choice20',
        store=True,
    )

    nfe40_orig = fields.Selection(
        related='icms_origin'
    )

    nfe40_modBC = fields.Selection(
        related='icms_base_type'
    )

    nfe40_vBC = fields.Monetary(
        related='icms_base'
    )

    nfe40_vICMS = fields.Monetary(
        related='icms_value'
    )

    nfe40_vPIS = fields.Monetary(
        related='pis_value'
    )

    nfe40_vCOFINS = fields.Monetary(
        related='cofins_value'
    )

    @api.depends('icms_cst_id')
    def _compute_choice11(self):
        for record in self:
            if record.icms_cst_id.code == '00':
                record.nfe40_choice11 = 'nfe40_ICMS00'
            elif record.icms_cst_id.code == '10':
                record.nfe40_choice11 = 'nfe40_ICMS10'
            elif record.icms_cst_id.code == '20':
                record.nfe40_choice11 = 'nfe40_ICMS20'
            elif record.icms_cst_id.code == '30':
                record.nfe40_choice11 = 'nfe40_ICMS30'
            elif record.icms_cst_id.code in ['40', '41', '50']:
                record.nfe40_choice11 = 'nfe40_ICMS40'
            elif record.icms_cst_id.code == '51':
                record.nfe40_choice11 = 'nfe40_ICMS51'
            elif record.icms_cst_id.code == '60':
                record.nfe40_choice11 = 'nfe40_ICMS60'
            elif record.icms_cst_id.code == '70':
                record.nfe40_choice11 = 'nfe40_ICMS70'
            elif record.icms_cst_id.code == '90':
                record.nfe40_choice11 = 'nfe40_ICMS90'
            elif record.icms_cst_id.code == '400':
                record.nfe40_choice11 = 'nfe40_ICMSSN102'

    @api.depends('pis_cst_id')
    def _compute_choice12(self):
        for record in self:
            if record.pis_cst_id.code in ['01', '02']:
                record.nfe40_choice12 = 'nfe40_PISAliq'
            elif record.pis_cst_id.code == '03':
                record.nfe40_choice12 = 'nfe40_PISQtde'
            elif record.pis_cst_id.code in ['04', '06', '07', '08', '09']:
                record.nfe40_choice12 = 'nfe40_PISNT'
            else:
                record.nfe40_choice12 = 'nfe40_PISOutr'

    @api.depends('cofins_cst_id')
    def _compute_choice15(self):
        for record in self:
            if record.cofins_cst_id.code in ['01', '02']:
                record.nfe40_choice15 = 'nfe40_COFINSAliq'
            elif record.cofins_cst_id.code == '03':
                record.nfe40_choice15 = 'nfe40_COFINSQtde'
            elif record.cofins_cst_id.code in ['04', '06', '07', '08', '09']:
                record.nfe40_choice15 = 'nfe40_COFINSNT'
            else:
                record.nfe40_choice15 = 'nfe40_COFINSOutr'

    @api.depends('ipi_cst_id')
    def _compute_choice3(self):
        for record in self:
            if record.ipi_cst_id.code in ['00', '49', '50', '99']:
                record.nfe40_choice3 = 'nfe40_IPITrib'
            else:
                record.nfe40_choice3 = 'nfe40_IPINT'

    @api.depends('ipi_base_type')
    def _compute_nfe40_choice20(self):
        for record in self:
            if record.ipi_base_type == 'percent':
                record.nfe40_choice20 = 'nfe40_pIPI'
            else:
                record.nfe40_choice20 = 'nfe40_vUnid'

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
        elif class_obj._name == 'nfe.40.ipitrib':
            xsd_fields = [i for i in xsd_fields]
            # if class_obj._fields['nfe40_choice20'] == 'nfe40_pIPI':
            xsd_fields.remove('nfe40_qUnid')
            xsd_fields.remove('nfe40_vUnid')
            # else:
            #     xsd_fields.remove('nfe40_vBC')
            #     xsd_fields.remove('nfe40_pIPI')
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


class IPITrib(models.AbstractModel):
    _inherit = 'nfe.40.ipitrib'

    def _export_field(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == self._inherit:
            xsd_fields = [i for i in xsd_fields]
            if class_obj._fields['nfe40_choice20'] == 'nfe40_pIPI':
                xsd_fields.remove('nfe40_qUnid')
                xsd_fields.remove('nfe40_vUnid')
            else:
                xsd_fields.remove('nfe40_vBC')
                xsd_fields.remove('nfe40_pIPI')

        return super(NFeLine, self)._export_field(
            xsd_fields, class_obj, export_dict)
