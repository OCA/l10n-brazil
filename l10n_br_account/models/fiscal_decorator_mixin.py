# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, models
from odoo.orm import model_classes as orm_model_classes

_logger = logging.getLogger(__name__)


def _check_inherits_allows_optional_fiscal_document(model_cls):
    """Patched version of odoo.orm.model_classes._check_inherits.

    Odoo 19.0 requires _inherits reference fields to be 'delegate' +
    'required' + ondelete='cascade'/'restrict' and raises a TypeError
    otherwise. account.move and account.move.line use _inherits on the
    fiscal document (line) but legitimately allow an empty reference
    (account moves that are not related to Brazilian companies, tax lines
    without fiscal document line...).

    Instead, we wrap the check for the models using this mixin:
    the required bit of the TypeError is relaxed, while the delegate and
    ondelete conditions are still enforced.
    """
    for comodel_name, field_name in model_cls._inherits.items():
        field = model_cls._fields.get(field_name)
        if not field or field.type != "many2one":
            raise TypeError(
                f"Missing many2one field definition for _inherits reference "
                f"{field_name!r} in model {model_cls._name!r}. "
                f"Add a field like: {field_name} = fields.Many2one("
                f"{comodel_name!r}, required=True, ondelete='cascade')"
            )
        delegate_ok = field.delegate and (field.ondelete or "").lower() in (
            "cascade",
            "restrict",
        )
        if not delegate_ok:
            raise TypeError(
                f"Field definition for _inherits reference {field_name!r} "
                f"in {model_cls._name!r} must be marked as 'delegate' with "
                "ondelete='cascade' or 'restrict'"
            )
        # NOTE: the 'required' condition of the original check is
        # voluntarily relaxed for the fiscal decorator models because
        # account.move(.line) may have no fiscal document at all.


_original_check_inherits = orm_model_classes._check_inherits


def _patched_check_inherits(model_cls):
    if getattr(model_cls, "_fiscal_decorator_model", None):
        return _check_inherits_allows_optional_fiscal_document(model_cls)
    return _original_check_inherits(model_cls)


orm_model_classes._check_inherits = _patched_check_inherits
_logger.debug(
    "l10n_br_account: patched odoo.orm.model_classes._check_inherits to "
    "allow optional fiscal document _inherits references"
)


class FiscalDecoratorMixin(models.AbstractModel):
    _name = "l10n_br_account.decorator.mixin"
    _description = """A mixin to decorate l10n_br_fiscal_document(.line) easily.
    It specially deals with related and compute fields inherited with _inherits.
    """
    _fiscal_decorator_model = None

    @api.model_create_multi
    def create(self, vals_list):
        return super(
            FiscalDecoratorMixin,
            self.with_context(create_from_account=True, allow_fiscal_access=True),
        ).create(vals_list)
