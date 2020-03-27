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


PROCESSADOR_ERPBRASIL_EDOC = 'erpbrasil_edoc'
PROCESSADOR = [(PROCESSADOR_ERPBRASIL_EDOC, 'erpbrasil.edoc')]


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
                "nfe.40.tendereco", "nfe.40.tenderemi",
                "nfe.40.dest", "nfe.40.emit"]
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
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="fiscal_document_id",
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
    nfe40_tpImp = fields.Selection(default='1')
    nfe40_tpEmis = fields.Selection(default='1')
    nfe40_tpAmb = fields.Selection(default='2')
    nfe40_procEmi = fields.Selection(default='0')
    nfe40_verProc = fields.Char(default='Odoo Brasil v12.0')

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
            record.date = fields.Datetime.now()
            record.date_in_out = fields.Datetime.now()

        super(NFe, self).action_document_confirm()

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
        self.nfe40_vBC = sum(self.line_ids.mapped('nfe40_vBC'))
        self.nfe40_vICMS = sum(self.line_ids.mapped('nfe40_vICMS'))
        self.nfe40_vPIS = sum(self.line_ids.mapped('nfe40_vPIS'))
        self.nfe40_vIPI = self.amount_ipi_value
        self.nfe40_vCOFINS = sum(
            self.line_ids.mapped('nfe40_vCOFINS'))
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
        if not self[field_name] and not xsd_required:
            if not any(self[f] for f in self[field_name]._fields
                       if self._fields[f]._attrs.get('xsd')) and \
                    field_name not in ['nfe40_PIS', 'nfe40_COFINS']:
                return False
        if field_name == 'nfe40_ISSQNtot' and all(
                t == 'consu' for t in
                self.nfe40_det.mapped('product_id.type')
        ):
            self[field_name] = False
            return False
        return super(NFe, self)._export_many2one(
            field_name, xsd_required, class_obj)

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

    def _build_many2one(self, comodel, vals, new_value, key, create_m2o):
        if self._name == 'account.invoice' and \
                comodel._name == 'l10n_br_fiscal.document':
            # stacked m2o
            vals.update(new_value)
        else:
            super(NFe, self)._build_many2one(comodel, vals, new_value,
                                             key, create_m2o)
