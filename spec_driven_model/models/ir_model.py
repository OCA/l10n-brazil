# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import re
from collections import defaultdict

from odoo import models

SPEC_FIELD_PREFIX_RE = re.compile(r"^([a-z]+)\d{2}_")


def disambiguate_spec_labels(cls):
    """Dynamically disambiguate the labels of spec fields that would
    otherwise be duplicates.

    NFe, CTe, MDFe... XSD schemas share many tags with the same label
    and those spec fields tend to be injected into the same Odoo models
    (res.partner, l10n_br_fiscal.document...). Odoo then emits a
    "Two fields ... have the same label" warning for each such pair of
    fields. These warnings are not legit in the spec_driven_model
    context: the labels come from the XSD schemas and cannot be changed
    without diverging from the spec. So instead we dynamically
    disambiguate the labels of the spec fields that would be duplicate
    by appending their schema and XSD tag, e.g. "Nome do município
    (cte_xMun)" or "Dados do endereço (cte_enderExped)".
    """
    by_label = defaultdict(list)
    for name, field in cls._fields.items():
        if not field.string:
            continue
        match = SPEC_FIELD_PREFIX_RE.match(name)
        if not match:
            # regular field: tracked to detect collisions with spec
            # fields, but its label is never changed
            by_label[field.string].append((name, field, None, None))
            continue
        schema = match.group(1)
        tag = name[match.end() :]
        suffix = f"({schema}_{tag})"
        # strip our own suffix if already applied in a previous registry
        # build (direct field objects may be shared between builds)
        base_label = field.string
        if base_label.endswith(f" {suffix}"):
            base_label = base_label[: -len(suffix) - 1]
        by_label[base_label].append((name, field, schema, tag))

    for fields in by_label.values():
        if len(fields) < 2:
            continue
        for _name, field, schema, tag in fields:
            if schema is None:
                continue
            suffix = f"({schema}_{tag})"
            # idempotent: a direct field object may already have been
            # disambiguated in a previous registry build of this process
            if field.string.endswith(f" {suffix}"):
                continue
            field.string = f"{field.string} {suffix}"


class IrModelFields(models.Model):
    """
    When NFe, CTe, MDFe... XSD spec fields are injected into the same
    Odoo model (either directly as a SpecModel or StackedModel, either
    through the _inherits delegation mechanism used by l10n_br_account
    for instance), many of them share the same label coming from the XSD
    schemas. Odoo then emits a "Two fields ... have the same label"
    warning in _reflect_fields for each such pair of fields.

    These warnings are not legit in the spec_driven_model context: the
    labels come from the XSD schemas and cannot be changed without
    diverging from the spec. So we dynamically disambiguate the labels
    of the spec fields that would be duplicate right before the label
    check of _reflect_fields, whatever the way (direct or delegated)
    the spec fields were injected.
    """

    _inherit = "ir.model.fields"

    def _reflect_fields(self, model_names):
        for model_name in model_names:
            disambiguate_spec_labels(self.env[model_name])
        return super()._reflect_fields(model_names)
