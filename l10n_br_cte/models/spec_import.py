# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SpecMixinCte(models.AbstractModel):
    """Extension of the mixin of the CT-e, not of the generic one: the models of the
    schema are rebuilt from their own mixin, and an override placed on the generic
    ``spec.mixin_import`` is lost when the registry is rebuilt (the tests of
    ``spec_driven_model`` do it), so the groups of a CT-e would be matched again."""

    _inherit = "spec.mixin.cte"

    @api.model
    def match_record(self, rec_dict, parent_dict, model=None):
        """The groups of a CT-e (collection, installments, components...) belong to
        the document that carries them: matching them by their first field would
        take the installment 001 of another CT-e away from it."""
        target = self if model is None else model
        if self.env.context.get("spec_schema") == "cte" and target._name.startswith(
            "cte.40."
        ):
            return False
        return super().match_record(rec_dict, parent_dict, model=model)
