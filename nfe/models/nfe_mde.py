# -*- coding: utf-8 -*-
# Copyright (C) 2015 Trustcode - www.trustcode.com.br
#              Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


import base64
from datetime import datetime

from odoo import models, api, fields, _
from ..sped.nfe.validator.config_check import \
    validate_nfe_configuration
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning as UserError

from ..service.mde import download_nfe, send_event


class L10nBrDocumentEvent(models.Model):
    _inherit = 'l10n_br_account.document_event'

    mde_event_id = fields.Many2one('nfe.mde', string="Manifesto")


class NfeMde(models.Model):
    _name = 'nfe.mde'
    _rec_name = 'nSeqEvento'
    _inherit = [
        'ir.needaction_mixin'
    ]

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.nNFe, rec.CNPJ, rec.xNome)
                 ) for rec in self]

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=_default_company, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Moeda', readonly=True)
    chNFe = fields.Char(string="Chave de Acesso", size=50, readonly=True)
    nNFe = fields.Char(string="Número NFe", size=10, readonly=True)
    nSeqEvento = fields.Char(
        string="Número Sequencial", readonly=True, size=20)
    CNPJ = fields.Char(string="CNPJ", readonly=True, size=20)
    IE = fields.Char(string="RG/IE", readonly=True, size=20)
    xNome = fields.Char(string="Razão Social", readonly=True, size=200)
    partner_id = fields.Many2one('res.partner', string='Fornecedor')
    dEmi = fields.Datetime(string="Data Emissão", readonly=True)
    tpNF = fields.Selection([('0', 'Entrada'), ('1', 'Saída')],
                            string="Tipo de Operação", readonly=True)
    vNF = fields.Float(string="Valor Total da NF-e",
                       readonly=True, digits=(18, 2))
    cSitNFe = fields.Selection([('1', 'Autorizada'), ('2', 'Cancelada'),
                                ('3', 'Denegada')],
                               string="Situação da NF-e", readonly=True)
    state = fields.Selection(string="Situação da Manifestação", readonly=True,
                             selection=[
                                 ('pending', 'Pendente'),
                                 ('ciente', 'Ciente da operação'),
                                 ('confirmado', 'Confirmada operação'),
                                 ('desconhecido', 'Desconhecimento'),
                                 ('nao_realizado', 'Não realizado')
                             ])
    formInclusao = fields.Char(string="Forma de Inclusão", readonly=True)
    dataInclusao = fields.Datetime(string="Data de Inclusão", readonly=True)

    document_event_ids = fields.One2many(
        'l10n_br_account.document_event',
        'mde_event_id', string="Documentos eletrônicos")

    xml_downloaded = fields.Boolean(u'Xml já baixado?', default=False)
    xml_imported = fields.Boolean(u'Xml já importado?', default=False)

    @api.constrains('CNPJ', 'partner_id')
    def _check_partner_id(self):
        for partner in self:
            if (partner.partner_id and
                    partner.CNPJ != partner.partner_id.cnpj_cpf):
                raise ValidationError(_(
                    "O Parceiro não possui o "
                    "mesmo CNPJ/CPF do manifesto atual"))

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'pending')]

    def _create_event(self, response, nfe_result, type_event='13'):
        return {
            'type': type_event, 'response': response,
            'company_id': self.company_id.id,
            'status': nfe_result['code'], 'message': nfe_result['message'],
            'create_date': datetime.now(), 'write_date': datetime.now(),
            'end_date': datetime.now(), 'state': 'done',
            'origin': response, 'mde_event_id': self.id,
            'file_sent': nfe_result.get('file_sent', False),
            'file_returned': nfe_result.get('file_returned', False),
        }

    def _create_attachment(self, event, result):
        file_name = 'evento-manifesto-%s.xml' % datetime.now().strftime(
            '%Y-%m-%d-%H-%M')
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas':
                    result.get('file_returned') and
                    base64.b64encode(result['file_returned']),
                'datas_fname': file_name,
                'description': u'Evento Manifesto Destinatário',
                'res_model': 'l10n_br_account.document_event',
                'res_id': event.id
            })

    @api.multi
    def action_known_emission(self):
        for record in self:
            validate_nfe_configuration(record.company_id)
            nfe_result = send_event(
                record.company_id, record.chNFe, 'ciencia_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Ciência da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'ciente'
            elif nfe_result['code'] == '573':
                record.state = 'ciente'
                event['response'] = \
                    'Ciência da operação já previamente realizada'
            else:
                event['response'] = 'Ciência da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_confirm_operation(self):
        for record in self:
            validate_nfe_configuration(record.company_id)
            nfe_result = send_event(
                record.company_id,
                record.chNFe,
                'confirma_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Confirmação da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'confirmado'
            else:
                event['response'] = 'Confirmação da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_unknown_operation(self):
        for record in self:
            validate_nfe_configuration(record.company_id)
            nfe_result = send_event(
                record.company_id,
                record.chNFe,
                'desconhece_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event(
                'Desconhecimento da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'desconhecido'
            else:
                event['response'] = 'Desconhecimento da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_not_operation(self):
        for record in self:
            validate_nfe_configuration(record.company_id)
            nfe_result = send_event(
                record.company_id,
                record.chNFe,
                'nao_realizar_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Operação não realizada', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'nap_realizado'
            else:
                event['response'] = \
                    'Tentativa de Operação não realizada sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_download_xml(self):
        result = True
        for record in self:
            validate_nfe_configuration(record.company_id)
            nfe_result = download_nfe(record.company_id, record.chNFe)
            env_events = record.env['l10n_br_account.document_event']
            if nfe_result['code'] == '138':
                event = record._create_event(
                    'Download NFe concluido', nfe_result, type_event='10')
                env_events.create(event)
                file_name = 'NFe%s.xml' % record.chNFe
                record.env['ir.attachment'].create(
                    {
                        'name': file_name,
                        'datas': base64.b64encode(nfe_result['nfe']),
                        'datas_fname': file_name,
                        'description':
                            u'XML NFe - Download manifesto do destinatário',
                        'res_model': 'nfe.mde',
                        'res_id': record.id
                    })
                record.write({'xml_downloaded': True})
            else:
                result = False
                event = record._create_event(
                    'Download NFe não efetuado', nfe_result, type_event='10')
                event = env_events.create(event)
                record._create_attachment(event, nfe_result)
        return result

    @api.multi
    def action_import_xml(self):
        self.ensure_one()
        attach_xml = self.env['ir.attachment'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'nfe.mde'),
            ('name', '=like', 'NFe%')
        ], limit=1)

        if attach_xml:
            import_doc = {'edoc_input': attach_xml.datas,
                          'file_name': attach_xml.datas_fname}
            nfe_import = self.env[
                'nfe_import.account_invoice_import'].create(import_doc)

            res = self.env.ref(
                'nfe.action_l10n_br_account_periodic_processing_edoc_import'
            ).read()[0]
            res['domain'] = "[('id', 'in', %s)]" % [nfe_import.id]
            res['res_id'] = nfe_import.id
            return res

        else:
            raise UserError(
                u'O arquivo xml já não existe mais no caminho especificado\n'
                u'Contate o responsável pelo sistema')

    @api.multi
    def action_visualizar_danfe(self):
        return self.env['report'].get_action(self, 'danfe_nfe_mde',
                                             data={'ids': self.ids,
                                                   'model': 'nfe.mde'})
