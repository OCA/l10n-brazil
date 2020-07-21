# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from nfselib.ginfes.v3_01.tipos_v03 import (
    ListaRpsType,
    tcCpfCnpj,
    tcDadosServico,
    tcDadosTomador,
    tcEndereco,
    tcIdentificacaoPrestador,
    tcIdentificacaoRps,
    tcIdentificacaoTomador,
    tcInfRps,
    tcLoteRps,
    tcRps,
    tcValores,
)
from nfselib.ginfes.v3_01.servico_enviar_lote_rps_envio_v03 import \
    EnviarLoteRpsEnvio

from odoo import models
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
)

from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR


def fiter_processador_edoc_nfse_ginfes(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_ginfes(record):
    if record.company_id.provedor_nfse == 'ginfes':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse_ginfes).filtered(
                    fiter_provedor_ginfes):
            edocs.append(record.serialize_nfse_ginfes())
        return edocs

    def _serialize_dados_servico(self):
        self.line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return tcDadosServico(
            Valores=tcValores(
                ValorServicos=dados['valor_servicos'],
                ValorDeducoes=dados['valor_deducoes'],
                ValorPis=dados['valor_pis'],
                ValorCofins=dados['valor_cofins'],
                ValorInss=dados['valor_inss'],
                ValorIr=dados['valor_ir'],
                ValorCsll=dados['valor_csll'],
                IssRetido=dados['iss_retido'],
                ValorIss=dados['valor_iss'],
                ValorIssRetido=dados['valor_iss_retido'],
                OutrasRetencoes=dados['outras_retencoes'],
                BaseCalculo=dados['base_calculo'],
                Aliquota=dados['aliquota'],
                ValorLiquidoNfse=dados['valor_liquido_nfse'],
            ),
            ItemListaServico=dados['item_lista_servico'],
            CodigoCnae=dados['codigo_cnae'],
            CodigoTributacaoMunicipio=dados['codigo_tributacao_municipio'],
            Discriminacao=dados['discriminacao'],
            CodigoMunicipio=dados['codigo_municipio'],
        )

    def _serialize_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return tcDadosTomador(
            IdentificacaoTomador=tcIdentificacaoTomador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=dados['cnpj'],
                    Cpf=dados['cpf'],
                ),
                InscricaoMunicipal=dados['inscricao_municipal']
            ),
            RazaoSocial=dados['razao_social'],
            Endereco=tcEndereco(
                Endereco=dados['endereco'],
                Numero=dados['numero'],
                Complemento=dados['complemento'],
                Bairro=dados['bairro'],
                CodigoMunicipio=dados['codigo_municipio'],
                Uf=dados['uf'],
                Cep=dados['cep'],
            ) or None,
        )

    def _serialize_rps(self, dados):

        return tcRps(
            InfRps=tcInfRps(
                Id=dados['id'],
                IdentificacaoRps=tcIdentificacaoRps(
                    Numero=dados['numero'],
                    Serie=dados['serie'],
                    Tipo=dados['tipo'],
                ),
                DataEmissao=dados['data_emissao'],
                NaturezaOperacao=dados['natureza_operacao'],
                RegimeEspecialTributacao=dados['regime_especial_tributacao'],
                OptanteSimplesNacional=dados['optante_simples_nacional'],
                IncentivadorCultural=dados['incentivador_cultural'],
                Status=dados['status'],
                RpsSubstituido=dados['rps_substitiuido'],
                Servico=self._serialize_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    Cnpj=dados['cnpj'],
                    InscricaoMunicipal=dados['inscricao_municipal'],
                ),
                Tomador=self._serialize_dados_tomador(),
                IntermediarioServico=dados['intermediario_servico'],
                ConstrucaoCivil=dados['construcao_civil'],
            )
        )

    def _serialize_lote_rps(self):
        dados = self._prepare_lote_rps()
        return tcLoteRps(
            Cnpj=dados['cnpj'],
            InscricaoMunicipal=dados['inscricao_municipal'],
            QuantidadeRps='1',
            ListaRps=ListaRpsType(
                Rps=[self._serialize_rps(dados)]
            )
        )

    def serialize_nfse_ginfes(self):
        # numero_lote = 14
        lote_rps = EnviarLoteRpsEnvio(
            LoteRps=self._serialize_lote_rps()
        )
        return lote_rps
