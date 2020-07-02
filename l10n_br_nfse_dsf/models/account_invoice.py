# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unicodedata import normalize
from nfselib.dsf.Tipos import (
    tpRPS,
    tpDeducoes,
    tpItens,
    tpLote,
)
from nfselib.dsf.ReqEnvioLoteRPS import (
    ReqEnvioLoteRPS,
    CabecalhoType,
)

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm
from odoo.addons.edoc_base.constantes import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_A_ENVIAR,
)
from odoo.addons.edoc_nfse.models.res_company import PROCESSADOR


def fiter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR and
            record.fiscal_document_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_dsf(record):
    if record.company_id.provedor_nfse == 'dsf':
        return True
    return False


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def _serialize(self, edocs):
        edocs = super(AccountInvoice, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfe).filtered(fiter_provedor_dsf):
            edocs.append(record.serialize_nfse_dsf())
        return edocs

    def serialize_nfse_dsf(self):
        dh_emi = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_hour_invoice)
        )

        numero_rps = self.fiscal_number

        lista_rps = []

        if self.partner_id.is_company:
            tomador_cnpj = punctuation_rm(
                self.partner_id.cnpj_cpf or '')
            tomador_cpf = None
        else:
            tomador_cnpj = None
            tomador_cpf = punctuation_rm(
                self.partner_id.cnpj_cpf or '')

        if self.partner_id.country_id.id != self.company_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
        else:
            address_invoice_state_code = self.partner_id.state_id.code
            address_invoice_city = (normalize(
                'NFKD', unicode(
                    self.partner_id.l10n_br_city_id.name or '')).encode(
                'ASCII', 'ignore'))
            address_invoice_city_code = int(('%s%s') % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.l10n_br_city_id.ibge_code))

        partner_cep = punctuation_rm(self.partner_id.zip)

        prestador_cnpj = punctuation_rm(self.company_id.partner_id.cnpj_cpf)
        prestador_im = punctuation_rm(
            self.company_id.partner_id.inscr_mun or '')

        inscricao_tomador = None
        if self.partner_id.l10n_br_city_id ==\
                self.company_id.partner_id.l10n_br_city_id:
            inscricao_tomador = \
                punctuation_rm(self.partner_id.inscr_mun or '') or None

        itens = []
        deducoes = []

        lista_rps.append(
            tpRPS(
                Id='rps' + str(numero_rps),
                Assinatura=None,
                InscricaoMunicipalPrestador=prestador_im or None,
                RazaoSocialPrestador=self.company_id.legal_name and self.company_id.legal_name[:120] or None,
                TipoRPS='RPS',
                SerieRPS='NF',
                NumeroRPS=int(numero_rps),
                DataEmissaoRPS=dh_emi, # AAAA-MM-DDTHH:MM:SS
                SituacaoRPS='N', # Situação RPS “N”-Normal“C”-Cancelada
                # SerieRPSSubstituido=None,
                # NumeroRPSSubstituido=None,
                # NumeroNFSeSubstituida=None,
                # DataEmissaoNFSeSubstituida=None,
                SeriePrestacao=99,
                InscricaoMunicipalTomador=inscricao_tomador,
                CPFCNPJTomador=tomador_cnpj or tomador_cpf or None,
                RazaoSocialTomador=self.partner_id.legal_name or None,
                # DocTomadorEstrangeiro=None,
                TipoLogradouroTomador=None,
                LogradouroTomador=self.partner_id.street or None,
                NumeroEnderecoTomador=self.partner_id.number or None,
                ComplementoEnderecoTomador=self.partner_id.street2 or None, # não obrigatório
                TipoBairroTomador='Bairro',
                BairroTomador=self.partner_id.district or None,
                CidadeTomador=address_invoice_city_code,
                CidadeTomadorDescricao=address_invoice_city,
                CEPTomador=partner_cep,
                EmailTomador=self.partner_id.email,
                CodigoAtividade='412040000',
                AliquotaAtividade=5.00,
                TipoRecolhimento='A',
                MunicipioPrestacao='0006291',
                MunicipioPrestacaoDescricao='CAMPINAS',
                Operacao='A',
                Tributacao='T',
                ValorPIS=str("%.2f" % self.pis_value),
                ValorCOFINS=str("%.2f" % self.cofins_value),
                ValorINSS=None,
                ValorIR=None,
                ValorCSLL=None,
                AliquotaPIS=None,
                AliquotaCOFINS=None,
                AliquotaINSS=None,
                AliquotaIR=None,
                AliquotaCSLL=None,
                DescricaoRPS='Descricao do RPS',
                # DDDPrestador=self.company_id.partner_id.phone and self.company_id.partner_id.phone[2:] or None,
                # TelefonePrestador=self.company_id.partner_id.phone and self.company_id.partner_id.phone[:2] or None,
                # DDDTomador=self.partner_id.phone and self.partner_id.phone[2:] or None,
                # TelefoneTomador=self.partner_id.phone and self.partner_id.phone[:2] or None,
                # MotCancelamento=None,
                # CPFCNPJIntermediario=None,
                Deducoes=deducoes,
                Itens=itens
            )
        )
        lote_rps = ReqEnvioLoteRPS(
            Cabecalho=CabecalhoType(
                CodCidade=None,
                CPFCNPJRemetente=None,
                RazaoSocialRemetente=None,
                transacao=True,
                dtInicio=None,
                dtFim=None,
                QtdRPS=None,
                ValorTotalServicos=None,
                ValorTotalDeducoes=None,
                Versao=None,
                MetodoEnvio=None,
                VersaoComponente=None
            ),
            Lote=tpLote(RPS=lista_rps)
        )

        # tpDeducoes(
        #     DeducaoPor=None,
        #     TipoDeducao=None,
        #     # CPFCNPJReferencia=None,
        #     # NumeroNFReferencia=None,
        #     # ValorTotalReferencia=None,
        #     PercentualDeduzir=None,
        #     ValorDeduzir=None
        # )

        for line in self.invoice_line_ids:
            itens.append(
                tpItens(
                    DiscriminacaoServico=normalize(
                        'NFKD', unicode(line.name[:120] or '')
                    ).encode('ASCII', 'ignore'),
                    Quantidade=line.quantity,
                    ValorUnitario=str("%.2f" % line.price_unit),
                    ValorTotal=str("%.2f" % line.price_gross),
                    Tributavel=None
                )
            )

        return lote_rps
