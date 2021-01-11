# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


# import xml.etree.ElementTree as ET
from nfselib.issnet.v1_00.servico_enviar_lote_rps_envio import (
    EnviarLoteRpsEnvio,
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

from odoo import models, api, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_AUTORIZADA,
)

from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR

from ..constants.issnet import (
    RECEPCIONAR_LOTE_RPS,
    CONSULTAR_SITUACAO_LOTE_RPS,
    # CANCELAR_NFSE,
)


def fiter_processador_edoc_nfse_issnet(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_issnet(record):
    if record.company_id.provedor_nfse == 'issnet':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ''
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get('type', '').\
                    replace('xsd:', '')
                break

        if value_type in ('int', 'byte', 'nonNegativeInteger'):
            return int(value)
        elif value_type == 'decimal':
            return float(value)
        elif value_type == 'string':
            return str(value)
        else:
            return value

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse_issnet).filtered(
                    fiter_provedor_issnet):
            edocs.append(record.serialize_nfse_issnet())
        return edocs

    def _serialize_dados_servico(self):
        self.line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return tcDadosServico(
            Valores=tcValores(
                ValorServicos=self.convert_type_nfselib(
                    tcValores, 'ValorServicos', dados['valor_servicos']),
                ValorDeducoes=self.convert_type_nfselib(
                    tcValores, 'ValorDeducoes', dados['valor_deducoes']),
                ValorPis=self.convert_type_nfselib(
                    tcValores, 'ValorPis', dados['valor_pis']),
                ValorCofins=self.convert_type_nfselib(
                    tcValores, 'ValorCofins', dados['valor_cofins']),
                ValorInss=self.convert_type_nfselib(
                    tcValores, 'ValorInss', dados['valor_inss']),
                ValorIr=self.convert_type_nfselib(
                    tcValores, 'ValorIr', dados['valor_ir']),
                ValorCsll=self.convert_type_nfselib(
                    tcValores, 'ValorCsll', dados['valor_csll']),
                IssRetido=self.convert_type_nfselib(
                    tcValores, 'IssRetido', dados['iss_retido']),
                ValorIss=self.convert_type_nfselib(
                    tcValores, 'ValorIss', dados['valor_iss']),
                ValorIssRetido=self.convert_type_nfselib(
                    tcValores, 'ValorIssRetido', dados['valor_iss_retido']),
                OutrasRetencoes=self.convert_type_nfselib(
                    tcValores, 'OutrasRetencoes', dados['outras_retencoes']),
                BaseCalculo=self.convert_type_nfselib(
                    tcValores, 'BaseCalculo', dados['base_calculo']),
                Aliquota=self.convert_type_nfselib(
                    tcValores, 'Aliquota', str(float(dados['aliquota'])*100)),
                ValorLiquidoNfse=self.convert_type_nfselib(
                    tcValores, 'ValorLiquidoNfse',
                    dados['valor_liquido_nfse']),
                DescontoIncondicionado=0,
                DescontoCondicionado=0,
            ),
            ItemListaServico=self.convert_type_nfselib(
                tcDadosServico, 'ItemListaServico',
                dados['item_lista_servico']),
            CodigoCnae=self.convert_type_nfselib(
                tcDadosServico, 'CodigoCnae', dados['codigo_cnae']),
            CodigoTributacaoMunicipio=self.convert_type_nfselib(
                tcDadosServico, 'CodigoTributacaoMunicipio',
                dados['codigo_tributacao_municipio']),
            Discriminacao=self.convert_type_nfselib(
                tcDadosServico, 'Discriminacao', dados['discriminacao']),
            MunicipioPrestacaoServico=self.convert_type_nfselib(
                tcDadosServico, 'MunicipioPrestacaoServico', dados['codigo_municipio'])
            if self.company_id.nfse_environment == '1'
            else 999,
        )

    def _serialize_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return tcDadosTomador(
            IdentificacaoTomador=tcIdentificacaoTomador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.convert_type_nfselib(
                        tcCpfCnpj, 'Cnpj', dados['cnpj']),
                    Cpf=self.convert_type_nfselib(
                        tcCpfCnpj, 'Cpf', dados['cpf']),
                ),
                InscricaoMunicipal=self.convert_type_nfselib(
                    tcIdentificacaoTomador, 'InscricaoMunicipal',
                    dados['inscricao_municipal'])
                if dados['codigo_municipio'] == int('%s%s' % (
                    self.company_id.partner_id.state_id.ibge_code,
                    self.company_id.partner_id.city_id.ibge_code
                )) else None,
            ),
            RazaoSocial=self.convert_type_nfselib(
                tcDadosTomador, 'RazaoSocial', dados['razao_social']),
            Endereco=tcEndereco(
                Endereco=self.convert_type_nfselib(
                    tcEndereco, 'Endereco', dados['endereco']),
                Numero=self.convert_type_nfselib(
                    tcEndereco, 'Numero', dados['numero']),
                Complemento=self.convert_type_nfselib(
                    tcEndereco, 'Complemento', dados['complemento']),
                Bairro=self.convert_type_nfselib(
                    tcEndereco, 'Bairro', dados['bairro']),
                Cidade=self.convert_type_nfselib(
                    tcEndereco, 'Cidade', dados['codigo_municipio']),
                Estado=self.convert_type_nfselib(tcEndereco, 'Estado', dados['uf']),
                Cep=self.convert_type_nfselib(tcEndereco, 'Cep', dados['cep']),
            ) or None,
        )

    def _serialize_rps(self, dados):

        return tcRps(
            InfRps=tcInfRps(
                id=dados['id'],
                IdentificacaoRps=tcIdentificacaoRps(
                    Numero=self.convert_type_nfselib(
                        tcIdentificacaoRps, 'Numero', dados['numero']),
                    Serie=self.convert_type_nfselib(
                        tcIdentificacaoRps, 'Serie', dados['serie']),
                    Tipo=self.convert_type_nfselib(
                        tcIdentificacaoRps, 'Tipo', dados['tipo']),
                ),
                DataEmissao=self.convert_type_nfselib(
                    tcInfRps, 'DataEmissao', dados['data_emissao']),
                NaturezaOperacao=self.convert_type_nfselib(
                    tcInfRps, 'NaturezaOperacao', dados['natureza_operacao']),
                RegimeEspecialTributacao=self.convert_type_nfselib(
                    tcInfRps, 'RegimeEspecialTributacao',
                    dados['regime_especial_tributacao']),
                OptanteSimplesNacional=self.convert_type_nfselib(
                    tcInfRps, 'OptanteSimplesNacional',
                    dados['optante_simples_nacional']),
                IncentivadorCultural=self.convert_type_nfselib(
                    tcInfRps, 'IncentivadorCultural',
                    dados['incentivador_cultural']),
                Status=self.convert_type_nfselib(
                    tcInfRps, 'Status', dados['status']),
                RpsSubstituido=self.convert_type_nfselib(
                    tcInfRps, 'RpsSubstituido', dados['rps_substitiuido']),
                Servico=self._serialize_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    CpfCnpj=tcCpfCnpj(
                        Cnpj=self.convert_type_nfselib(
                            tcCpfCnpj, 'Cnpj', dados['cnpj']),
                    ),
                    InscricaoMunicipal=self.convert_type_nfselib(
                        tcIdentificacaoPrestador, 'InscricaoMunicipal',
                        dados['inscricao_municipal']),
                ),
                Tomador=self._serialize_dados_tomador(),
                IntermediarioServico=self.convert_type_nfselib(
                    tcInfRps, 'IntermediarioServico',
                    dados['intermediario_servico']),
                ConstrucaoCivil=self.convert_type_nfselib(
                    tcInfRps, 'ConstrucaoCivil', dados['construcao_civil']),
            )
        )

    def _serialize_lote_rps(self):
        dados = self._prepare_lote_rps()
        return tcLoteRps(
            CpfCnpj=tcCpfCnpj(
                Cnpj=self.convert_type_nfselib(
                    tcCpfCnpj, 'Cnpj', dados['cnpj']),
            ),
            InscricaoMunicipal=self.convert_type_nfselib(
                tcLoteRps, 'InscricaoMunicipal', dados['inscricao_municipal']),
            QuantidadeRps=1,
            ListaRps=ListaRpsType(
                Rps=[self._serialize_rps(dados)]
            )
        )

    def serialize_nfse_issnet(self):
        lote_rps = EnviarLoteRpsEnvio(
            LoteRps=self._serialize_lote_rps()
        )
        return lote_rps

    def cancel_document_issnet(self):
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(doc_numero=int(self.number))

            status, message = \
                processador.analisa_retorno_cancelamento(processo)

            return status

    def action_consultar_nfse_rps(self):
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                rps_number=int(self.rps_number),
                document_serie=self.document_serie,
                rps_type=int(self.rps_type)
            )

            return _(
                processador.analisa_retorno_consulta(
                    processo,
                    self.number,
                    self.company_cnpj_cpf,
                    self.company_legal_name)
            )

    @api.multi
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            for record in self.filtered(fiter_provedor_issnet):
                processador = record._processador_erpbrasil_nfse()

                protocolo = record.protocolo_autorizacao
                vals = dict()

                if not protocolo:
                    for edoc in record.serialize():
                        processo = None
                        for p in processador.processar_documento(edoc):
                            processo = p

                            if processo.webservice in RECEPCIONAR_LOTE_RPS:
                                if processo.resposta.Protocolo is None:
                                    mensagem_completa = ''
                                    if processo.resposta.ListaMensagemRetorno:
                                        lista_msgs = processo.resposta.\
                                            ListaMensagemRetorno
                                        for mr in lista_msgs.MensagemRetorno:

                                            correcao = ''
                                            if mr.Correcao:
                                                correcao = mr.Correcao

                                            mensagem_completa += (
                                                mr.Codigo + ' - ' +
                                                mr.Mensagem +
                                                ' - Correção: ' +
                                                correcao + '\n'
                                            )
                                    vals['edoc_error_message'] = \
                                        mensagem_completa
                                    record.write(vals)
                                    return
                                protocolo = processo.resposta.Protocolo

                        if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                            if processo.resposta.Situacao is None:
                                mensagem_completa = ''
                                if processo.resposta.ListaMensagemRetorno:
                                    lista_msgs = processo.resposta. \
                                        ListaMensagemRetorno
                                    for mr in lista_msgs.MensagemRetorno:

                                        correcao = ''
                                        if mr.Correcao:
                                            correcao = mr.Correcao

                                        mensagem_completa += (
                                            mr.Codigo + ' - ' +
                                            mr.Mensagem +
                                            ' - Correção: ' +
                                            correcao + '\n'
                                        )
                                vals['edoc_error_message'] = \
                                    mensagem_completa
                                record.write(vals)
                                return
                            else:
                                vals['codigo_situacao'] = \
                                    processo.resposta.Situacao
                else:
                    vals['codigo_situacao'] = 4

                if vals.get('codigo_situacao') == 1:
                    vals['motivo_situacao'] = _('Not received')

                elif vals.get('codigo_situacao') == 2:
                    vals['motivo_situacao'] = _('Batch not yet processed')

                elif vals.get('codigo_situacao') == 3:
                    vals['motivo_situacao'] = _('Processed with Error')

                elif vals.get('codigo_situacao') == 4:
                    vals['motivo_situacao'] = _('Successfully Processed')
                    vals['protocolo_autorizacao'] = protocolo

                if vals.get('codigo_situacao') in (3, 4):
                    processo = processador.consultar_lote_rps(protocolo)

                    if processo.resposta:
                        mensagem_completa = ''
                        if processo.resposta.ListaMensagemRetorno:
                            lista_msgs = processo.resposta.ListaMensagemRetorno
                            for mr in lista_msgs.MensagemRetorno:

                                correcao = ''
                                if mr.Correcao:
                                    correcao = mr.Correcao

                                mensagem_completa += (
                                    mr.Codigo + ' - ' +
                                    mr.Mensagem +
                                    ' - Correção: ' +
                                    correcao + '\n'
                                )
                        vals['edoc_error_message'] = mensagem_completa

                    if processo.resposta.ListaNfse:
                        xml_file = processo.retorno
                        record.autorizacao_event_id.set_done(xml_file)
                        for comp in processo.resposta.ListaNfse.CompNfse:
                            vals['number'] = comp.Nfse.InfNfse.Numero
                            vals['data_hora_autorizacao'] = \
                                comp.Nfse.InfNfse.DataEmissao
                            vals['verify_code'] = \
                                comp.Nfse.InfNfse.CodigoVerificacao
                        record._change_state(SITUACAO_EDOC_AUTORIZADA)

                record.write(vals)
        return

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        super(Document, self)._exec_before_SITUACAO_EDOC_CANCELADA(
            old_state, new_state)
        return self.cancel_document_issnet()
