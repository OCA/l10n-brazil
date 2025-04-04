# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import mute_logger


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
                f"{self._fiscal_decorator_model}.mixin"
            ]._fields.items():
                field_cls = type(field)
                if (
                    name in self._fields
                    or name.startswith("fiscal_proxy_")
                    or (not field.compute and not field.related)
                    or field_cls in [fields.One2many, fields.Many2many]
                    or field.compute in self._fiscal_decorator_compute_blacklist
                ):
                    continue
                self._add_field(
                    name,
                    field_cls(
                        related=field.related,
                        compute=field.compute,
                        inverse=field.inverse,
                        comodel_name=field.comodel_name,
                    ),
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

    @api.model
    def _inject_shadowed_fields(self, vals_list):
        for vals in vals_list:
            for field in self._shadowed_fields():
                if field in vals:
                    vals[f"fiscal_proxy_{field}"] = vals[field]
