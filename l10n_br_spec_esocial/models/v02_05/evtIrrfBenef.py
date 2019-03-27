# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:37 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtirrfbene.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TNaoResid(spec_models.AbstractSpecMixin):
    "Endereço no Exterior - Fiscal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.tnaoresid'
    _generateds_type = 'TNaoResid'
    _concrete_rec_name = 'esoc_idePais'

    esoc02_idePais = fields.Many2one(
        "esoc.02.evtirrfbene.idepais",
        string="Identificação do País onde foi efetuado o pagamento",
        xsd_required=True)
    esoc02_endExt = fields.Many2one(
        "esoc.02.evtirrfbene.endext",
        string="Informações complementares de endereço do beneficiário",
        xsd_required=True)


class BasesIrrf(spec_models.AbstractSpecMixin):
    "Bases do IRRF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.basesirrf'
    _generateds_type = 'basesIrrfType'
    _concrete_rec_name = 'esoc_tpValor'

    esoc02_basesIrrf_infoIrrf_id = fields.Many2one(
        "esoc.02.evtirrfbene.infoirrf")
    esoc02_tpValor = fields.Boolean(
        string="tpValor", xsd_required=True)
    esoc02_valor = fields.Monetary(
        string="valor", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtirrfbene.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtIrrfBenef'

    esoc02_evtIrrfBenef = fields.Many2one(
        "esoc.02.evtirrfbene.evtirrfbenef",
        string="evtIrrfBenef",
        xsd_required=True)


class EndExt(spec_models.AbstractSpecMixin):
    "Informações complementares de endereço do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.endext'
    _generateds_type = 'endExtType'
    _concrete_rec_name = 'esoc_dscLograd'

    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd")
    esoc02_complem = fields.Char(
        string="complem")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_nmCid = fields.Char(
        string="nmCid", xsd_required=True)
    esoc02_codPostal = fields.Char(
        string="codPostal")


class EvtIrrfBenef(spec_models.AbstractSpecMixin):
    "IRRF do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.evtirrfbenef'
    _generateds_type = 'evtIrrfBenefType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtirrfbene.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtirrfbene.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtirrfbene.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_infoDep = fields.Many2one(
        "esoc.02.evtirrfbene.infodep",
        string="Informações relativas a existência de dependentes")
    esoc02_infoIrrf = fields.One2many(
        "esoc.02.evtirrfbene.infoirrf",
        "esoc02_infoIrrf_evtIrrfBenef_id",
        string="Informações relativas ao IRRF",
        xsd_required=True
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class IdePais(spec_models.AbstractSpecMixin):
    "Identificação do País onde foi efetuado o pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.idepais'
    _generateds_type = 'idePaisType'
    _concrete_rec_name = 'esoc_codPais'

    esoc02_codPais = fields.Char(
        string="codPais", xsd_required=True)
    esoc02_indNIF = fields.Boolean(
        string="indNIF", xsd_required=True)
    esoc02_nifBenef = fields.Char(
        string="nifBenef")


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)


class InfoDep(spec_models.AbstractSpecMixin):
    "Informações relativas a existência de dependentes"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.infodep'
    _generateds_type = 'infoDepType'
    _concrete_rec_name = 'esoc_vrDedDep'

    esoc02_vrDedDep = fields.Monetary(
        string="vrDedDep", xsd_required=True)


class InfoIrrf(spec_models.AbstractSpecMixin):
    "Informações relativas ao IRRF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.infoirrf'
    _generateds_type = 'infoIrrfType'
    _concrete_rec_name = 'esoc_codCateg'

    esoc02_infoIrrf_evtIrrfBenef_id = fields.Many2one(
        "esoc.02.evtirrfbene.evtirrfbenef")
    esoc02_codCateg = fields.Integer(
        string="codCateg")
    esoc02_indResBr = fields.Char(
        string="indResBr", xsd_required=True)
    esoc02_basesIrrf = fields.One2many(
        "esoc.02.evtirrfbene.basesirrf",
        "esoc02_basesIrrf_infoIrrf_id",
        string="Bases do IRRF", xsd_required=True
    )
    esoc02_irrf = fields.One2many(
        "esoc.02.evtirrfbene.irrf",
        "esoc02_irrf_infoIrrf_id",
        string="Informações relativas ao IRRF"
    )
    esoc02_idePgtoExt = fields.Many2one(
        "esoc.02.evtirrfbene.tnaoresid",
        string="idePgtoExt",
        help="Informações complementares sobre pagamentos a residente"
        "\nfiscal no exterior")


class Irrf(spec_models.AbstractSpecMixin):
    "Informações relativas ao IRRF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrfbene.irrf'
    _generateds_type = 'irrfType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_irrf_infoIrrf_id = fields.Many2one(
        "esoc.02.evtirrfbene.infoirrf")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrIrrfDesc = fields.Monetary(
        string="vrIrrfDesc", xsd_required=True)
