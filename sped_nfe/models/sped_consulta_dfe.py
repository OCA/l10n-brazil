# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import base64
import re

from datetime import datetime
from lxml import objectify

import logging

from odoo.osv import orm
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

AMBIENTE_NFE_PRODUCAO = '1'

try:
    from pysped.nfe import ProcessadorNFe
    from pysped.nfe.webservices_flags import (AMBIENTE_NFE_PRODUCAO,
        CONS_NFE_TODAS, CONS_NFE_EMISSAO_TODOS_EMITENTES)
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class ConsultaDFe(models.Model):
    _name = b'sped.consulta.dfe'
    _description = 'Consulta DFe'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        required=True,
    )
    ultimo_nsu = fields.Char(
        string='Último NS',
        size=25,
        default='0',
        required=True,
    )
    ultima_consulta = fields.Datetime(
        string='Última consulta',
    )

    def __processo(self, company):
        p = ProcessadorNFe()
        p.ambiente = int(company.ambiente_nfe)
        p.estado = company.partner_id.state_id.code
        p.certificado.stream_certificado = base64.decodestring(company.certificado_id.arquivo)
        p.certificado.senha = company.certificado_id.senha
        p.salvar_arquivos = False
        p.contingencia_SCAN = False
        return p

    def _format_nsu(self, nsu):
        nsu = long(nsu)
        return "%015d" % (nsu,)

    def distribuicao_nfe(self, company, ultimo_nsu):
        ultimo_nsu = self._format_nsu(ultimo_nsu)
        p = self.__processo(company)
        cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
        result = p.consultar_distribuicao(
            cnpj_cpf=cnpj_partner,
            ultimo_nsu=ultimo_nsu)

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
                    'code': result.resposta.cStat.valor,
                    'message': result.resposta.xMotivo.valor,
                    'list_nfe': nfe_list, 'file_returned': result.resposta.xml
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

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub('[^0-9]', '', cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8],
                                           val[8:12], val[12:14])
        return cnpj

    @api.multi
    def busca_documentos(self, raise_error=False):
        nfe_mdes = []
        company = self.empresa_id
        for consulta in self:
            try:
                self.validate_nfe_configuration(company)
                last_nsu = self.ultimo_nsu
                nfe_result = self.distribuicao_nfe(
                    company, last_nsu)
                _logger.info('%s.query_nfe_batch(), lastNSU: %s',
                             company, last_nsu)
            except Exception:
                _logger.error("Erro ao consultar Manifesto", exc_info=True)
                if raise_error:
                    raise UserError(
                        u'Atenção',
                        u'Não foi possivel efetuar a consulta!\n '
                        u'Verifique o log')
            else:
                if self.ultimo_nsu:
                    # do this here instead of in get_last_dfe_nsu() in case the
                    # exception gets swallowed in the `except` above.
                    self.ultimo_nsu = ''
                # env_events = self.env['l10n_br_account.document_event']

                if nfe_result['code'] == '137' or nfe_result['code'] == '138':

                    event = {
                        'type': '12', 'company_id': company.id,
                        'response': 'Consulta distribuição: sucesso',
                        'status': nfe_result['code'],
                        'message': nfe_result['message'],
                        'create_date': datetime.now(),
                        'write_date': datetime.now(),
                        'end_date': datetime.now(),
                        'state': 'done', 'origin': 'Scheduler Download'
                    }

                    # obj = env_events.create(event)
                    self.env['ir.attachment'].create(
                        {
                            'name': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'datas': base64.b64encode(
                                nfe_result['file_returned']),
                            'datas_fname': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'description': u'Consulta distribuição: sucesso',
                            'res_model': 'l10n_br_account.document_event',
                            # 'res_id': obj.id
                        })

                    env_mde = self.env['sped.manifestacao.destinatario']
                    for nfe in nfe_result['list_nfe']:
                        exists_nsu = self.env['sped.manifestacao.destinatario'].search(
                            [('nsu', '=', nfe['NSU']),
                             ('empresa_id', '=', company.id),
                             ]).id
                        nfe_xml = nfe['xml'].encode('utf-8')
                        root = objectify.fromstring(nfe_xml)
                        if nfe['schema'] == u'procNFe_v3.10.xsd' and \
                                not exists_nsu:
                            chave_nfe = root.protNFe.infProt.chNFe
                            exists_chnfe = self.env[
                                'sped.manifestacao.destinatario'].search(
                                [('chave', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.NFe.infNFe.emit.CNPJ))
                                partner = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    'numero': root.NFe.infNFe.ide.nNF,
                                    'chave': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    'razao_social': root.NFe.infNFe.emit.xNome,
                                    'tipo_operacao': str(root.NFe.infNFe.ide.tpNF),
                                    'valor_documento': root.NFe.infNFe.total.ICMSTot.vNF,
                                    # 'cSitNFe': str(root.cSitNFe),
                                    'situacao_manifestacao': 'pendente',
                                    'data_hora_autorizacao': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.NFe.infNFe.emit.IE,
                                    'participante_id': partner.id,
                                    'data_hora_emissao': datetime.strptime(
                                        str(root.NFe.infNFe.ide.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'empresa_id': company.id,
                                    'justificativa': u'Verificação agendada'
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
                                            'sped.manifestacao.destinatario',
                                        'res_id': obj_nfe.id
                                    })
                        elif nfe['schema'] == 'resNFe_v1.01.xsd' and \
                                not exists_nsu:
                            chave_nfe = root.chNFe
                            exists_chnfe = self.env[
                                'sped.manifestacao.destinatario'].search(
                                [('chave', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.CNPJ))
                                # partner = self.env['res.partner'].search(
                                #     [('cnpj_cpf', '=', cnpj_forn)])
                                partner = self.env['sped.empresa'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    # 'numero': root.NFe.infNFe.ide.nNF,
                                    'chave': chave_nfe,
                                    'nsu': nfe['NSU'],
                                    'razao_social': root.xNome,
                                    'tipo_operacao': str(root.tpNF),
                                    'valor_documento': root.vNF,
                                    'situacao_nfe': str(root.cSitNFe),
                                    'situacao_manifestacao': 'pendente',
                                    'data_hora_autorizacao': datetime.now(),
                                    'cnpj_cpf': cnpj_forn,
                                    'ie': root.IE,
                                    'participante_id': partner.id,
                                    'data_hora_emissao': datetime.strptime(
                                        str(root.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'empresa_id': company.id,
                                    'justificativa': u'Verificação agendada - '
                                                    u'manifestada por outro app'
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
                                            'sped.manifestacao.destinatario',
                                        'res_id': obj_nfe.id
                                    })

                        nfe_mdes.append(nfe)
                else:

                    event = {
                        'type': '12',
                        'response': 'Consulta distribuição com problemas',
                        'company_id': company.id,
                        'file_returned': nfe_result['file_returned'],
                        'file_sent': nfe_result['file_sent'],
                        'message': nfe_result['message'],
                        'create_date': datetime.now(),
                        'write_date': datetime.now(),
                        'end_date': datetime.now(),
                        'status': nfe_result['code'],
                        'state': 'done', 'origin': 'Scheduler Download'
                    }

                    # obj = env_events.create(event)

                    if nfe_result['file_returned']:
                        self.env['ir.attachment'].create({
                            'name': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'datas': base64.b64encode(
                                nfe_result['file_returned']),
                            'datas_fname': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'description': u'Consulta manifesto com erro',
                            'res_model': 'l10n_br_account.document_event',
                            # 'res_id': obj.id
                        })


        return nfe_mdes

    def validate_nfe_configuration(self,company):
        error = u'As seguintes configurações estão faltando:\n'

        #TODO: Versão da NFE
        # if not company.nfe_version:
        #     error += u'Empresa - Versão NF-e\n'

        if not company.certificado_id.arquivo:
            error += u'Empresa - Arquivo NF-e A1\n'
        if not company.certificado_id.senha:
            error += u'Empresa - Senha NF-e A1\n'
        if error != u'As seguintes configurações estão faltando:\n':
            raise orm.except_orm(_(u'Validação !'), _(error))