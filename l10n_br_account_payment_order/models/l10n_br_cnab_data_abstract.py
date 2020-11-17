# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class L10nBrCNABDataAbstract(models.AbstractModel):
    _name = 'l10n_br_cnab.data.abstract'
    _inherit = 'mail.thread'
    _description = 'CNAB Data Abstract'

    name = fields.Char(
        string='Name',
        index=True,
        track_visibility='always',
    )
    code = fields.Char(
        string='Code',
        index=True,
        track_visibility='always',
    )
    bank_id = fields.Many2one(
        string='Bank',
        comodel_name='res.bank',
        index=True,
        track_visibility='always',
    )
    payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        string='Payment Method',
        index=True,
        track_visibility='always',
    )
    # Fields used to create domain
    bank_code_bc = fields.Char(
        related='bank_id.code_bc',
        store=True,
        track_visibility='always',
    )
    payment_method_code = fields.Char(
        related='payment_method_id.code',
        store=True,
        track_visibility='always',
    )

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((
                record.id,  '%s - %s' % (
                    record.code, record.name)
            ))
        return result

    @api.constrains('code')
    def check_code(self):
        for record in self:
            # Tamanho do campo é padrão 2 p/ todos os codigos CNAB ?
            if len(record.code) != 2:
                raise ValidationError(_(
                    'The field Code should have two characters.'))

            # Mesmo o record que está sendo alterado não ter sido ainda salvo
            # a pesquisa acaba trazendo ele, por isso o filtro 'id'
            search_domain = [
                ('id', '!=', record.id),
                ('code', '=', record.code),
                ('payment_method_code', '=', record.payment_method_code),
            ]
            # 240 mais padronizado
            if record.payment_method_id.code != '240':
                search_domain.append(
                    ('bank_code_bc', '=', record.bank_code_bc))
            code_already_exist = record.search(search_domain)
            if code_already_exist:
                code_name_exist = \
                    code_already_exist.code + ' - ' + code_already_exist.name
                raise ValidationError(_(
                    'The Code %s already exist %s for Bank %s'
                    ' and CNAB %s.') % (
                    record.code, code_name_exist, record.bank_id.name,
                    record.payment_method_code))
