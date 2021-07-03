# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from erpbrasil.base import misc

from odoo import models


class SpecMixin(models.AbstractModel):
    _inherit = "spec.mixin"

    def _export_field(self, xsd_field, class_obj, member_spec):
        # TODO: Export number required fields with Zero.
        # xsd_required = class_obj._fields[xsd_field]._attrs.get(
        #    'xsd_required')

        if (
            hasattr(class_obj._fields[xsd_field], "xsd_type")
            and class_obj._fields[xsd_field].xsd_type in ("TCnpj", "TCpf")
            and self[xsd_field] is not False
        ):
            return misc.punctuation_rm(self[xsd_field])
        elif (
            hasattr(class_obj._fields[xsd_field], "xsd_type")
            and "TIe" in class_obj._fields[xsd_field].xsd_type
            and self[xsd_field] is not False
        ):
            return misc.punctuation_rm(self[xsd_field])
        elif (
            hasattr(class_obj._fields[xsd_field], "xsd_type")
            and "foneType" in class_obj._fields[xsd_field].xsd_type
            and self[xsd_field] is not False
        ):
            return (
                self[xsd_field]
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "")
                .replace("-", "")
                .replace("+", "")
            )
        elif (
            hasattr(class_obj._fields[xsd_field], "xsd_type")
            and "CEPType" in class_obj._fields[xsd_field].xsd_type
            and self[xsd_field] is not False
        ):
            return self[xsd_field].replace("-", "")
        else:
            return super()._export_field(xsd_field, class_obj, member_spec)
