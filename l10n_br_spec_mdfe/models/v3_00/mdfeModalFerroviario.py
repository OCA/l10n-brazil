# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 24 01:00:23 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class Ferrov(spec_models.AbstractSpecMixin):
    "Informações do modal Ferroviário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.ferrov'
    _generateds_type = 'ferrov'
    _concrete_rec_name = 'mdfe_trem'

    mdfe30_trem = fields.Many2one(
        "mdfe.30.trem",
        string="trem", xsd_required=True)
    mdfe30_vag = fields.One2many(
        "mdfe.30.vag",
        "mdfe30_vag_ferrov_id",
        string="vag", xsd_required=True
    )


class Trem(spec_models.AbstractSpecMixin):
    "Informações da composição do trem"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.trem'
    _generateds_type = 'tremType'
    _concrete_rec_name = 'mdfe_xPref'

    mdfe30_xPref = fields.Char(
        string="Prefixo do Trem", xsd_required=True)
    mdfe30_dhTrem = fields.Datetime(
        string="Data e hora de liberação do trem na origem")
    mdfe30_xOri = fields.Char(
        string="Origem do Trem", xsd_required=True)
    mdfe30_xDest = fields.Char(
        string="Destino do Trem", xsd_required=True)
    mdfe30_qVag = fields.Char(
        string="Quantidade de vagões carregados",
        xsd_required=True)


class Vag(spec_models.AbstractSpecMixin):
    "informações dos Vagões"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.vag'
    _generateds_type = 'vagType'
    _concrete_rec_name = 'mdfe_pesoBC'

    mdfe30_vag_ferrov_id = fields.Many2one(
        "mdfe.30.ferrov")
    mdfe30_pesoBC = fields.Monetary(
        digits=3, string="Peso Base de Cálculo de Frete em Toneladas",
        xsd_required=True)
    mdfe30_pesoR = fields.Monetary(
        digits=3, string="Peso Real em Toneladas",
        xsd_required=True)
    mdfe30_tpVag = fields.Char(
        string="Tipo de Vagão")
    mdfe30_serie = fields.Char(
        string="Serie de Identificação do vagão",
        xsd_required=True)
    mdfe30_nVag = fields.Char(
        string="Número de Identificação do vagão",
        xsd_required=True)
    mdfe30_nSeq = fields.Char(
        string="Sequencia do vagão na composição")
    mdfe30_TU = fields.Monetary(
        digits=3, string="Tonelada Útil", xsd_required=True)
