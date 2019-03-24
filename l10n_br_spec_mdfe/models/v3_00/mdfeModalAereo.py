# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 24 01:00:21 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class Aereo(spec_models.AbstractSpecMixin):
    "Informações do modal Aéreo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.aereo'
    _generateds_type = 'aereo'
    _concrete_rec_name = 'mdfe_nac'

    mdfe30_nac = fields.Char(
        string="nac", xsd_required=True)
    mdfe30_matr = fields.Char(
        string="matr", xsd_required=True)
    mdfe30_nVoo = fields.Char(
        string="nVoo", xsd_required=True)
    mdfe30_cAerEmb = fields.Char(
        string="cAerEmb", xsd_required=True)
    mdfe30_cAerDes = fields.Char(
        string="cAerDes", xsd_required=True)
    mdfe30_dVoo = fields.Date(
        string="dVoo", xsd_required=True)
