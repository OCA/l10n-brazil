# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:53 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtAssocDespRep'

    efdreinf01_evtAssocDespRep = fields.Many2one(
        "efdreinf.01.evtassocdesprep",
        string="evtAssocDespRep",
        xsd_required=True)


class EvtAssocDespRep(spec_models.AbstractSpecMixin):
    """Evento Recursos Repassados para Associação Desportiva que mantenha
    equipe de futebol profissional.Identificação Única do Evento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtassocdesprep'
    _generateds_type = 'evtAssocDespRepType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="Informações de identificação do contribuinte",
        xsd_required=True)


class IdeContri(spec_models.AbstractSpecMixin):
    "Informações de identificação do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="Informar o CNPJ do contribuinte.",
        xsd_required=True)
    efdreinf01_ideEstab = fields.Many2one(
        "efdreinf.01.ideestab",
        string="ideEstab", xsd_required=True,
        help="Identificação do estabelecimento que efetuou o repasse de"
        "\nrecursos a Associação Desportiva que mantém equipe de"
        "\nfutebol profissional")


class IdeEstab(spec_models.AbstractSpecMixin):
    """Identificação do estabelecimento que efetuou o repasse de recursos a
    Associação Desportiva que mantém equipe de futebol profissional"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_nrInscEstab = fields.Char(
        string="Informar o CNPJ do contribuinte.",
        xsd_required=True)
    efdreinf01_recursosRep = fields.One2many(
        "efdreinf.01.recursosrep",
        "efdreinf01_recursosRep_ideEstab_id",
        string="recursosRep",
        xsd_required=True,
        help="Detalhamento dos repasses efetuados pelo estabelecimento"
        "\nindicado em {ideEstab} à Associação Desportiva que"
        "\nmantenha equipe de futebol profissional"
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_indRetif'

    efdreinf01_nrRecibo = fields.Char(
        string="nrRecibo")
    efdreinf01_perApur = fields.Date(
        string="Informar o ano/mês",
        xsd_required=True,
        help="Informar o ano/mês (formato AAAA-MM) de referência das"
        "\ninformações")
    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class InfoProc(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a não retenção de contribuição
    previdenciária."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoproc'
    _generateds_type = 'infoProcType'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_infoProc_recursosRep_id = fields.Many2one(
        "efdreinf.01.recursosrep")
    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_codSusp = fields.Char(
        string="codSusp")
    efdreinf01_vlrNRet = fields.Char(
        string="vlrNRet", xsd_required=True)


class InfoRecurso(spec_models.AbstractSpecMixin):
    """Detalhamento dos recursos repassados à associação desportiva que mantém
    equipe de futebol profissional"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.inforecurso'
    _generateds_type = 'infoRecursoType'
    _concrete_rec_name = 'efdreinf_tpRepasse'

    efdreinf01_infoRecurso_recursosRep_id = fields.Many2one(
        "efdreinf.01.recursosrep")
    efdreinf01_tpRepasse = fields.Char(
        string="tpRepasse", xsd_required=True)
    efdreinf01_descRecurso = fields.Char(
        string="descRecurso",
        xsd_required=True)
    efdreinf01_vlrBruto = fields.Char(
        string="vlrBruto", xsd_required=True)
    efdreinf01_vlrRetApur = fields.Char(
        string="vlrRetApur",
        xsd_required=True)


class RecursosRep(spec_models.AbstractSpecMixin):
    """Detalhamento dos repasses efetuados pelo estabelecimento indicado em
    {ideEstab} à Associação Desportiva que mantenha equipe de futebol
    profissional"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.recursosrep'
    _generateds_type = 'recursosRepType'
    _concrete_rec_name = 'efdreinf_cnpjAssocDesp'

    efdreinf01_recursosRep_ideEstab_id = fields.Many2one(
        "efdreinf.01.ideestab")
    efdreinf01_cnpjAssocDesp = fields.Char(
        string="cnpjAssocDesp",
        xsd_required=True)
    efdreinf01_vlrTotalRep = fields.Char(
        string="vlrTotalRep",
        xsd_required=True)
    efdreinf01_vlrTotalRet = fields.Char(
        string="vlrTotalRet",
        xsd_required=True)
    efdreinf01_vlrTotalNRet = fields.Char(
        string="vlrTotalNRet")
    efdreinf01_infoRecurso = fields.One2many(
        "efdreinf.01.inforecurso",
        "efdreinf01_infoRecurso_recursosRep_id",
        string="infoRecurso",
        xsd_required=True,
        help="Detalhamento dos recursos repassados à associação desportiva"
        "\nque mantém equipe de futebol profissional"
    )
    efdreinf01_infoProc = fields.One2many(
        "efdreinf.01.infoproc",
        "efdreinf01_infoProc_recursosRep_id",
        string="infoProc",
        help="Informações de processos relacionados a não retenção de"
        "\ncontribuição previdenciária."
    )
