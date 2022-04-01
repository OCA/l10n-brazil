# Copyright 2020 Akretion - Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # TODO - default don't work, solve with data file
    boleto_cnab_api = fields.Char(
        string='Endereço do Boleto CNAB API / BRCobranca',
        help='Endereço Eletrônico IP ou Nome do Boleto CNAB API.',
        default='boleto_cnab_api'
    )

    cnab_return_method = fields.Selection(
        [('manual', 'Manual'),
         ('automatic', 'Automatico')], 'CNAB Return method',
        default='manual',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            boleto_cnab_api=self.env[
                'ir.config_parameter'].sudo().get_param(
                'l10n_br_account_payment_brcobranca.boleto_cnab_api'),
            cnab_return_method=self.env[
                'ir.config_parameter'].sudo().get_param(
                'l10n_br_account_payment_brcobranca.cnab_return_method')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        boleto_cnab_api =\
            self.boleto_cnab_api or 'boleto_cnab_api'

        param.set_param(
            'l10n_br_account_payment_brcobranca.boleto_cnab_api',
            boleto_cnab_api)

        cnab_return_method =\
            self.cnab_return_method or 'manual'

        param.set_param(
            'l10n_br_account_payment_brcobranca.cnab_return_method',
            cnab_return_method)
