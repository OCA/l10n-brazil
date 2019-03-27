# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:47 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# A associação desportiva que mantém equipe de futebol profissional,
# possui informações sobre recursos recebidos?
evtAssDespRec_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não."),
]

# Possui informações sobre repasses efetuados à associação desportiva
# que
# mantém equipe de futebol profissional?
evtAssDespRep_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não."),
]

# Possui informações sobre a apuração da Contribuição Previdenciária
# sobre a Receita Bruta?
evtCPRB_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não"),
]

# O produtor rural PJ/Agroindústria possui informações de
# comercialização de produção?
evtComProd_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não."),
]

# Prestou serviços sujeitos à retenção de contribuição previdenciária?
evtServPr_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não."),
]

# Contratou serviços sujeitos à retenção de contribuição
# previdenciária?
evtServTm_infoFech = [
    ("S", "S - Sim"),
    ("N", "N - Não."),
]


class Reinf(spec_models.AbstractSpecMixin):
    "EFD-Reinf"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.reinf'
    _generateds_type = 'Reinf'
    _concrete_rec_name = 'efdreinf_evtFechaEvPer'

    efdreinf01_evtFechaEvPer = fields.Many2one(
        "efdreinf.01.evtfechaevper",
        string="evtFechaEvPer",
        xsd_required=True)


class EvtFechaEvPer(spec_models.AbstractSpecMixin):
    "Evento de informações do ContribuinteIdentificador do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtfechaevper'
    _generateds_type = 'evtFechaEvPerType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="ideContri", xsd_required=True)
    efdreinf01_ideRespInf = fields.Many2one(
        "efdreinf.01.iderespinf",
        string="ideRespInf")
    efdreinf01_infoFech = fields.Many2one(
        "efdreinf.01.infofech",
        string="infoFech", xsd_required=True)


class IdeContri(spec_models.AbstractSpecMixin):
    "Informações de identificação do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True,
        help="Informar o número de inscrição do contribuinte de acordo com"
        "\no tipo de inscrição indicado no campo {tpInsc}."
        "\nSe for um CNPJ deve ser informada apenas a Raiz/Base de oito"
        "\nposições,"
        "\nexceto se natureza jurídica de administração pública direta federal"
        "\n([101-5], [104-0], [107-4], [116-3],"
        "\nsituação em que o campo deve ser preenchido com o CNPJ completo (14"
        "\nposições).")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_perApur'

    efdreinf01_perApur = fields.Date(
        string="Informar o ano/mês",
        xsd_required=True,
        help="Informar o ano/mês (formato AAAA-MM) de referência das"
        "\ninformações")
    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_procEmi = fields.Integer(
        string="procEmi", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class IdeRespInf(spec_models.AbstractSpecMixin):
    "Responsável pelas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.iderespinf'
    _generateds_type = 'ideRespInfType'
    _concrete_rec_name = 'efdreinf_nmResp'

    efdreinf01_nmResp = fields.Char(
        string="nmResp", xsd_required=True)
    efdreinf01_cpfResp = fields.Char(
        string="Preencher com o CPF do responsável",
        xsd_required=True)
    efdreinf01_telefone = fields.Char(
        string="Informar o número do telefone",
        help="Informar o número do telefone, com DDD.")
    efdreinf01_email = fields.Char(
        string="Endereço eletrônico")


class InfoFech(spec_models.AbstractSpecMixin):
    "Responsável pelas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infofech'
    _generateds_type = 'infoFechType'
    _concrete_rec_name = 'efdreinf_evtServTm'

    efdreinf01_evtServTm = fields.Selection(
        evtServTm_infoFech,
        string="evtServTm", xsd_required=True,
        help="Contratou serviços sujeitos à retenção de contribuição"
        "\nprevidenciária?")
    efdreinf01_evtServPr = fields.Selection(
        evtServPr_infoFech,
        string="evtServPr", xsd_required=True,
        help="Prestou serviços sujeitos à retenção de contribuição"
        "\nprevidenciária?")
    efdreinf01_evtAssDespRec = fields.Selection(
        evtAssDespRec_infoFech,
        string="evtAssDespRec",
        xsd_required=True,
        help="A associação desportiva que mantém equipe de futebol"
        "\nprofissional,"
        "\npossui informações sobre recursos recebidos?")
    efdreinf01_evtAssDespRep = fields.Selection(
        evtAssDespRep_infoFech,
        string="evtAssDespRep",
        xsd_required=True,
        help="Possui informações sobre repasses efetuados à associação"
        "\ndesportiva que"
        "\nmantém equipe de futebol profissional?")
    efdreinf01_evtComProd = fields.Selection(
        evtComProd_infoFech,
        string="evtComProd",
        xsd_required=True,
        help="O produtor rural PJ/Agroindústria possui informações de"
        "\ncomercialização de produção?")
    efdreinf01_evtCPRB = fields.Selection(
        evtCPRB_infoFech,
        string="evtCPRB", xsd_required=True,
        help="Possui informações sobre a apuração da Contribuição"
        "\nPrevidenciária sobre a Receita Bruta?")
    efdreinf01_evtPgtos = fields.Char(
        string="evtPgtos")
    efdreinf01_compSemMovto = fields.Date(
        string="compSemMovto")
