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
from erpbrasil.base import misc
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_A_ENVIAR,
)
from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR

#TODO: Manter aqui ou deixar no modulo nfse
def fiter_processador_edoc_nfse(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False

#TODO: Manter aqui ou deixar no modulo nfse
def fiter_provedor_dsf(record):
    if record.company_id.provedor_nfse == 'dsf':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse).filtered(fiter_provedor_dsf):
            edocs.append(record.serialize_nfse_dsf())
        return edocs

    def _prepare_itens(self, itens):
        for line in self.line_ids:
            itens.append(
                tpItens(
                    DiscriminacaoServico=normalize(
                        'NFKD', str(line.name[:120] or '')
                    ).encode('ASCII', 'ignore'),
                    Quantidade=line.quantity,
                    ValorUnitario=str("%.2f" % line.price_unit),
                    ValorTotal=str("%.2f" % line.price_gross),
                    Tributavel=None
                )
            )

    def _prepare_deducoes(self, deducoes):
        # TODO: Popular lista de deduções
        pass

    def serialize_nfse_dsf(self):
        lista_rps = []
        itens = []
        deducoes = []

        dict_servico = self._prepare_dados_servico()
        dict_tomador = self._prepare_dados_tomador()
        dict_rps = self._prepare_lote_rps()

        self._prepare_itens(itens)
        self._prepare_deducoes(deducoes)

        lista_rps.append(
            tpRPS(
                Id=dict_rps['id'],
                Assinatura=None,
                InscricaoMunicipalPrestador=dict_tomador['inscricao_municipal'] or None,
                RazaoSocialPrestador=dict_tomador['razao_social'] and dict_tomador['razao_social'][:120] or None,
                TipoRPS='RPS',
                SerieRPS='NF',
                NumeroRPS=dict_rps['numero'],
                DataEmissaoRPS=dict_rps['data_emissao'], # AAAA-MM-DDTHH:MM:SS
                SituacaoRPS='N', # Situação RPS “N”-Normal“C”-Cancelada
                # SerieRPSSubstituido=None,
                # NumeroRPSSubstituido=None,
                # NumeroNFSeSubstituida=None,
                # DataEmissaoNFSeSubstituida=None,
                SeriePrestacao=99,
                InscricaoMunicipalTomador=dict_tomador['inscricao_municipal'],
                CPFCNPJTomador=dict_tomador['cnpj'] or dict_tomador['cpf'] or None,
                RazaoSocialTomador=dict_tomador['razao_social'] or None,
                # DocTomadorEstrangeiro=None,
                TipoLogradouroTomador=None,
                LogradouroTomador=dict_tomador['endereco'] or None,
                NumeroEnderecoTomador=dict_tomador['numero'] or None,
                ComplementoEnderecoTomador=dict_tomador['complemento'] or None, # não obrigatório
                TipoBairroTomador='Bairro',
                BairroTomador=dict_tomador['bairro'] or None,
                CidadeTomador=dict_tomador['codigo_municipio'],
                CidadeTomadorDescricao=dict_tomador['codigo_municipio'], # TODO: Verificar informação
                CEPTomador=dict_tomador['cep'],
                EmailTomador=dict_tomador['email'],
                CodigoAtividade='412040000',
                AliquotaAtividade=5.00,
                TipoRecolhimento='A',
                MunicipioPrestacao='0006291',
                MunicipioPrestacaoDescricao='CAMPINAS',
                Operacao='A',
                Tributacao='T',
                ValorPIS=str("%.2f" % dict_servico['valor_pis']),
                ValorCOFINS=str("%.2f" % dict_servico['valor_cofins']),
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
                Deducoes=deducoes, # TODO: Lista vazia
                Itens=itens # TODO: Lista vazia
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

        for line in self.line_ids:
            itens.append(
                tpItens(
                    DiscriminacaoServico=normalize(
                        'NFKD', str(line.name[:120] or '')
                    ).encode('ASCII', 'ignore'),
                    Quantidade=line.quantity,
                    ValorUnitario=str("%.2f" % line.price_unit),
                    ValorTotal=str("%.2f" % line.price_gross),
                    Tributavel=None
                )
            )

        return lote_rps
