# Copyright 2025 - Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import fields, models


class TaxDefinition(models.Model):
    """SPED EFD ICMS/IPI: Tabela 5.3 adjustment code on fiscal benefits."""

    _inherit = "l10n_br_fiscal.tax.definition"

    sped_cod_aj = fields.Char(
        string="SPED Adjustment Code",
        size=8,
        help="Código de ajuste da apuração do ICMS (Tabela 5.3) usado no "
        "registro C197 do SPED EFD ICMS/IPI para este benefício fiscal. "
        "Quando vazio, o C197 usa o cBenef declarado pelo fornecedor.",
    )


class ICMSRelief(models.Model):
    """SPED EFD ICMS/IPI: Tabela 5.3 adjustment code on ICMS relief."""

    _inherit = "l10n_br_fiscal.icms.relief"

    sped_cod_aj = fields.Char(
        string="SPED Adjustment Code",
        size=8,
        help="Código de ajuste da apuração do ICMS (Tabela 5.3) usado no "
        "registro C197 do SPED EFD ICMS/IPI para este motivo de desoneração. "
        "Quando vazio, o C197 usa o cBenef declarado pelo fornecedor.",
    )
