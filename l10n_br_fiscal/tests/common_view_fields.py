# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from lxml import etree

SUBVIEW_TAGS = ("list", "form", "kanban")


class ViewFieldsCheck:
    """Every field of the final arch of a view (as ``get_views`` returns it,
    with the views embedded in the x2many fields) exists in its model."""

    def _primary_views(self, model_name):
        views = self.env["ir.ui.view"].search(
            [
                ("model", "=", model_name),
                ("mode", "=", "primary"),
                ("type", "in", ("form", "list")),
            ]
        )
        return [(view.id, view.type) for view in views] + [
            (False, "form"),
            (False, "list"),
        ]

    def _missing_fields(self, model_name, arch):
        """The field names of the arch that the model does not have, with the
        embedded views of the x2many fields checked against their own model."""
        model = self.env[model_name]
        missing = []
        for node in arch.iterchildren():
            missing += self._missing_in_node(model, node)
        return missing

    def _missing_in_node(self, model, node):
        missing = []
        if node.tag == "field":
            name = node.get("name")
            if name not in model._fields:
                missing.append(f"{model._name}.{name}")
                return missing
            comodel = model._fields[name].comodel_name
            for child in node.iterchildren():
                if child.tag in SUBVIEW_TAGS and comodel:
                    for grandchild in child.iterchildren():
                        missing += self._missing_in_node(self.env[comodel], grandchild)
            return missing
        for child in node.iterchildren():
            missing += self._missing_in_node(model, child)
        return missing

    def check_view_fields(self, model_names):
        checked = 0
        for model_name in model_names:
            if model_name not in self.env:
                continue
            for view_id, view_type in self._primary_views(model_name):
                with self.subTest(model=model_name, view=view_id, type=view_type):
                    try:
                        result = self.env[model_name].get_views([(view_id, view_type)])
                    except ValueError:
                        # the model has no default view of this type
                        continue
                    arch = etree.fromstring(result["views"][view_type]["arch"])
                    missing = self._missing_fields(model_name, arch)
                    self.assertEqual(
                        missing,
                        [],
                        f"fields of the view {view_id or 'default'} ({view_type}) "
                        f"of {model_name} that the model does not have",
                    )
                    checked += 1
        return checked
