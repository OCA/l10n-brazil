# Copyright 2019 Akretion
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.edoc.pdf import base
from nfelib.v4_00 import leiauteNFe
from odoo import api, fields, _
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
    NFE_IND_IE_DEST, NFE_IND_IE_DEST_DEFAULT,
)
from odoo.addons.l10n_br_nfe.sped.nfe.validator import txt
from odoo.addons.spec_driven_model.models import spec_models
from odoo.exceptions import UserError
from ..constants.nfe import (NFE_ENVIRONMENT_DEFAULT, NFE_ENVIRONMENTS,
                             NFE_VERSION_DEFAULT, NFE_VERSIONS)
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

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS, string="NFe Version",
        default=lambda self: self.env.user.company_id.nfe_version,
    )

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string="NFe Environment",
        default=lambda self: self.env.user.company_id.nfe_environment,
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
    nfe40_tpAmb = fields.Selection(
        related='nfe_environment'
    )
    nfe40_indIEDest = fields.Selection(
        related='partner_ind_ie_dest'
    )
    nfe40_tpNF = fields.Selection(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_tpNF',
    )
    nfe40_tpImp = fields.Selection(default='1')
    nfe40_modFrete = fields.Selection(default='9')
    nfe40_tpEmis = fields.Selection(default='1')
    nfe40_procEmi = fields.Selection(default='0')
    nfe40_verProc = fields.Char(default='Odoo Brasil v12.0')
    nfe40_CRT = fields.Selection(
        related='company_tax_framework'
    )

    partner_ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string=u"Contribuinte do ICMS",
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT,
    )

    company_street = fields.Char(string="Rua")
    company_number = fields.Char(string="Número")
    company_street2 = fields.Char(string="Complemento")
    company_district = fields.Char(string="Bairro")
    company_country_id = fields.Many2one(
        string="País",
        comodel_name='res.country',
    )
    company_state_id = fields.Many2one(
        string="Estado",
        comodel_name='res.country.state',
        domain="[('country_id', '=', company_country_id)]",
    )
    company_city_id = fields.Many2one(
        string="Cidade",
        comodel_name='res.city',
        domain="[('state_id', '=', company_state_id)]",
    )
    company_zip = fields.Char(string="CEP")
    company_phone = fields.Char(string="Telefone")

    partner_street = fields.Char(string="Rua")
    partner_number = fields.Char(string="Número")
    partner_street2 = fields.Char(string="Complemento")
    partner_district = fields.Char(string="Bairro")
    partner_country_id = fields.Many2one(
        string="País",
        comodel_name='res.country',
    )
    partner_state_id = fields.Many2one(
        string="Estado",
        comodel_name='res.country.state',
        domain="[('country_id', '=', partner_country_id)]",
    )
    partner_city_id = fields.Many2one(
        string="Cidade",
        comodel_name='res.city',
        domain="[('state_id', '=', partner_state_id)]",
    )
    partner_zip = fields.Char(string="CEP")
    partner_phone = fields.Char(string="Telefone")
    partner_is_company = fields.Boolean(string="É uma empresa")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        super(NFe, self)._onchange_company_id()
        if self.company_id:
            self.company_street = self.company_id.street
            self.company_street2 = self.company_id.street2
            self.company_district = self.company_id.district
            self.company_country_id = self.company_id.country_id
            self.company_state_id = self.company_id.state_id
            self.company_city_id = self.company_id.city_id
            self.company_zip = self.company_id.zip
            self.company_phone = self.company_id.phone
            self.env.cr.execute('select street_number from res_partner '
                                'where id=%s' % self.company_id.partner_id.id)
            [(self.company_number,)] = self.env.cr.fetchall()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(NFe, self)._onchange_partner_id()
        if self.partner_id:
            self.partner_street = self.partner_id.street
            self.partner_number = self.partner_id.street_number
            self.partner_street2 = self.partner_id.street2
            self.partner_district = self.partner_id.district
            self.partner_country_id = self.partner_id.country_id
            self.partner_state_id = self.partner_id.state_id
            self.partner_city_id = self.partner_id.city_id
            self.partner_zip = self.partner_id.zip
            self.partner_phone = self.partner_id.phone
            self.partner_ind_ie_dest = self.partner_id.ind_ie_dest
            self.partner_is_company = \
                self.partner_id.company_type == 'company'
            self.env.cr.execute('select street_number from res_partner '
                                'where id=%s' % self.partner_id.id)
            [(self.partner_number,)] = self.env.cr.fetchall()

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
            versao=self.nfe_version, ambiente=self.nfe_environment
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
                        procesador._generateds_to_string_etree(nfe_proc)[0]
                    record.autorizacao_event_id.set_done(xml_file)
                    record.atualiza_status_nfe(protocolo.infProt)
                    record.gera_pdf()
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

        if xsd_field == 'nfe40_CNPJ':
            if class_obj._name == 'nfe.40.emit':
                if self.company_cnpj_cpf:
                    return self.company_cnpj_cpf.replace(
                        '.', '').replace('/', '').replace('-', '')
            elif class_obj._name == 'nfe.40.dest' and self.partner_is_company:
                if self.partner_cnpj_cpf:
                    return self.partner_cnpj_cpf.replace(
                        '.', '').replace('/', '').replace('-', '')
        if xsd_field == 'nfe40_CPF':
            if class_obj._name == 'nfe.40.dest' and \
                    not self.partner_is_company:
                if self.partner_cnpj_cpf:
                    return self.partner_cnpj_cpf.replace(
                        '.', '').replace('/', '').replace('-', '')
        if xsd_field == 'nfe40_xNome':
            if class_obj._name == 'nfe.40.emit':
                if self.company_legal_name:
                    return self.company_legal_name
            if class_obj._name == 'nfe.40.dest':
                if self.nfe40_tpAmb == '2':
                    return 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO ' \
                           '- SEM VALOR FISCAL'
                if self.partner_legal_name:
                    return self.partner_legal_name
        if xsd_field == 'nfe40_IE':
            if class_obj._name == 'nfe.40.emit':
                if self.company_inscr_est:
                    return self.company_inscr_est.replace('.', '')
            if class_obj._name == 'nfe.40.dest':
                if self.partner_inscr_est:
                    return self.partner_inscr_est.replace('.', '')
        if xsd_field == 'nfe40_ISUF':
            if class_obj._name == 'nfe.40.emit':
                if self.company_suframa:
                    return self.company_suframa
            if class_obj._name == 'nfe.40.dest':
                if self.partner_suframa:
                    return self.partner_suframa

        if xsd_field == 'nfe40_xLgr':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_street:
                    return self.company_street
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_street:
                    return self.partner_street
        if xsd_field == 'nfe40_nro':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_number:
                    return self.company_number
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_number:
                    return self.partner_number
        if xsd_field == 'nfe40_xCpl':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_street2:
                    return self.company_street2
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_street2:
                    return self.partner_street2
        if xsd_field == 'nfe40_xBairro':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_district:
                    return self.company_district
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_district:
                    return self.partner_district
        if xsd_field == 'nfe40_cMun':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_state_id and self.company_city_id:
                    return '%s%s' % (self.company_state_id.ibge_code,
                                     self.company_city_id.ibge_code)
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_state_id and self.partner_city_id:
                    return '%s%s' % (self.partner_state_id.ibge_code,
                                     self.partner_city_id.ibge_code)
        if xsd_field == 'nfe40_xMun':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_city_id.name:
                    return self.company_city_id.name
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_city_id.name:
                    return self.partner_city_id.name
        if xsd_field == 'nfe40_UF':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_state_id.code:
                    return self.company_state_id.code
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_state_id.code:
                    return self.partner_state_id.code
        if xsd_field == 'nfe40_CEP':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_zip:
                    return self.company_zip.replace('-', '')
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_zip:
                    return self.partner_zip.replace('-', '')
        if xsd_field == 'nfe40_cPais':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_country_id.ibge_code:
                    return self.company_country_id.ibge_code
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_country_id.ibge_code:
                    return self.partner_country_id.ibge_code
        if xsd_field == 'nfe40_xPais':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_country_id.name:
                    return self.company_country_id.name
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_country_id.name:
                    return self.partner_country_id.name
        if xsd_field == 'nfe40_fone':
            if class_obj._name == 'nfe.40.tenderemi':
                if self.company_phone:
                    return self.company_phone.replace('(', '').replace(
                        ')', '').replace(' ', '').replace(
                        '-', '').replace('+', '')
            if class_obj._name == 'nfe.40.tendereco':
                if self.partner_phone:
                    return self.partner_phone.replace('(', '').replace(
                        ')', '').replace(' ', '').replace(
                        '-', '').replace('+', '')

        return super(NFe, self)._export_field(
            xsd_field, class_obj, member_spec)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if not self[field_name] and not xsd_required:
            if not any(self[f] for f in self[field_name]._fields
                       if self._fields[f]._attrs.get('xsd')) and \
                    field_name not in ['nfe40_PIS', 'nfe40_COFINS',
                                       'nfe40_enderDest']:
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

    def _build_attr(self, node, fields, vals, path, attr, create_m2o,
                    defaults):
        key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
        value = getattr(node, attr.get_name())
        comodel_name = "nfe.40.%s" % (node.original_tagname_,)

        if key == 'nfe40_mod':
            vals['document_section'] = 'nfe' if value == '55' else False
            vals['document_type_id'] = \
                self.env['l10n_br_fiscal.document.type'].search([
                    ('code', '=', value)], limit=1).id

        if key == 'nfe40_CNPJ':
            if comodel_name == 'nfe.40.emit':
                vals['company_cnpj_cpf'] = value
            elif comodel_name == 'nfe.40.dest':
                vals['partner_is_company'] = True
                vals['partner_cnpj_cpf'] = value
        if key == 'nfe40_CPF':
            if comodel_name == 'nfe.40.dest':
                vals['partner_is_company'] = False
                vals['partner_cnpj_cpf'] = value
        if key == 'nfe40_xNome':
            if comodel_name == 'nfe.40.emit':
                vals['company_legal_name'] = value
            if comodel_name == 'nfe.40.dest':
                vals['partner_legal_name'] = value
        if key == 'nfe40_IE':
            if comodel_name == 'nfe.40.emit':
                vals['company_inscr_est'] = value
            if comodel_name == 'nfe.40.dest':
                vals['partner_inscr_est'] = value
        if key == 'nfe40_ISUF':
            if comodel_name == 'nfe.40.emit':
                vals['company_suframa'] = value
            if comodel_name == 'nfe.40.dest':
                vals['partner_suframa'] = value

        if key == 'nfe40_xLgr':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_street'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_street'] = value
        if key == 'nfe40_nro':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_number'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_number'] = value
        if key == 'nfe40_xCpl':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_street2'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_street2'] = value
        if key == 'nfe40_xBairro':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_district'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_district'] = value
        if key == 'nfe40_cMun':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_state_id'] = \
                    self.env['res.country.state'].search([
                        ('ibge_code', '=', value[:2])], limit=1).id
                vals['company_city_id'] = \
                    self.env['res.city'].search([
                        ('ibge_code', '=', value[2:])], limit=1).id
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_state_id'] = \
                    self.env['res.country.state'].search([
                        ('ibge_code', '=', value[:2])], limit=1).id
                vals['partner_city_id'] = \
                    self.env['res.city'].search([
                        ('ibge_code', '=', value[2:])], limit=1).id
        if key == 'nfe40_CEP':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_zip'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_zip'] = value
        if key == 'nfe40_cPais':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_country_id'] = \
                    self.env['res.country'].search([
                        ('ibge_code', '=', value)], limit=1).id
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_country_id'] = \
                    self.env['res.country'].search([
                        ('ibge_code', '=', value)], limit=1).id
        if key == 'nfe40_fone':
            if comodel_name == 'nfe.40.enderEmit':
                vals['company_phone'] = value
            if comodel_name == 'nfe.40.enderDest':
                vals['partner_phone'] = value

        return super(NFe, self)._build_attr(
            node, fields, vals, path, attr, create_m2o, defaults)

    def _build_many2one(self, comodel, vals, new_value, key, create_m2o):
        if self._name == 'account.invoice' and \
                comodel._name == 'l10n_br_fiscal.document':
            # stacked m2o
            vals.update(new_value)
        else:
            super(NFe, self)._build_many2one(comodel, vals, new_value,
                                             key, create_m2o)

    def gera_pdf(self):
        file_pdf = self.file_pdf_id
        self.file_pdf_id = False
        file_pdf.unlink()
        output = self.autorizacao_event_id.monta_caminho(
            ambiente=self.nfe40_tpAmb,
            company_id=self.company_id,
            chave=self.key,
        )
        arquivo = output + self.file_xml_autorizacao_id.datas_fname
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
