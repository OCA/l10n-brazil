# -*- coding: utf-8 -*-
# @ 2016 Kmee - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class L10nBrBaseResConfig(models.TransientModel):
    _name = 'l10n_br_base.config.settings'
    _inherit = 'res.config.settings'

    allow_cnpj_multi_ie = fields.Boolean(
        string=u'Permitir o cadastro com CNPJs e IE diferentes',
        default=False,
    )
    check_cnpj = fields.Boolean(
        string=u'Valida CNPJ',
    )
    check_ie = fields.Boolean(
        string=u'Valida IE',
    )
    check_zip = fields.Boolean(
        string=u'Valida Cep',
    )
    check_phone = fields.Boolean(
        string=u'Valida Telefone',
    )
    check_mail = fields.Boolean(
        string=u'Valida Email',
    )

    @api.model
    def get_default_allow_cnpj_multi_ie(self, field):
        return {
            'allow_cnpj_multi_ie':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_allow_cnpj_multi_ie")
        }

    @api.multi
    def set_allow_cnpj_multi_ie(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_allow_cnpj_multi_ie",
                config.allow_cnpj_multi_ie or '')

    @api.model
    def get_default_check_cnpj(self, field):
        return {
            'check_cnpj':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_cnpj")
        }

    @api.multi
    def set_check_cnpj(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_cnpj",
                config.check_cnpj or '')

    @api.model
    def get_default_check_ie(self, field):
        return {
            'check_ie':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_ie")
        }

    @api.multi
    def set_check_ie(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_ie",
                config.check_ie or '')

    @api.model
    def get_default_check_zip(self, field):
        return {
            'check_zip':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_zip")
        }

    @api.multi
    def set_check_zip(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_zip",
                config.check_zip or '')

    @api.model
    def get_default_check_phone(self, field):
        return {
            'check_phone':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_phone")
        }

    @api.multi
    def set_check_phone(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_phone",
                config.check_phone or '')

    @api.model
    def get_default_check_mail(self, field):
        return {
            'check_mail':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_mail")
        }

    @api.multi
    def set_check_mail(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_mail",
                config.check_mail or '')
