# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
import io
import logging
import re
import tempfile
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.mde import MDe as edoc_nfe
from erpbrasil.edoc.mde import TransmissaoMDE as TransmissaoSOAP
from lxml import objectify
from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import orm

_logger = logging.getLogger(__name__)

# TODO: Remover chamadas envolvendo essas constante
REMOVE_AMBIENTE_PADRAO_PROD = 1  # PRODUÇÃO
REMOVE_AMBIENTE_PADRAO_HML = 2  # HOMOLOGAÇÃO


def _format_nsu(nsu):
    nsu = int(nsu)
    return "%015d" % (nsu,)


def _processador(company_id, force_ambiente=REMOVE_AMBIENTE_PADRAO_HML):
    """
    # TODO: Utilizar método _procesador(self) já existente no l10n_br_fiscal.document
    :param company_id: Empresa
    :return: Um elemento edoc_nfe
    """
    if not company_id.certificate_nfe_id:
        raise UserError(_("Certificate not found"))

    tmp_certificate = tempfile.NamedTemporaryFile(delete=True)
    tmp_certificate.seek(0)
    tmp_certificate.write(base64.b64decode(
        company_id.certificate_nfe_id.file.decode('utf8')))
    tmp_certificate.flush()

    certificado = cert.Certificado(
        arquivo=tmp_certificate.name,
        senha=company_id.certificate_nfe_id.password,
    )
    session = Session()
    session.verify = False
    transmissao = TransmissaoSOAP(certificado, session)

    ambiente = force_ambiente or company_id.nfe_environment
    return edoc_nfe(
        transmissao, company_id.state_id.ibge_code,
        versao='1.01', ambiente=ambiente  # 1 - PROD. 2-HML
    )


