# Copyright (C) 2009 Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _

from .constants.fiscal import (
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_DEFAULT,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_DEFAULT
)


class PartnerProfile(models.Model):
    _name = 'fiscal.partner.profile'

    code = fields.Char(
        string=u'Código',
        size=16,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=64)

    is_company = fields.Boolean(
        string=u'Pessoa Jurídica?')

    default = fields.Boolean(
        string=u'Default Profile',
        default=True)

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string=u'Contribuinte do ICMS',
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT)

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_DEFAULT,
        string='Tax Framework')

    cnae_main_id = fields.Many2one(
        comodel_name='fiscal.cnae',
        domain="[('internal_type', '=', 'normal')]",
        string='Main CNAE')

    @api.constrains('default', 'is_company')
    def _check_default(self):
        for fiscal_type in self:
            if len(fiscal_type.search([
                ('default', '=', 'True'),
                ('is_company', '=', fiscal_type.is_company)
            ])) > 1:
                raise ValidationError(
                    _(u'Mantenha apenas um tipo fiscal padrão'
                      u' para Pessoa Física ou para Pessoa Jurídica!'))
            return True
