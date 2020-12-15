# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import models


class SpecMixin(models.AbstractModel):
    """putting this mixin here makes it possible for generated schemas mixins
    to be installed without depending on the fiscal module.
    """
    _description = "root abstract model meant for xsd generated fiscal models"
    _name = 'spec.mixin'
    # _spec_module = 'override.with.your.python.module'
    # _odoo_module = 'your Odoo module'
    # _field_prefix = 'your_field_prefix_'
    # _schema_name = 'your_schema_name'
