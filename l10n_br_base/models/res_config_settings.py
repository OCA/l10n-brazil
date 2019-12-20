# @ 2016 Kmee - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_cnpj_multi_ie = fields.Boolean(
        string="Multiple partners with the same CNPJ",
        config_parameter="l10n_br_base_allow_cnpj_multi_ie",
        default=False,
    )

    module_l10n_br_zip = fields.Boolean(string="Use Brazilian postal service API")

    module_l10n_br_validate_cpf_cnpj_ie = fields.Boolean(string="Allow CPF, CNPJ and IE validation")

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        select_type = self.env['ir.config_parameter'].sudo()

        select_type.set_param('l10n_br_base.validate_cpf_cnpj_ie',
                              self.module_l10n_br_validate_cpf_cnpj_ie)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        select_type = self.env['ir.config_parameter'].sudo()

        sell = select_type.get_param('l10n_br_base.validate_cpf_cnpj_ie')

        res.update({'module_l10n_br_validate_cpf_cnpj_ie': sell})

        return res
