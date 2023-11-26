# Copyright (C) 2023  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.icms import ICMS_TAX_BENEFIT_TYPE


# pylint: disable=consider-merging-classes-inherited
class TaxDefinitionBenefit(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    is_benefit = fields.Boolean(
        string="Benefit?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    code = fields.Char(
        size=8,
        states={"draft": [("readonly", False)]},
    )

    name = fields.Char(
        states={"draft": [("readonly", False)]},
    )

    description = fields.Text(
        states={"draft": [("readonly", False)]},
    )

    benefit_type = fields.Selection(
        selection=ICMS_TAX_BENEFIT_TYPE,
        states={"draft": [("readonly", False)]},
    )

    # Anexo RICMS
    # Informar o anexo do Regulamento do ICMS.

    # Artigo
    # Informar o artigo referente ao enquadramento legal da operação
    # ou prestação geradora de crédito acumulado.

    # Inciso
    # Informar o inciso referente ao enquadramento legal da operação
    # ou prestação geradora de crédito acumulado.

    # Alínea
    # Alínea referente ao enquadramento legal da operação ou prestação
    # geradora de crédito acumulado.

    # Parágrafo
    # Informar o parágrafo referente ao enquadramento legal da operação
    # ou prestação geradora de crédito acumulado.

    # Item RICMS
    # Informar o item do Regulamento do ICMS.

    # Letra RICMS
    # Informar a letra do Regulamento do ICMS.

    def _get_search_domain(self, tax_definition):
        """Create domain to be used in contraints methods"""
        domain = super()._get_search_domain(tax_definition)
        if tax_definition.icms_regulation_id and tax_definition.is_benefit:
            domain.append(
                ("is_benefit", "=", tax_definition.is_benefit),
            )

            if tax_definition.ncm_ids:
                domain.append(
                    ("ncm_ids", "in", tax_definition.ncm_ids.ids),
                )

            if tax_definition.cest_ids:
                domain.append(
                    ("cest_ids", "in", tax_definition.cest_ids.ids),
                )

            if tax_definition.nbm_ids:
                domain.append(
                    ("nbm_ids", "in", tax_definition.nbm_ids.ids),
                )

            if tax_definition.product_ids:
                domain.append(
                    ("product_ids", "in", tax_definition.product_ids.ids),
                )

            if tax_definition.ncm_exception:
                domain.append(
                    ("ncm_exception", "=", tax_definition.ncm_exception),
                )

        return domain

    @api.constrains("is_benefit", "code", "benefit_type", "state_from_id")
    def _check_tax_benefit_code(self):
        for record in self:
            if record.is_benefit:
                if record.code:
                    if len(record.code) != 8:
                        raise ValidationError(
                            _("Tax benefit code must be 8 characters!")
                        )

                    if record.code[:2].upper() != record.state_from_id.code.upper():
                        raise ValidationError(
                            _("Tax benefit code must be start with state code!")
                        )

                    if record.code[3:4] != record.benefit_type:
                        raise ValidationError(
                            _(
                                "The tax benefit code must contain "
                                "the type of benefit!"
                            )
                        )
