# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  KMEE  - www.kmee.com.br - Rafael da Silva Lima
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
import base64
import logging
import re
from datetime import datetime
from lxml import objectify

from odoo.addons.nfe.sped.nfe.validator.config_check import \
    validate_nfe_configuration
from odoo.exceptions import Warning as UserError
from ..service.mde import distribuicao_nfe
from odoo import api, models, fields

_logger = logging.getLogger(__name__)

NFE_NAMESPACE_MAP = dict(
    nfe='http://www.portalfiscal.inf.br/nfe',
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    nfe_email = fields.Text('Observação em Email NFe')
    nfe_logo = fields.Binary('NFe Logo')
    nfe_logo_vertical = fields.Boolean('Logo na Vertical')
    danfe_automatic_generate = fields.Boolean('Gera DANFE Automaticamente')

    last_nsu_nfe = fields.Char(string="Forçar NSU", size=20, default='0')

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub('[^0-9]', '', cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8],
                                           val[8:12], val[12:14])
        return cnpj

    @api.multi
    def get_last_dfe_nsu(self):
        self.ensure_one()
        last_nsu = 0L
        doc_event_model = 'l10n_br_account.document_event'
        last_dist_dfe_domain = [
            ('company_id', '=', self.id),
            ('type', '=', u'12'),
            ('status', 'in', ['137', '138']),
        ]
        last_dist_dfe = self.env[doc_event_model].search(
            last_dist_dfe_domain,
            order='id desc',
            limit=1
        )
        for dfe in last_dist_dfe:
            xml = objectify.fromstring(self.env['ir.attachment'].search([
                ('res_model', '=', doc_event_model),
                ('res_id', '=', dfe.id),
            ]).datas.decode('base64'))
            [last_nsu] = [long(node) for node in xml.xpath(
                '/nfe:retDistDFeInt/nfe:ultNSU/text()',
                namespaces=NFE_NAMESPACE_MAP,
            )]
        return last_nsu

    @api.multi
    def query_nfe_batch(self, raise_error=False):
        nfe_mdes = []
        for company in self:
            try:
                validate_nfe_configuration(company)
                last_nsu = (
                    long(company.last_nsu_nfe) if company.last_nsu_nfe
                    else company.get_last_dfe_nsu()
                )
                nfe_result = distribuicao_nfe(
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
                if company.last_nsu_nfe:
                    # do this here instead of in get_last_dfe_nsu() in case the
                    # exception gets swallowed in the `except` above.
                    company.sudo().last_nsu_nfe = ''
                env_events = self.env['l10n_br_account.document_event']

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

                    obj = env_events.create(event)
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
                            'res_id': obj.id
                        })

                    env_mde = self.env['nfe.mde']
                    for nfe in nfe_result['list_nfe']:
                        exists_nsu = self.env['nfe.mde'].search(
                            [('nSeqEvento', '=', nfe['NSU']),
                             ('company_id', '=', company.id),
                             ]).id
                        nfe_xml = nfe['xml'].encode('utf-8')
                        root = objectify.fromstring(nfe_xml)
                        if nfe['schema'] == u'procNFe_v3.10.xsd' and \
                                not exists_nsu:
                            chave_nfe = root.protNFe.infProt.chNFe
                            exists_chnfe = self.env['nfe.mde'].search(
                                [('chNFe', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.NFe.infNFe.emit.CNPJ))
                                partner = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    'nNFe': root.NFe.infNFe.ide.nNF,
                                    'chNFe': chave_nfe,
                                    'nSeqEvento': nfe['NSU'],
                                    'xNome': root.NFe.infNFe.emit.xNome,
                                    'tpNF': str(root.NFe.infNFe.ide.tpNF),
                                    'vNF': root.NFe.infNFe.total.ICMSTot.vNF,
                                    # 'cSitNFe': str(root.cSitNFe),
                                    'state': 'pending',
                                    'dataInclusao': datetime.now(),
                                    'CNPJ': cnpj_forn,
                                    'IE': root.NFe.infNFe.emit.IE,
                                    'partner_id': partner.id,
                                    'dEmi': datetime.strptime(
                                        str(root.NFe.infNFe.ide.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': company.id,
                                    'formInclusao': u'Verificação agendada'
                                }
                                obj_nfe = env_mde.create(invoice_eletronic)
                                file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                                self.env['ir.attachment'].create(
                                    {
                                        'name': file_name,
                                        'datas': base64.b64encode(nfe_xml),
                                        'datas_fname': file_name,
                                        'description': u'NFe via manifesto',
                                        'res_model': 'nfe.mde',
                                        'res_id': obj_nfe.id
                                    })
                        elif nfe['schema'] == 'resNFe_v1.01.xsd' and \
                                not exists_nsu:
                            chave_nfe = root.chNFe
                            exists_chnfe = self.env['nfe.mde'].search(
                                [('chNFe', '=', chave_nfe)]).id

                            if not exists_chnfe:
                                cnpj_forn = self._mask_cnpj(
                                    ('%014d' % root.CNPJ))
                                partner = self.env['res.partner'].search(
                                    [('cnpj_cpf', '=', cnpj_forn)])

                                invoice_eletronic = {
                                    # 'nNFe': root.NFe.infNFe.ide.nNF,
                                    'chNFe': chave_nfe,
                                    'nSeqEvento': nfe['NSU'],
                                    'xNome': root.xNome,
                                    'tpNF': str(root.tpNF),
                                    'vNF': root.vNF,
                                    'cSitNFe': str(root.cSitNFe),
                                    'state': 'pending',
                                    'dataInclusao': datetime.now(),
                                    'CNPJ': cnpj_forn,
                                    'IE': root.IE,
                                    'partner_id': partner.id,
                                    'dEmi': datetime.strptime(
                                        str(root.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': company.id,
                                    'formInclusao': u'Verificação agendada - '
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
                                        'res_model': 'nfe.mde',
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

                    obj = env_events.create(event)

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
                            'res_id': obj.id
                        })
        return nfe_mdes