class DFe(models.Model):
    _inherit = "l10n_br_fiscal.dfe"

    def document_distribution(self, company_id, last_nsu):
        last_nsu = _format_nsu(last_nsu)

        processor = _processador(company_id, force_ambiente=False)

        cnpj_partner = re.sub('[^0-9]', '', company_id.cnpj_cpf)
        result = processor.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            ultimo_nsu=last_nsu
        )

        if result.retorno.status_code == 200:  # Webservice ok
            if (result.resposta.cStat in ['137', '138']):

                nfe_list = []
                if result.resposta.loteDistDFeInt:
                    for doc in result.resposta.loteDistDFeInt.docZip:
                        nfe_list.append({
                            'xml': doc.valueOf_, 'NSU': doc.NSU,
                            'schema': doc.schema
                        })

                return {
                    'result': result,
                    'code': result.resposta.cStat,
                    'message': result.resposta.xMotivo,
                    'list_nfe': nfe_list, 'file_returned': result.retorno.text
                }
            else:
                return {
                    'result': result,
                    'code': result.resposta.cStat,
                    'message': result.resposta.xMotivo,
                    'file_sent': result.envio_xml,
                    'file_returned': result.retorno.text
                }
        else:
            return {
                'result': result,
                'code': result.retorno.status_code,
                'message': result.resposta.xMotivo,
                'file_sent': result.envio_xml, 'file_returned': None
            }

    def parse_xml_document(self, doc_xml):
        """
        Converte um documento de XML para um objeto l10n_br_fiscal.document
        :param doc_xml: XML (str ou byte[]) do documento a ser convertido
        :return: Um novo objeto do modelo l10n_br_fiscal.document
        """

        from nfelib.v4_00 import leiauteNFe_sub as nfe_sub

        # TODO: Identificar o tipo do documento e utilizar o parser correto
        #  doc_obj = objectify.fromstring(doc_xml)
        #  modelo = doc_obj.NFe.infNFe.ide.mod.text

        tmp_document = tempfile.NamedTemporaryFile(delete=True)
        tmp_document.seek(0)
        tmp_document.write(doc_xml)
        tmp_document.flush()
        file_path = tmp_document.name

        obj = nfe_sub.parse(file_path)
        nfe = self.env["nfe.40.infnfe"].build(obj.infNFe)

        return nfe

    @api.multi
    def download_documents(self, mdfe_ids=None):
        """
        - Declara Ciência da Emissão para todas as manifestações já recebidas,
        - Realiza Download dos XMLs das NF-e
        - Cria um sped_documento para cada XML importado
        :param mdfe_ids: Recordset de objetos l10n_br_fiscal.mdfe
        :return: Um recordset de l10n_br_fiscal.document instanciados
        """

        # Coletando os erros para caso seja de importância no futuro
        errors = []

        document_ids = self.env['l10n_br_fiscal.document']
        if not mdfe_ids or isinstance(mdfe_ids, dict):
            mdfe_ids = self.env['l10n_br_fiscal.mdfe']. \
                search([('company_id', '=', self.company_id.id)])

        for mdfe_id in mdfe_ids:

            if mdfe_id.state not in ['pendente', 'ciente']:
                continue

            elif mdfe_id.state == 'pendente':
                '''
                Aqui é importante tentar manifestar Ciência da
                Emissão duas vezes pois existe a possibilidade de uma
                manifestação ser importada com a Ciência de Emissão já
                declarada, retornando uma mensagem de erro.
                A segunda tentativa de chamar o método alterará o campo state
                do mesmo para 'ciente', sincronizando com o estado real da
                manifestação na receita federal.
                '''
                try:
                    mdfe_id.action_ciencia_emissao()
                except Exception as e:
                    errors.append(('MDF-e', mdfe_id.id, e))

                    try:
                        mdfe_id.action_ciencia_emissao()
                    except:
                        errors.append((mdfe_id.id, e))
                        # continue

            self.validate_document_configuration(self.company_id)

            nfe_result = self.download_nfe(self.company_id, mdfe_id.document_key)

            if nfe_result['code'] == '138':

                # O XML do documento será convertido para
                # um novo objeto l10n_br_fiscal.document
                document_id = self.parse_xml_document(nfe_result['nfe'])

                mdfe_id.document_id = document_id
                document_ids += document_id

            else:
                errors.append(('nfe', False, '{} - {}'.format(
                    nfe_result.get('code', '???'),
                    nfe_result.get('message', ''))))

        data = document_ids.ids + self.imported_document_ids.ids

        # Atualiza a lista de documentos atual com os novos documentos criados
        self.update({'imported_document_ids': [(6, False, data)]})

        return document_ids

    def _cron_search_documents(self, context=None):
        """ Método chamado pelo agendador do sistema, processa
        automaticamente a busca de documentos conforme configuração do
        sistema.
        :param context:
        :return:
        """

        consulta_ids = self.env['l10n_br_fiscal.dfe'].search([])

        for consulta_id in consulta_ids:
            if consulta_id.use_cron:
                consulta_id.search_documents(raise_error=False)

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub('[^0-9]', '', cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8],
                                           val[8:12], val[12:14])
        return cnpj

    @api.multi
    def search_documents(self, context=None, raise_error=True):
        nfe_mdes = []
        xml_ids = []
        for record in self:
            try:
                record.validate_document_configuration(record.company_id)
                nfe_result = record.document_distribution(
                    record.company_id, record.last_nsu)
                record.last_query = fields.Datetime.now()
                _logger.info('%s.search_documents(), lastNSU: %s',
                             record.company_id.name, record.last_nsu)
            except Exception as e:
                _logger.error("Erro ao consultar Manifesto.\n%s" % e,
                              exc_info=True)
                if raise_error:
                    raise UserError(
                        'Não foi possivel efetuar a consulta!\n '
                        '%s' % e)
            else:
                if nfe_result['code'] in ['137', '138']:
                    env_mdfe = self.env['l10n_br_fiscal.mdfe']
                    env_mdfe_xml = self.env['l10n_br_fiscal.dfe_xml']

                    xml_ids.append(
                        env_mdfe_xml.create(
                            {
                                'dfe_id': record.id,
                                'xml_type': '0',
                                # TODO: Inserir XML de fato. 'envio_xml' é um
                                #  arquivo gz codificado em base64
                                'xml': nfe_result['result'].envio_xml
                            }).id
                    )
                    xml_ids.append(
                        env_mdfe_xml.create(
                            {
                                'dfe_id': record.id,
                                'xml_type': '1',
                                # TODO: Inserir XML de fato. 'retorno.text' é
                                #  um arquivo gz codificado em base64
                                'xml': nfe_result['result'].retorno.text
                            }).id
                    )
                    xml_ids.append(
                        env_mdfe_xml.create(
                            {
                                'dfe_id': record.id,
                                'xml_type': '2',
                                # TODO: Obter o XML do loteDistDFeInt
                                # 'xml': nfe_result[
                                #     'result'].resposta.loteDistDFeInt.xml
                            }).id
                    )

                    for nfe in nfe_result['list_nfe']:
                        exists_nsu = env_mdfe.search([
                            ('nsu', '=', nfe['NSU']),
                            # TODO: Verificar se formatação dos dois campos NSU
                            #  equivalem
                            ('company_id', '=', self.company_id.id),
                        ])

                        arq = io.BytesIO()
                        arq.write(base64.b64decode(nfe['xml']))
                        arq.seek(0)

                        tmp_nfe_zip = gzip.GzipFile(
                            mode='r',
                            fileobj=arq
                        )
                        nfe_xml = tmp_nfe_zip.read()

                        root = objectify.fromstring(nfe_xml)
                        self.last_nsu = nfe['NSU']

                        if nfe['schema'] == 'procNFe_v3.10.xsd' and not exists_nsu:
                            chave_nfe = root.protNFe.infProt.chNFe
                            exists_chnfe = env_mdfe.search(
                                [('document_key', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = record._mask_cnpj(
                                    ('%014d' % root.NFe.infNFe.emit.CNPJ))
                                # TODO: Verificar qual modelo utilizar para parceiro
                                # partner = self.env['sped.participante'].search(
                                partner = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                mdfe_dict = {
                                    'document_number': root.NFe.infNFe.ide.nNF,
                                    'document_key': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    # 'fornecedor': root.xNome,
                                    'operation_type': str(root.NFe.infNFe.ide.
                                                          tpNF),
                                    'document_value':
                                        root.NFe.infNFe.total.ICMSTot.vNF,
                                    'state': 'pendente',
                                    'inclusion_datetime': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.NFe.infNFe.emit.IE,
                                    'partner_id': partner.id,
                                    'emission_datetime': datetime.strptime(
                                        str(root.NFe.infNFe.ide.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': record.company.id,
                                    'dfe_id': record.id,
                                    'inclusion_mode': 'Verificação agendada'
                                }
                                obj_nfe = env_mdfe.create(mdfe_dict)
                                file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                                self.env['ir.attachment'].create(
                                    {
                                        'name': file_name,
                                        'datas': base64.b64encode(nfe_xml),
                                        'datas_fname': file_name,
                                        'description': 'NFe via manifest',
                                        'res_model':
                                            'l10n_br_fiscal.mdfe',
                                        'res_id': obj_nfe.id
                                    })

                                xml_ids.append(
                                    env_mdfe_xml.create(
                                        {
                                            'dfe_id': record.id,
                                            'xml_type': '3',
                                            'xml': nfe['xml']
                                        }).id
                                )
                            else:
                                manifesto = \
                                    record.env['l10n_br_fiscal.mdfe'] \
                                        .browse(exists_chnfe)

                                if not manifesto.dfe_id:
                                    manifesto.update({
                                        'dfe_id': record.id,
                                    })

                        elif nfe['schema'] == 'resNFe_v1.01.xsd' and not exists_nsu:
                            chave_nfe = root.chNFe
                            exists_chnfe = env_mdfe.search([
                                ('document_key', '=', chave_nfe)
                            ]).id

                            if not exists_chnfe:
                                cnpj_forn = record._mask_cnpj(
                                    ('%014d' % root.CNPJ))
                                # TODO: Verificar qual modelo de parceiro usar
                                # partner_id = self.env['sped.participante'].search(
                                #     [('cnpj_cpf', '=', cnpj_forn)])
                                partner_id = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                mdfe_dict = {
                                    # 'number': root.NFe.infNFe.ide.nNF,
                                    'document_key': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    'fornecedor': root.xNome,
                                    'operation_type': str(root.tpNF),
                                    'document_value': root.vNF,
                                    'situacao_nfe': str(root.cSitNFe),
                                    'state': 'pendente',
                                    'inclusion_datetime': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.IE,
                                    'partner_id': partner_id.id,
                                    'emission_datetime': datetime.strptime(
                                        str(root.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': record.company_id.id,
                                    'dfe_id': record.id,
                                    'inclusion_mode': 'Verificação agendada -'
                                                      ' manifestada por '
                                                      'outro '
                                                      'app'
                                }
                                obj_nfe = env_mdfe.create(mdfe_dict)
                                file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                                self.env['ir.attachment'].create(
                                    {
                                        'name': file_name,
                                        'datas': base64.b64encode(nfe_xml),
                                        'datas_fname': file_name,
                                        'description': 'NFe via manifesto',
                                        'res_model':
                                            'l10n_br_fiscal.mdfe',
                                        'res_id': obj_nfe.id
                                    })

                                xml_ids.append(
                                    env_mdfe_xml.create(
                                        {
                                            'dfe_id': record.id,
                                            'xml_type': '3',
                                            'xml': nfe['xml']
                                        }).id
                                )

                            else:
                                manifesto = \
                                    env_mdfe.browse(exists_chnfe)

                                if not manifesto.dfe_id:
                                    manifesto.update({
                                        'dfe_id': record.id,
                                    })

                        nfe_mdes.append(nfe)

                    self.write({'recipient_xml_ids': [(6, 0, xml_ids)]})

                else:
                    if not nfe_result.get('code') and not nfe_result.get('message'):
                        raise models.ValidationError(_(
                            'The service returned an incomprehensible answer.'
                            ' Check the handling of the service response'
                        ))
                    raise models.ValidationError('{} - {}'.format(
                        nfe_result.get('code', '???'),
                        nfe_result.get('message', ''))
                    )

        return nfe_mdes

    @staticmethod
    def validate_document_configuration(company_id):
        missing_configs = []

        if not company_id.certificate_nfe_id.file:
            missing_configs.append(_('Company - NF-e A1 File'))
        if not company_id.certificate_nfe_id.password:
            missing_configs.append(_('Company - NF-e A1 Password'))
        if missing_configs:
            error_msg = 'The following configurations are missing\n' + \
                        '\n'.join([m for m in missing_configs])
            raise orm.except_orm(_('Validation!'), _(error_msg))

    @staticmethod
    def send_event(company_id, nfe_key, method):
        processor = _processador(company_id, force_ambiente=False)
        cnpj_partner = re.sub('[^0-9]', '', company_id.cnpj_cpf)
        result = {}
        if method == 'ciencia_operacao':
            result = processor.ciencia_da_operacao(
                nfe_key,
                cnpj_partner)  # CNPJ do destinatário/gerador do evento
        elif method == 'confirma_operacao':
            result = processor.confirmacao_da_operacao(
                nfe_key,
                cnpj_partner)  # CNPJ do destinatário/gerador do evento
        elif method == 'desconhece_operacao':
            result = processor.desconhecimento_da_operacao(
                nfe_key,
                cnpj_partner)  # CNPJ do destinatário/gerador do evento
        elif method == 'nao_realizar_operacao':
            result = processor.operacao_nao_realizada(
                nfe_key,
                cnpj_partner)  # CNPJ do destinatário/gerador do evento

        if result.retorno.status_code == 200:  # Webservice ok
            if result.resposta.cStat == '128':
                inf_evento = result.resposta.retEvento[0].infEvento
                return {
                    'code': inf_evento.cStat,
                    'message': inf_evento.xMotivo,
                    'file_sent': result.envio_xml,
                    'file_returned': result.retorno.text
                }
            else:
                return {
                    'code': result.resposta.cStat,
                    'message': result.resposta.xMotivo,
                    'file_sent': result.envio_xml,
                    'file_returned': result.retorno.text
                }
        else:
            return {
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio_xml,
                'file_returned': None
            }

    @staticmethod
    def download_nfe(company_id, list_nfe):
        p = _processador(company_id, force_ambiente=False)
        cnpj_partner = re.sub('[^0-9]', '', company_id.cnpj_cpf)

        result = p.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            chave=list_nfe)

        if result.retorno.status_code == 200:  # Webservice ok
            if result.resposta.cStat == '138':
                nfe_zip = result.resposta.loteDistDFeInt.docZip[0].valueOf_
                arq = io.BytesIO()
                arq.write(base64.b64decode(nfe_zip))
                arq.seek(0)

                orig_file_desc = gzip.GzipFile(
                    mode='r',
                    fileobj=arq
                )
                nfe = orig_file_desc.read()
                orig_file_desc.close()

                return {
                    'code': result.resposta.cStat,
                    'message': result.resposta.xMotivo,
                    'file_sent': result.envio_xml,
                    'file_returned': result.retorno.text,
                    'nfe': nfe,
                }
            else:
                return {
                    'code': result.resposta.cStat,
                    'message': result.resposta.xMotivo,
                    'file_sent': result.envio_xml,
                    'file_returned': result.retorno.text
                }
        else:
            return {
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio_xml, 'file_returned': None
            }
