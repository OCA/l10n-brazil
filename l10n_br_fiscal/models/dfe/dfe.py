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

from datetime import datetime
from lxml import objectify

import logging

from odoo.osv import orm
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
        required=True,
    )
    last_nsu = fields.Char(
        string="Last NSU",
        size=25,
        default='0',
        required=True,
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
    def action_gerencia_manifestacoes(self):

        return {
            'name': self.company_id.razao_social,
            'view_mode': 'tree,form',
            'res_model': 'l10n_br_fiscal.mdfe',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('company_id', '=', self.company_id.id)],
            'limit': self.env['l10n_br_fiscal.mdfe'].search_count([
                ('company_id', '=', self.company_id.id)]),
        }

    def _format_nsu(self, nsu):
        # nsu = long(nsu)
        return "%015d" % (nsu,)

    def distribuicao_nfe(self, company, last_nsu):
        last_nsu = self._format_nsu(last_nsu)
        p = company.processador_nfe()
        cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
        result = p.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            last_nsu=last_nsu)

        if result.resposta.status == 200:  # Webservice ok
            if (result.resposta.cStat.valor == '137' or
                result.resposta.cStat.valor == '138'):

                nfe_list = []
                for doc in result.resposta.loteDistDFeInt.docZip:
                    nfe_list.append({
                        'xml': doc.texto, 'NSU': doc.NSU.valor,
                        'schema': doc.schema.valor
                    })

                return {
                    'result': result,
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'list_nfe': nfe_list, 'file_returned': result.resposta.xml
                }
            else:
                return {
                    'result': result,
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }
        else:
            return {
                'result': result,
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio.xml, 'file_returned': None
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
    def baixa_documentos(self, manifestos=None):
        '''
        - Declara Ciência da Emissão para todas as manifestações já recebidas,
        - Realiza Download dos XMLs das NF-e
        - Cria um sped_documento para cada XML importado
        '''

        # Coletando os erros para caso seja de importância no futuro
        erros = []

        nfe_ids = []
        if not manifestos or isinstance(manifestos, dict):
            manifestos = self.env['l10n_br_fiscal.mdfe']. \
                search([('company_id', '=', self.company_id.id)])

        for manifesto in manifestos:

            if not manifesto.state in ['pendente', 'ciente']:
                continue

            elif manifesto.state == 'pendente':
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
                    manifesto.action_ciencia_emissao()
                except Exception as e:
                    erros.append(('manifesto', manifesto.id, e))

                    try:
                        manifesto.action_ciencia_emissao()
                    except:
                        erros.append((manifesto.id, e))
                        continue

            self.validate_nfe_configuration(self.company_id)

            nfe_result = self.download_nfe(self.company_id,
                                           manifesto.chave)

            if nfe_result['code'] == '138':
                nfe = objectify.fromstring(nfe_result['nfe'])
                documento = self.env['l10n_br_fiscal.document'].new()
                documento.modelo = nfe.NFe.infNFe.ide.mod.text
                nfe = documento.le_nfe(xml=nfe_result['nfe'])

                manifesto.documento_id = nfe

                nfe_ids.append(nfe)

            else:
                erros.append(('nfe', False,
                              nfe_result['code'] + ' - ' +
                              nfe_result['message']))

        # TODO: Descomentar
        # dados = [nfe.id for nfe in nfe_ids] + self.nfe_importada_ids.ids

        # self.update({'nfe_importada_ids': [(6, False, dados)]})

        return nfe_ids

    def _cron_busca_documentos(self, context=None):
        """ Método chamado pelo agendador do sistema, processa
        automaticamente a busca de documentos conforme configuração do
        sistema.
        :param context:
        :return:
        """

        consulta_ids = self.env['l10n_br_fiscal.dfe'].search([])

        for consulta_id in consulta_ids:
            if consulta_id.use_cron:
                consulta_id.busca_documentos()

    @api.multi
    def busca_documentos(self, raise_error=False):
        nfe_mdes = []
        xml_ids = []
        company = self.company_id
        for consulta in self:
            try:
                consulta.validate_nfe_configuration(company)
                last_nsu = consulta.last_nsu
                nfe_result = consulta.distribuicao_nfe(
                    company, last_nsu)
                consulta.last_query = fields.Datetime.now()
                _logger.info('%s.busca_documentos(), lastNSU: %s',
                             company.name, last_nsu)
            except Exception:
                _logger.error("Erro ao consultar Manifesto", exc_info=True)
                if raise_error:
                    raise UserError(
                        u'Atenção',
                        u'Não foi possivel efetuar a consulta!\n '
                        u'Verifique o log')
            else:
                if nfe_result['code'] == '137' or nfe_result['code'] == '138':
                    env_mde = self.env['l10n_br_fiscal.mdfe']
                    env_mde_xml = self.env[
                        'l10n_br_fiscal.dfe_xml']

                    xml_ids.append(
                        env_mde_xml.create(
                            {
                                'consulta_id': self.id,
                                'xml_type': '0',
                                'xml': nfe_result['result'].envio.original
                            }).id
                    )
                    xml_ids.append(
                        env_mde_xml.create(
                            {
                                'consulta_id': self.id,
                                'xml_type': '1',
                                'xml': nfe_result['result'].resposta.original
                            }).id
                    )
                    xml_ids.append(
                        env_mde_xml.create(
                            {
                                'consulta_id': self.id,
                                'xml_type': '2',
                                'xml': nfe_result[
                                    'result'].resposta.loteDistDFeInt.xml
                            }).id
                    )

                    for nfe in nfe_result['list_nfe']:
                        exists_nsu = self.env['l10n_br_fiscal.mdfe']
                        exists_nsu.search(
                            [('nsu', '=', nfe['NSU']),
                             ('company_id', '=', company.id),
                             ]).id
                        nfe_xml = nfe['xml'].encode('utf-8')
                        root = objectify.fromstring(nfe_xml)
                        self.last_nsu = nfe['NSU']

                        if nfe['schema'] == u'procNFe_v3.10.xsd' and \
                            not exists_nsu:
                            chave_nfe = root.protNFe.infProt.chNFe
                            exists_chnfe = self.env[
                                'l10n_br_fiscal.mdfe'].search(
                                [('chave', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.NFe.infNFe.emit.CNPJ))
                                partner = self.env['sped.participante'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    'numero': root.NFe.infNFe.ide.nNF,
                                    'chave': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    # 'fornecedor': root.xNome,
                                    'tipo_operacao': str(root.NFe.infNFe.ide.
                                                         tpNF),
                                    'valor_documento':
                                        root.NFe.infNFe.total.ICMSTot.vNF,
                                    'state': 'pendente',
                                    'data_hora_inclusao': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.NFe.infNFe.emit.IE,
                                    'participante_id': partner.id,
                                    'data_hora_emissao': datetime.strptime(
                                        str(root.NFe.infNFe.ide.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': company.id,
                                    'dfe_id': consulta.id,
                                    'forma_inclusao': u'Verificação agendada'
                                }
                                obj_nfe = env_mde.create(invoice_eletronic)
                                file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                                self.env['ir.attachment'].create(
                                    {
                                        'name': file_name,
                                        'datas': base64.b64encode(nfe_xml),
                                        'datas_fname': file_name,
                                        'description': u'NFe via manifesto',
                                        'res_model':
                                            'l10n_br_fiscal.mdfe',
                                        'res_id': obj_nfe.id
                                    })

                                xml_ids.append(
                                    env_mde_xml.create(
                                        {
                                            'consulta_id': self.id,
                                            'xml_type': '3',
                                            'xml': nfe['xml']
                                        }).id
                                )
                            else:
                                manifesto = \
                                    self.env['l10n_br_fiscal.mdfe'] \
                                        .browse(exists_chnfe)

                                if not manifesto.dfe_id:
                                    manifesto.update({
                                        'dfe_id': consulta.id,
                                    })

                        elif nfe['schema'] == 'resNFe_v1.01.xsd' and \
                            not exists_nsu:
                            chave_nfe = root.chNFe
                            exists_chnfe = self.env[
                                'l10n_br_fiscal.mdfe'].search(
                                [('chave', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.CNPJ))
                                partner = self.env['sped.participante'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    # 'numero': root.NFe.infNFe.ide.nNF,
                                    'chave': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    'fornecedor': root.xNome,
                                    'tipo_operacao': str(root.tpNF),
                                    'valor_documento': root.vNF,
                                    'situacao_nfe': str(root.cSitNFe),
                                    'state': 'pendente',
                                    'data_hora_inclusao': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.IE,
                                    'participante_id': partner.id,
                                    'data_hora_emissao': datetime.strptime(
                                        str(root.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': company.id,
                                    'dfe_id': consulta.id,
                                    'forma_inclusao': u'Verificação agendada -'
                                                      u' manifestada por '
                                                      u'outro '
                                                      u'app'
                                }
                                obj_nfe = env_mde.create(invoice_eletronic)
                                file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                                self.env['ir.attachment'].create(
                                    {
                                        'name': file_name,
                                        'datas': base64.b64encode(nfe_xml),
                                        'datas_fname': file_name,
                                        'description': u'NFe via manifesto',
                                        'res_model':
                                            'l10n_br_fiscal.mdfe',
                                        'res_id': obj_nfe.id
                                    })

                                xml_ids.append(
                                    env_mde_xml.create(
                                        {
                                            'consulta_id': self.id,
                                            'xml_type': '3',
                                            'xml': nfe['xml']
                                        }).id
                                )

                            else:
                                manifesto = \
                                    self.env['l10n_br_fiscal.mdfe'] \
                                        .browse(exists_chnfe)

                                if not manifesto.dfe_id:
                                    manifesto.update({
                                        'dfe_id': consulta.id,
                                    })

                        nfe_mdes.append(nfe)

                    self.write({'recipient_xml_ids': [(6, 0, xml_ids)]})

                else:
                    raise models.ValidationError(
                        nfe_result['code'] + ' - ' + nfe_result['message'])

        return nfe_mdes

    @staticmethod
    def validate_nfe_configuration(company):
        error = u'As seguintes configurações estão faltando:\n'

        if not company.certificate_nfe_id.arquivo:
            error += u'Empresa - Arquivo NF-e A1\n'
        if not company.certificate_nfe_id.senha:
            error += u'Empresa - Senha NF-e A1\n'
        if error != u'As seguintes configurações estão faltando:\n':
            raise orm.except_orm(_(u'Validação !'), _(error))

    def send_event(self, company, nfe_key, method):
        p = company.processador_nfe()
        cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
        result = {}
        if method == 'ciencia_operacao':
            result = p.conhecer_operacao_evento(
                cnpj=cnpj_partner,
                # CNPJ do destinatário/gerador do evento
                chave_nfe=nfe_key)
        elif method == 'confirma_operacao':
            result = p.confirmar_operacao_evento(
                cnpj=cnpj_partner,
                chave_nfe=nfe_key)
        elif method == 'desconhece_operacao':
            result = p.desconhecer_operacao_evento(
                cnpj=cnpj_partner,
                chave_nfe=nfe_key)
        elif method == 'nao_realizar_operacao':
            result = p.nao_realizar_operacao_evento(
                cnpj=cnpj_partner,
                chave_nfe=nfe_key)

        if result.resposta.status == 200:  # Webservice ok
            if result.resposta.cStat.valor == '128':
                inf_evento = result.resposta.retEvento[0].infEvento
                return {
                    'code': inf_evento.cStat.valor,
                    'message': inf_evento.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }
            else:
                return {
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }
        else:
            return {
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio.xml,
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
            if result.resposta.cStat.valor == '138':
                nfe_zip = result.resposta.loteDistDFeInt.docZip[
                    0].docZip.valor
                orig_file_desc = gzip.GzipFile(
                    mode='r',
                    fileobj=io.StringIO(
                        base64.b64decode(nfe_zip))
                )
                nfe = orig_file_desc.read()
                orig_file_desc.close()

                return {
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml,
                    'nfe': nfe,
                }
            else:
                return {
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }
        else:
            return {
                'code': result.resposta.status,
                'message': result.resposta.reason,
                'file_sent': result.envio.xml, 'file_returned': None
            }


class DFeXML(models.Model):
    _name = 'l10n_br_fiscal.dfe_xml'
    _description = 'DF-e XML Document'

    dfe_id = fields.Many2one(
        string=u'DF-e Consult',
        comodel_name='l10n_br_fiscal.dfe',
        readonly=True,
    )

    xml_type = fields.Selection([
        ('0', 'Envio'),
        ('1', 'Resposta'),
        ('2', 'Resposta-LoteDistDFeInt'),
        ('3', 'Resposta-LoteDistDFeInt-DocZip(NFe)')
    ],
        string="XML Type",
        readonly=True,
    )

    xml = fields.Char(
        string="XML",
        size=5000,
        required=True,
    )
