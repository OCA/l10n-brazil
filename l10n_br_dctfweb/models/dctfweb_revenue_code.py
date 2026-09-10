# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    MIT_GOLD_CODE,
    MIT_GROUP,
    MIT_GROUP_JSON_KEY,
    MIT_OTHER_CONTRIBUTIONS_NO_ESTABLISHMENT,
    MIT_PERIODICITY,
    MIT_POSTPONED_EXTENSION,
    MIT_RET_NO_INCORPORATION,
    MIT_SCP_GROUPS,
)


class DctfwebRevenueCode(models.Model):
    """A revenue code of the MIT table.

    This is the authority's own table (manual do MIT, item 10.1): 240 codes,
    each one bound to a tax group and to a periodicity. The record is what
    decides which extra fields a debit has to carry, so the serializer never
    guesses: it asks the code.
    """

    _name = "l10n_br_dctfweb.revenue.code"
    _description = "MIT Revenue Code"
    _order = "group, code, extension"
    _rec_names_search = ["name", "code", "mit_code"]

    code = fields.Char(
        size=4,
        required=True,
        help="Revenue code, 4 digits, as published in the DARF table.",
    )
    extension = fields.Char(
        size=2,
        required=True,
        help="Variation of the revenue code, 2 digits.",
    )
    mit_code = fields.Char(
        compute="_compute_mit_code",
        store=True,
        help="The 6 digits the layout writes in CodigoDebito, code plus extension.",
    )
    name = fields.Char(required=True)
    group = fields.Selection(
        selection=MIT_GROUP,
        required=True,
        help="Tax group the debit is written under, inside the Debitos object.",
    )
    periodicity = fields.Selection(
        selection=MIT_PERIODICITY,
        required=True,
        help="Assessment periodicity of the code, as published in the manual.",
    )
    active = fields.Boolean(default=True)

    # The fields below are the layout rules made explicit. They are stored so a
    # debit can be validated without reading the manual again.
    requires_period = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="PaDebito: the day or the ten-day period of a daily or ten-day code.",
    )
    requires_establishment = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="CnpjEstabelecimento: the establishment the debit belongs to.",
    )
    requires_incorporation = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="CnpjIncorporacao: the real estate development the debit belongs to.",
    )
    allows_scp = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="CnpjScp: the unincorporated joint venture the debit belongs to.",
    )
    requires_gold_city = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="CodigoMunicipioOuro: the city the gold was produced in.",
    )
    is_postponed = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="AnoPostergado: IRPJ or CSLL postponed from an earlier period.",
    )
    requires_debit_year = fields.Boolean(
        compute="_compute_layout_rules",
        store=True,
        help="AnoDebito: annual IRPJ or CSLL adjustment, declared in March.",
    )

    _sql_constraints = [
        (
            "unique_code_extension",
            "unique(code, extension)",
            "This revenue code and extension are already registered.",
        )
    ]

    @api.depends("code", "extension")
    def _compute_mit_code(self):
        for record in self:
            record.mit_code = f"{record.code or ''}{record.extension or ''}"

    @api.depends("group", "periodicity", "mit_code", "extension", "name")
    def _compute_layout_rules(self):
        """Read the layout rules off the code itself.

        Sources: MIT JSON import layout 1.0 (rectified 2025-02-20), fields
        PaDebito, CnpjEstabelecimento, CnpjIncorporacao, CnpjScp,
        CodigoMunicipioOuro, AnoPostergado and AnoDebito; and the MIT manual,
        item 4.2, which lists the codes excluded from the establishment and the
        incorporation rules.
        """
        for record in self:
            group = record.group
            mit_code = record.mit_code or ""
            record.requires_period = record.periodicity in ("daily", "ten_day")
            record.requires_establishment = group == "ipi" or (
                group == "other_contributions"
                and mit_code != MIT_OTHER_CONTRIBUTIONS_NO_ESTABLISHMENT
            )
            record.requires_incorporation = (
                group == "ret" and mit_code != MIT_RET_NO_INCORPORATION
            )
            # The table marks the joint venture codes in the description
            # itself, which is how the authority distinguishes them.
            record.allows_scp = (
                group in MIT_SCP_GROUPS and "SCP" in (record.name or "").upper()
            )
            record.requires_gold_city = mit_code == MIT_GOLD_CODE
            record.is_postponed = (
                group in ("irpj", "csll")
                and record.extension == MIT_POSTPONED_EXTENSION
            )
            record.requires_debit_year = (
                group in ("irpj", "csll")
                and record.periodicity == "annual"
                and record.extension != MIT_POSTPONED_EXTENSION
            )

    @api.constrains("code", "extension")
    def _check_digits(self):
        for record in self:
            if not (record.code or "").isdigit() or len(record.code) != 4:
                raise ValidationError(
                    _("The revenue code %s must have 4 digits.") % record.code
                )
            if not (record.extension or "").isdigit() or len(record.extension) != 2:
                raise ValidationError(
                    _("The extension of the revenue code %s must have 2 digits.")
                    % record.code
                )

    @property
    def json_key(self):
        """The name of the JSON object this code is written under."""
        self.ensure_one()
        return MIT_GROUP_JSON_KEY[self.group]

    def name_get(self):
        return [
            (record.id, f"{record.code}-{record.extension} {record.name}")
            for record in self
        ]
