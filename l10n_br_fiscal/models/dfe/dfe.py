# -*- coding: utf-8 -*-
#
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import base64
import re
import gzip
import io
import tempfile

from datetime import datetime
from lxml import objectify
from requests import Session

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP


from odoo.osv import orm
from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


def _format_nsu(nsu):
    nsu = int(nsu)
    return "%015d" % (nsu,)

def _processador(company_id):
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
    # TODO: Utilizar ambiente
    return edoc_nfe(
        transmissao, company_id.state_id.ibge_code,
        versao='1.01', ambiente=company_id.nfe_environment # 1 - PROD. 2-HML
    )


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _description = 'Consult DF-e'
    _order = 'id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        compute='_compute_display_name'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
    )
    last_nsu = fields.Char(
        string="Last NSU",
        size=25,
        default='0',
    )
    last_query = fields.Datetime(
        string="Last query",
    )

    recipient_xml_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.dfe_xml',
        inverse_name='dfe_id',
        string="XML Documents",
    )

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = '{} - NSU: {}'.format(
                record.company_id.name, record.last_nsu)

    imported_document_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document',
        inverse_name='dfe_id',
        string="Imported Documents",
    )

    imported_dfe_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.mdfe',
        inverse_name='dfe_id',
        string="Manifestações do Destinatário Importadas",
    )

    use_cron = fields.Boolean(
        default=False,
        string="Download new documents automatically",
        help='If activated, allows new manifestations to be automatically '
             'searched with a Cron',
    )

    @api.multi
    def action_manage_manifestations(self):

        return {
            'name': self.company_id.legal_name,
            'view_mode': 'tree,form',
            'res_model': 'l10n_br_fiscal.mdfe',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('company_id', '=', self.company_id.id)],
            'limit': self.env['l10n_br_fiscal.mdfe'].search_count([
                ('company_id', '=', self.company_id.id)]),
        }

    def document_distribution(self, company_id, last_nsu):
        last_nsu = _format_nsu(last_nsu)

        processor = _processador(company_id)

        cnpj_partner = re.sub('[^0-9]', '', company_id.cnpj_cpf)
        result = processor.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            ultimo_nsu=last_nsu
        )

        if result.retorno.status_code == 200:  # Webservice ok
            if (result.resposta.cStat in ['137', '138']):

                nfe_list = []
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

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub('[^0-9]', '', cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8],
                                           val[8:12], val[12:14])
        return cnpj

    @api.multi
    def download_documents(self, manifests=None):
        '''
        - Declara Ciência da Emissão para todas as manifestações já recebidas,
        - Realiza Download dos XMLs das NF-e
        - Cria um sped_documento para cada XML importado
        '''

        # Coletando os erros para caso seja de importância no futuro
        errors = []

        nfe_ids = []
        if not manifests or isinstance(manifests, dict):
            manifests = self.env['l10n_br_fiscal.mdfe']. \
                search([('company_id', '=', self.company_id.id)])

        for mdfe in manifests:

            if not mdfe.state in ['pendente', 'ciente']:
                continue

            elif mdfe.state == 'pendente':
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
                    mdfe.action_ciencia_emissao()
                except Exception as e:
                    errors.append(('mdfe', mdfe.id, e))

                    try:
                        mdfe.action_ciencia_emissao()
                    except:
                        errors.append((mdfe.id, e))
                        continue

            self.validate_document_configuration(self.company_id)

            nfe_result = self.download_nfe(self.company_id, mdfe.key)

            if nfe_result['code'] == '138':
                nfe = objectify.fromstring(nfe_result['nfe'])
                document_id = self.env['l10n_br_fiscal.document'].new()
                document_id.modelo = nfe.NFe.infNFe.ide.mod.text

                # TODO: Chamar método para construir um
                #  'l10n_br_fiscal.document'
                document_id = document_id.le_nfe(xml=nfe_result['nfe'])

                mdfe.documento_id = nfe

                nfe_ids.append(nfe)

            else:
                errors.append(('nfe', False,
                              nfe_result['code'] + ' - ' +
                              nfe_result['message']))

        # TODO: Descomentar
        # dados = [nfe.id for nfe in nfe_ids] + self.nfe_importada_ids.ids

        # self.update({'nfe_importada_ids': [(6, False, dados)]})

        return nfe_ids

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
                _logger.error("Erro ao consultar Manifesto.\n%s" % e, exc_info=True)
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
                            ('nsu', '=', nfe['NSU']), # TODO: Verificar se formatação dos dois campos NSU equivalem
                            ('company_id', '=', self.company_id.id),
                        ])
                        nfe_b64decode = base64.b64decode(nfe['xml'])

                        tmp_nfe_zip = tempfile.NamedTemporaryFile(delete=True)
                        tmp_nfe_zip.seek(0)
                        tmp_nfe_zip.write(nfe_b64decode)
                        tmp_nfe_zip.flush()

                        nfe_xml = gzip.open(tmp_nfe_zip.name, 'rb').read()

                        root = objectify.fromstring(nfe_xml)
                        self.last_nsu = nfe['NSU']

                        if nfe['schema'] == 'procNFe_v3.10.xsd' and \
                            not exists_nsu:
                            chave_nfe = root.protNFe.infProt.chNFe
                            exists_chnfe = env_mdfe.search(
                                [('key', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = record._mask_cnpj(
                                    ('%014d' % root.NFe.infNFe.emit.CNPJ))
                                # TODO: Verificar qual modelo utilizar para parceiro
                                # partner = self.env['sped.participante'].search(
                                partner = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                mdfe_dict = {
                                    'number': root.NFe.infNFe.ide.nNF,
                                    'key': chave_nfe,
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

                        elif nfe['schema'] == 'resNFe_v1.01.xsd' and \
                            not exists_nsu:
                            chave_nfe = root.chNFe
                            exists_chnfe = env_mdfe.search([
                                ('key', '=', chave_nfe)
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
                                    'key': chave_nfe,
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
                    raise models.ValidationError( '{} - {}'.format(
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

    def send_event(self, company_id, nfe_key, method):
        processor = _processador(company_id)
        cnpj_partner = re.sub('[^0-9]', '', company_id.cnpj_cpf)
        result = {}
        if method == 'ciencia_operacao':
            result = processor.ciencia_da_operacao(
                nfe_key,
                cnpj_partner) # CNPJ do destinatário/gerador do evento
        elif method == 'confirma_operacao':
            result = processor.confirmacao_da_operacao(
                nfe_key,
                cnpj_partner) # CNPJ do destinatário/gerador do evento
        elif method == 'desconhece_operacao':
            result = processor.desconhecimento_da_operacao(
                nfe_key,
                cnpj_partner) # CNPJ do destinatário/gerador do evento
        elif method == 'nao_realizar_operacao':
            result = processor.operacao_nao_realizada(
                nfe_key,
                cnpj_partner) # CNPJ do destinatário/gerador do evento

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
    def download_nfe(company, list_nfe):
        p = company.processador_nfe()
        cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)

        result = p.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            chave_nfe=list_nfe)

        if result.resposta.status == 200:  # Webservice ok
            if result.resposta.cStat == '138':
                nfe_zip = result.resposta.loteDistDFeInt.docZip[
                    0].docZip
                orig_file_desc = gzip.GzipFile(
                    mode='r',
                    fileobj=io.StringIO(
                        base64.b64decode(nfe_zip))
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


class DFeXML(models.Model):
    _name = 'l10n_br_fiscal.dfe_xml'
    _description = 'DF-e XML Document'

    dfe_id = fields.Many2one(
        string='DF-e Consult',
        comodel_name='l10n_br_fiscal.dfe',
    )

    xml_type = fields.Selection([
        ('0', 'Envio'),
        ('1', 'Resposta'),
        ('2', 'Resposta-LoteDistDFeInt'),
        ('3', 'Resposta-LoteDistDFeInt-DocZip(NFe)')
    ],
        string="XML Type",
    )

    xml = fields.Char(
        string="XML",
        size=5000,
    )
