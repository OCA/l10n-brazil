# -*- coding: utf-8 -*-
#
# Copyright 2016 KMEE
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class AccountInvoice(SpedCalculoImposto, models.Model):
    _inherit = 'account.invoice'

    sped_documento_ids = fields.Many2one(
        comodel_name='sped.documento',
        inverse_name='invoice_id',
        string=u'Documentos Fiscais',
    )
    order_line = fields.One2many(
        #
        # Workarrond para termos os mesmos campos nos outros objetos
        #
        'account.invoice.line',
        related='invoice_line_ids',
        string='Order Lines',
        readonly=True,
    )

    def _get_date(self):
        """
        Return the document date
        Used in _amount_all_wrapper
        """
        date = super(AccountInvoice, self)._get_date()
        if self.date_invoice:
            return self.date_invoice
        return date

    @api.one
    @api.depends(
        'invoice_line_ids.price_subtotal',
        'tax_line_ids.amount',
        'currency_id',
        'company_id',
        'date_invoice',
        'type',
        #
        # Brasil
        #
        'invoice_line_ids.vr_nf',
        'invoice_line_ids.vr_fatura',
    )
    def _compute_amount(self):
        if not self.is_brazilian:
            return super(AccountInvoice, self)._compute_amount()
        self._amount_all_brazil()
        # FIX ME
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if (self.currency_id and self.company_id and
                self.currency_id != self.company_id.currency_id):
            currency_id = self.currency_id.with_context(
                date=self._get_date())
            amount_total_company_signed = \
                currency_id.compute(self.amount_total,
                                    self.company_id.currency_id)
            amount_untaxed_signed = \
                currency_id.compute(self.amount_untaxed,
                                    self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign


    @api.model
    def create(self, dados):
        invoice = super(AccountInvoice, self).create(dados)
        return invoice

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if not invoice.is_brazilian:
                super(AccountInvoice, self).action_move_create()
                continue
                # invoice.sped_documento_id.account_move_create()
        return True

    @api.multi
    def invoice_validate(self):
        brazil = self.filtered(lambda inv: inv.is_brazilian)
        brazil.action_sped_create()

        not_brazil = self - brazil

        return super(AccountInvoice, not_brazil | brazil).invoice_validate()

    @api.multi
    def action_view_sped(self):
        # FIXME:
        speds = self.mapped('sped_documento_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(speds) > 1:
            action['domain'] = [('id', 'in', speds.ids)]
        elif len(speds) == 1:
            action['views'] = [
                (self.env.ref('account.invoice_form').id, 'form')
            ]
            action['res_id'] = speds.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _prepare_sped(self, operacao_id):
        """
        Prepare the dict of values to create the new fiscal for an invoice.

        This method may be overridden to implement custom fiscal generation

        (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()

        sped_vals = {
            'empresa_id': self.sped_empresa_id.id,
            'operacao_id': operacao_id.id,  # FIXME
            'participante_id': self.sped_participante_id.id,
            'payment_term_id': self.payment_term_id.id,
            'modelo': operacao_id.modelo,
            'emissao': operacao_id.emissao,
            'natureza_operacao_id': operacao_id.natureza_operacao_id.id,
            'infcomplementar': self.comment or '',
            'journal_id': self.journal_id.id,
            # 'duplicata_ids': ,
            # 'pagamento_ids': ,
            # 'transportadora_id': ,
            # 'volume_ids': ,
            # 'name': self.client_order_ref or '',
            # 'origin': self.name,
            # 'type': 'out_invoice',
            # 'account_id':
            #   self.partner_invoice_id.property_account_receivable_id.id,
            # 'partner_shipping_id': self.partner_shipping_id.id,
            # 'user_id': self.user_id and self.user_id.id,
            # 'team_id': self.team_id.id
        }
        return sped_vals

    def _brazil_group(self, operacao_id):
        """ Separamos por parceiro, endereço de entrega e operação.

        :param operacao_id:
        :return:
        """
        return (
            self.sped_participante_id.partner_id.id,
            self.sped_participante_id.partner_id.address_get(
                ['delivery'])['delivery'],
            operacao_id,
        )

    @api.multi
    def action_sped_create(self, grouped=False, send=False):
        """
        Create the sped documento associated to the invoice
        :param grouped:

        if True, sped_documento are grouped by invoice id.

        If False, sped_documento are grouped by
                        (partner_invoice_id, sped_operacao)
        :param send: if True, electronic document will be automatically sent.

        :returns: list of created documents
        """
        sped_obj = self.env['sped.documento']
        precision = self.env['decimal.precision'].precision_get('Account')
        documents = {}
        references = {}
        for invoice in self:
            #
            # FIXME: Não esta faturando em lote.
            #
            for operacao in self.order_line.mapped('operacao_id'):
                #
                # Verifica as operações das linhas;
                #
                # Quando for nota conjugada, devemos implementar algo?
                #
                # Melhorar esta lógica
                #
                group_key = invoice._brazil_group(operacao.id)
                for line in invoice.order_line.filtered(
                        lambda line: line.operacao_id == operacao):

                    if group_key not in documents:
                        sped_data = invoice._prepare_sped(operacao)
                        sped_documento = sped_obj.create(sped_data)
                        sped_documento.calcula_imposto_cabecalho()
                        references[sped_documento] = invoice
                        invoice.sped_documento_ids = sped_documento.id
                        documents[group_key] = sped_documento
                    elif group_key in documents:
                        #
                        # TODO: Verificar a origem do pedido do cliente xPed
                        #
                        vals = {}

                        if (invoice.name not in
                                documents[group_key].origin.split(', ')):

                            vals['origin'] = (
                                documents[group_key].origin +
                                ', ' +
                                invoice.name
                            )

                        if (invoice.client_invoice_ref and
                            invoice.client_invoice_ref not in
                            documents[group_key].name.split(', ') and
                            invoice.client_invoice_ref !=
                                documents[group_key].name):

                            vals['name'] = (
                                documents[group_key].name +
                                ', ' +
                                invoice.client_invoice_ref
                            )

                        documents[group_key].write(vals)

                    line.sped_line_create(documents[group_key].id)

                if references.get(documents.get(group_key)):
                    if invoice not in references[documents[group_key]]:

                        references[sped_documento] = \
                            references[sped_documento] | invoice

        if not documents:
            raise UserError(_('There is no line_ids line.'))

        for sped_documento in documents.values():
            if not sped_documento.item_ids:
                raise UserError(_('There is no fiscal line.'))

            for line in sped_documento.item_ids:
                line._set_additional_fields(sped_documento)

            sped_documento.calcula_imposto()

            # sped_documento.mensagem_enviado_faturamento(
            #     sped_documento, references[sped_documento])
            #

        return [doc.id for doc in documents.values()]

    def mensagem_enviado_faturamento(self, sped_documento, references):

        return sped_documento.message_post_with_view(
            'mail.message_origin_link',
            values={
                'self': sped_documento,
                'origin': references
            },
            subtype_id=self.env.ref('mail.mt_note').id
        )