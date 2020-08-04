# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import xml.etree.ElementTree as ET
from datetime import datetime
from erpbrasil.base import misc
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

from odoo import models, _
from odoo.exceptions import ValidationError
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

    def cancelar_documento(self):
        for record in self.filtered(fiter_processador_edoc_nfse_ginfes):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(doc_numero=self.number)

            if processo.webservice == 'CancelarNfseV3':
                mensagem_completa = ''
                situacao = True
                retorno = ET.fromstring(processo.retorno)
                nsmap = {'tipo': 'http://www.ginfes.com.br/tipos_v03.xsd'}

                sucesso = retorno.findall(".//tipo:Sucesso", namespaces=nsmap)
                if not sucesso:
                    mensagem_erro = retorno.findall(
                        ".//tipo:Mensagem", namespaces=nsmap)[0].text
                    correcao = retorno.findall(
                        ".//tipo:Correcao", namespaces=nsmap)[0].text
                    codigo = retorno.findall(
                        ".//tipo:Codigo", namespaces=nsmap)[0].text
                    mensagem_completa += (
                        codigo + ' - ' + mensagem_erro +
                        ' - Correção: ' + correcao + '\n')
                    situacao = False

                return situacao, mensagem_completa

    def action_consultar_nfse_rps(self):
        for record in self.filtered(fiter_processador_edoc_nfse_ginfes):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                self.rps_number, self.document_serie, self.rps_type)

            retorno = ET.fromstring(processo.retorno)
            nsmap = {'consulta': 'http://www.ginfes.com.br/servico_consultar_'
                                 'nfse_rps_resposta_v03.xsd',
                     'tipo': 'http://www.ginfes.com.br/tipos_v03.xsd'}
            if processo.webservice == 'ConsultarNfsePorRpsV3':
                enviado = retorno.findall(
                    ".//consulta:CompNfse", namespaces=nsmap)
                nao_encontrado = retorno.findall(
                    ".//tipo:MensagemRetorno", namespaces=nsmap)

                if enviado:
                    # NFS-e já foi enviada

                    cancelada = retorno.findall(
                        ".//tipo:NfseCancelamento", namespaces=nsmap)

                    if cancelada:
                        # NFS-e enviada foi cancelada

                        data = retorno.findall(
                            ".//tipo:DataHora", namespaces=nsmap)[0].text
                        data = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S').\
                            strftime("%m/%d/%Y")
                        mensagem = _('NFS-e cancelada em ' + data)
                        raise ValidationError(_(mensagem))

                    else:
                        numero = retorno.findall(".//tipo:InfNfse/tipo:Numero",
                                                 namespaces=nsmap)[0].text
                        cnpj_prestador = retorno.findall(
                            ".//tipo:IdentificacaoPrestador/tipo:Cnpj",
                            namespaces=nsmap)[0].text
                        razao_social_prestador = retorno.findall(
                            ".//tipo:PrestadorServico/tipo:RazaoSocial",
                            namespaces=nsmap)[0].text

                        varibles_error = []

                        if numero != self.number:
                            varibles_error.append('Número')
                        if cnpj_prestador != misc.punctuation_rm(
                                self.company_cnpj_cpf):
                            varibles_error.append('CNPJ do prestador')
                        if razao_social_prestador != self.company_legal_name:
                            varibles_error.append('Razão Social de pestrador')

                        if varibles_error:
                            mensagem = 'Os seguintes campos não condizem com' \
                                       ' o provedor NFS-e: \n'
                            mensagem += '\n'.join(varibles_error)
                            raise ValidationError(_(mensagem))
                        else:
                            # TODO: Mensagem de sucesso
                            pass

                elif nao_encontrado:
                    # NFS-e não foi enviada

                    mensagem_erro = retorno.findall(
                        ".//tipo:Mensagem", namespaces=nsmap)[0].text
                    correcao = retorno.findall(
                        ".//tipo:Correcao", namespaces=nsmap)[0].text
                    codigo = retorno.findall(
                        ".//tipo:Codigo", namespaces=nsmap)[0].text
                    mensagem = (
                        codigo + ' - ' + mensagem_erro +
                        ' - Correção: ' + correcao + '\n'
                    )

                    raise ValidationError(_(mensagem))

                else:
                    mensagem = _('Erro desconhecido.')
                    raise ValidationError(_(mensagem))
