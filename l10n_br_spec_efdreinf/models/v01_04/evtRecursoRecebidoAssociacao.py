# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:52 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtAssocDespRec'

    efdreinf01_evtAssocDespRec = fields.Many2one(
        "efdreinf.01.evtassocdesprec",
        string="evtAssocDespRec",
        xsd_required=True)


class EvtAssocDespRec(spec_models.AbstractSpecMixin):
    """Evento Recursos Recebidos por Associação Desportiva que mantenha equipe
    de Futebol profissionalIdentificação Única do Evento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtassocdesprec'
    _generateds_type = 'evtAssocDespRecType'
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
        string="nrInsc", xsd_required=True,
        help="Informar o CNPJ com Raiz/Base de oito posições ou com catorze"
        "\nposições.")
    efdreinf01_ideEstab = fields.Many2one(
        "efdreinf.01.ideestab",
        string="ideEstab", xsd_required=True,
        help="Identificação dos estabelecimentos da associação desportiva"
        "\nque receberam os recursos.")


class IdeEstab(spec_models.AbstractSpecMixin):
    """Identificação dos estabelecimentos da associação desportiva que
    receberam os recursos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_nrInscEstab = fields.Char(
        string="nrInscEstab",
        xsd_required=True,
        help="Informar o número de inscrição do estabelecimento de acordo"
        "\ncom o tipo de inscrição indicado no campo"
        "\n{tpInscEstab}")
    efdreinf01_recursosRec = fields.One2many(
        "efdreinf.01.recursosrec",
        "efdreinf01_recursosRec_ideEstab_id",
        string="recursosRec",
        xsd_required=True,
        help="Registro preenchido exclusivamente por associação desportiva"
        "\nque mantenha equipe de futebol profissional,"
        "\nquando receber repasse de outras empresas a título de patrocínio,"
        "\npublicidade, licenciamento, etc ."
        "\nTotalizador dos recursos recebidos por estabelecimento"
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

    efdreinf01_infoProc_recursosRec_id = fields.Many2one(
        "efdreinf.01.recursosrec")
    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_codSusp = fields.Char(
        string="codSusp")
    efdreinf01_vlrNRet = fields.Char(
        string="vlrNRet", xsd_required=True)


class InfoRecurso(spec_models.AbstractSpecMixin):
    "Detalhamento dos recursos recebidos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.inforecurso'
    _generateds_type = 'infoRecursoType'
    _concrete_rec_name = 'efdreinf_tpRepasse'

    efdreinf01_infoRecurso_recursosRec_id = fields.Many2one(
        "efdreinf.01.recursosrec")
    efdreinf01_descRecurso = fields.Char(
        string="descRecurso",
        xsd_required=True)
    efdreinf01_vlrBruto = fields.Char(
        string="vlrBruto", xsd_required=True)
    efdreinf01_vlrRetApur = fields.Char(
        string="vlrRetApur",
        xsd_required=True)


class RecursosRec(spec_models.AbstractSpecMixin):
    """Registro preenchido exclusivamente por associação desportiva que
    mantenha equipe de futebol profissional,
    quando receber repasse de outras empresas a título de patrocínio,
    publicidade, licenciamento, etc .
    Totalizador dos recursos recebidos por estabelecimento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.recursosrec'
    _generateds_type = 'recursosRecType'
    _concrete_rec_name = 'efdreinf_cnpjOrigRecurso'

    efdreinf01_recursosRec_ideEstab_id = fields.Many2one(
        "efdreinf.01.ideestab")
    efdreinf01_cnpjOrigRecurso = fields.Char(
        string="cnpjOrigRecurso",
        xsd_required=True)
    efdreinf01_vlrTotalRec = fields.Char(
        string="vlrTotalRec",
        xsd_required=True)
    efdreinf01_vlrTotalRet = fields.Char(
        string="vlrTotalRet",
        xsd_required=True)
    efdreinf01_vlrTotalNRet = fields.Char(
        string="vlrTotalNRet")
    efdreinf01_infoRecurso = fields.One2many(
        "efdreinf.01.inforecurso",
        "efdreinf01_infoRecurso_recursosRec_id",
        string="Detalhamento dos recursos recebidos",
        xsd_required=True,
        help="Detalhamento dos recursos recebidos"
    )
    efdreinf01_infoProc = fields.One2many(
        "efdreinf.01.infoproc",
        "efdreinf01_infoProc_recursosRec_id",
        string="infoProc",
        help="Informações de processos relacionados a não retenção de"
        "\ncontribuição previdenciária."
    )
