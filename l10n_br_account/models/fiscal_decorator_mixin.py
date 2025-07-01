# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, fields, models
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class InheritsCheckMuteLogger(mute_logger):
    """
    Mute the Model#_inherits_check warning
    because the _inherits field is not required.
    (some account.move may have no fiscal document)
    """

    def filter(self, record):
        msg = record.getMessage()
        if "Field definition for _inherits reference" in msg:
            return 0
        return super().filter(record)


class FiscalDecoratorMixin(models.AbstractModel):
    _name = "l10n_br_account.decorator.mixin"
    _description = """A mixin to decorate l10n_br_fiscal_document(.line) easily.
    It specially deals with related and compute fields inherited with _inherits.
    """
    _fiscal_decorator_model = None
    _fiscal_decorator_compute_blacklist = []  # conflicting computes to skip

    @api.model
    def _add_inherited_fields(self):
        """
        Add related and computed fields inherited with _inherits from the
        _fiscal_decorator_model preserving the related and compute attributes.
        The original Odoo method would indeed alter the related attribute in a way
        that disables dynamic onchanges/compute during the edition before saving.
        As the account.move(.line) inherits with _inherit (no s) from the
        l10n_br_fiscal.document(.line).mixin.methods, we can preserve the compute
        attribute except for compute in the _fiscal_decorator_compute_blacklist.
        """
        if self._fiscal_decorator_model is not None:
            for name, field in self.env.registry[
                self._fiscal_decorator_model
            ]._fields.items():
                field_cls = type(field)
                if (
                    name in self._fields
                    or field_cls in [fields.One2many, fields.Many2many]
                    or not (field.compute or field.related)
                    or field.compute in self._fiscal_decorator_compute_blacklist
                ):  # not a problematic case, or expected for o2m and m2m or blacklist
                    continue
                if field.compute and field.store:
                    _logger.debug(
                        f"field {name} is a compute with store=True in "
                        f"{self._fiscal_decorator_model} with store=True. "
                        "It may not be refreshed 'live' before saving in "
                        f"{self._name}. For that, you may want to override "
                        f"it in {self._name}."
                    )
                    continue
                if isinstance(field.compute, str) and not hasattr(
                    self.__class__, field.compute
                ):
                    continue

                attrs = {
                    "related": field.related,
                    "compute": field.compute,
                    "inverse": field.inverse,
                    "comodel_name": field.comodel_name,
                }

                if field.related and field.related.startswith("document_id."):
                    attrs["related"] = field.related.replace("document_id.", "move_id.")

                if field_cls == fields.Selection:  # required for some NFe/CTe fields
                    attrs["selection"] = field.selection

                self._add_field(
                    name,
                    field_cls(**attrs),
                )
        return super()._add_inherited_fields()

    @api.model
    def _inherits_check(self):
        """
        Overriden to avoid the super method to set the fiscal_document(_line)_id
        field as required.
        """
        with InheritsCheckMuteLogger("odoo.models"):  # mute spurious warnings
            res = super()._inherits_check()
        if self._fiscal_decorator_model is not None:
            field_name = self._inherits[self._fiscal_decorator_model]
            field = self._fields.get(field_name)
            field.required = False  # unset the required = True assignement
        return res

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(create_from_account=True)
        return super().create(vals_list)
