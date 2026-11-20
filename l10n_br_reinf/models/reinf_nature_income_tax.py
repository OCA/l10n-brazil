# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants import (
    REINF_CLASSIFICATION_INDICATORS,
    REINF_EVENT_TYPES,
    REINF_REVENUE_PERIODICITIES,
    REINF_WITHHOLDING_TAXES,
)


class ReinfNatureIncomeTax(models.Model):
    """One line of the Annex I of the manual: a nature of income, a tax and the
    revenue code the tax is collected under.

    The Annex is not a flat table of natures: the same nature is declared in
    the R-4010 and in the R-4020, carries a different set of taxes in each one,
    and answers a different revenue code when the beneficiary is abroad. That
    is why the mapping is a table of its own and the nature only keeps what
    does not depend on the tax.
    """

    _name = "l10n_br_reinf.nature.income.tax"
    _description = "EFD-Reinf Nature of Income Tax Mapping"
    _order = "nature_income_id, event_type, tax_type, foreign_taxation"

    nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="Nature of Income",
        required=True,
        index=True,
        ondelete="cascade",
    )

    event_type = fields.Selection(
        selection=REINF_EVENT_TYPES,
        string="Event",
        required=True,
        index=True,
        help="Event the nature is declared in with this mapping.",
    )

    tax_type = fields.Selection(
        selection=REINF_WITHHOLDING_TAXES,
        index=True,
        help="Tax the revenue code collects. The tables of the R-4040 and of "
        "the R-4080 do not break the withholding down by tax, so it is empty "
        "there.",
    )

    foreign_taxation = fields.Boolean(
        help="Whether this line applies to the taxation of income of a "
        "beneficiary resident or domiciled abroad (the trib_exterior column of "
        "the Annex I).",
    )

    classification_indicator = fields.Selection(
        selection=REINF_CLASSIFICATION_INDICATORS,
        string="Tax Classification 85",
        help="Whether the line applies to a declarant of the tax "
        "classification 85. It is what picks between the pair of revenue codes "
        "of a nature: the aggregated withholding of a private company answers "
        "595207, and a body of the public administration answers its own pair.",
    )

    revenue_code = fields.Char(
        size=6,
        index=True,
        help="Revenue code (CR) of the DARF the tax is collected under, as the "
        "official table gives it, with the check digits. It can be empty: some "
        "natures have a withholding informed and generate no code of their own "
        "because the collection happens in another event, and the event of the "
        "line is what says which one.",
    )

    date_start = fields.Date(
        string="Start Date",
        index=True,
        help="The published tables version their lines: a revenue code is "
        "replaced without the nature changing, and an event of a closed "
        "competence has to keep answering the code that was valid then.",
    )

    date_end = fields.Date(
        string="End Date",
        index=True,
    )

    periodicity = fields.Selection(
        selection=REINF_REVENUE_PERIODICITIES,
        help="Periodicity of the collection of the revenue code. It says in "
        "which totalizer group of the R-9015 the code is answered.",
    )
