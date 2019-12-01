from odoo import models


class SpecMixin(models.AbstractModel):
    """putting this mixin here makes it possible for generated schemas mixins
    to be installed without depending on the fiscal module.
    """
    _description = "root abstract model meant for xsd generated fiscal models"
    _name = 'spec.mixin'
