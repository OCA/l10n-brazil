# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:47 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class Reinf(spec_models.AbstractSpecMixin):
    "EFD-Reinf"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.reinf'
    _generateds_type = 'Reinf'
    _concrete_rec_name = 'efdreinf_evtExclusao'

    efdreinf01_evtExclusao = fields.Many2one(
        "efdreinf.01.evtexclusao",
        string="evtExclusao",
        xsd_required=True)


class EvtExclusao(spec_models.AbstractSpecMixin):
    """Evento destinado a exclusão de eventosIdentificação única do evento."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtexclusao'
    _generateds_type = 'evtExclusaoType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="ideContri", xsd_required=True)
    efdreinf01_infoExclusao = fields.Many2one(
        "efdreinf.01.infoexclusao",
        string="infoExclusao",
        xsd_required=True)


class IdeContri(spec_models.AbstractSpecMixin):
    "Informações de identificação do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True,
        help="Informar o número de inscrição do contribuinte de acordo com"
        "\no tipo de inscrição indicado no campo {tpInsc}.Se for"
        "\num CNPJ deve ser informada apenas a Raiz/Base de oito"
        "\nposições, exceto se natureza jurídica de"
        "\nadministração pública direta federal ([101-5],"
        "\n[104-0], [107-4], [116-3], situação em que o campo"
        "\ndeve ser preenchido com o CNPJ completo (14"
        "\nposições).")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de Identificação do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_tpAmb'

    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class InfoExclusao(spec_models.AbstractSpecMixin):
    "Registro que identifica o evento objeto da exclusão"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoexclusao'
    _generateds_type = 'infoExclusaoType'
    _concrete_rec_name = 'efdreinf_tpEvento'

    efdreinf01_tpEvento = fields.Char(
        string="tpEvento", xsd_required=True)
    efdreinf01_nrRecEvt = fields.Char(
        string="nrRecEvt", xsd_required=True)
    efdreinf01_perApur = fields.Date(
        string="perApur", xsd_required=True)
