# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:46 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtEspDesportivo'

    efdreinf01_evtEspDesportivo = fields.Many2one(
        "efdreinf.01.evtespdesportivo",
        string="evtEspDesportivo",
        xsd_required=True)


class Boletim(spec_models.AbstractSpecMixin):
    "Boletim do Espetáculo Desportivo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.boletim'
    _generateds_type = 'boletimType'
    _concrete_rec_name = 'efdreinf_nrBoletim'

    efdreinf01_boletim_ideEstab_id = fields.Many2one(
        "efdreinf.01.ideestab")
    efdreinf01_nrBoletim = fields.Char(
        string="nrBoletim", xsd_required=True)
    efdreinf01_modDesportiva = fields.Char(
        string="Descrição da modalidade do evento desportivo",
        xsd_required=True)
    efdreinf01_nomeCompeticao = fields.Char(
        string="Nome da competição",
        xsd_required=True,
        help="Nome da competição. (Campeonato Brasileiro, Copa do Brasil,"
        "\nCampeonato Estadual, entre outras)")
    efdreinf01_cnpjMandante = fields.Char(
        string="Preencher com o CNPJ do clube mandante",
        xsd_required=True,
        help="Preencher com o CNPJ do clube mandante"
        "\nValidação: Deve ser um CNPJ válido")
    efdreinf01_cnpjVisitante = fields.Char(
        string="cnpjVisitante",
        help="Preencher com o número de inscrição do clube visitante no"
        "\nCNPJ. Não deve ser preenchido em caso de clube"
        "\nestrangeiro"
        "\nValidação: Se informado, deve ser um CNPJ válido")
    efdreinf01_nomeVisitante = fields.Char(
        string="Nome do clube visitante",
        help="Nome do clube visitante"
        "\nValidação: Preenchimento obrigatório se não preencher"
        "\n{cnpjVisitante}")
    efdreinf01_pracaDesportiva = fields.Char(
        string="Praça desportiva do local do evento",
        xsd_required=True,
        help="Praça desportiva do local do evento")
    efdreinf01_codMunic = fields.Integer(
        string="Preencher com o código do município",
        help="Preencher com o código do município, conforme tabela do IBGE"
        "\nValidação: Se informado, deve ser um código existente na tabela de"
        "\nmunicípios do IBGE")
    efdreinf01_uf = fields.Char(
        string="Preencher com a sigla da Unidade da Federação",
        xsd_required=True,
        help="Preencher com a sigla da Unidade da Federação"
        "\nValidação: Deve ser uma UF válida.")
    efdreinf01_qtdePagantes = fields.Integer(
        string="Quantidade de espectadores pagantes do evento",
        xsd_required=True)
    efdreinf01_qtdeNaoPagantes = fields.Integer(
        string="Quantidade de espectadores não pagantes do evento",
        xsd_required=True)
    efdreinf01_receitaIngressos = fields.One2many(
        "efdreinf.01.receitaingressos",
        "efdreinf01_receitaIngressos_boletim_id",
        string="Receita da Venda de Ingressos",
        xsd_required=True
    )
    efdreinf01_outrasReceitas = fields.One2many(
        "efdreinf.01.outrasreceitas",
        "efdreinf01_outrasReceitas_boletim_id",
        string="Outras receitas do espetáculo"
    )


class EvtEspDesportivo(spec_models.AbstractSpecMixin):
    """Evento Espetáculo Desportivo do qual participe ao menos uma equipe que
    mantenha equipe de futebol profissional.Identificação única do
    evento."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtespdesportivo'
    _generateds_type = 'evtEspDesportivoType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="ideContri", xsd_required=True,
        help="Informações de identificação da Entidade promotora do"
        "\nespetáculo desportivo")


class IdeContri(spec_models.AbstractSpecMixin):
    """Informações de identificação da Entidade promotora do espetáculo
    desportivo"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="Informar o CNPJ apenas com a Raiz/Base de oito posições",
        xsd_required=True,
        help="Informar o CNPJ apenas com a Raiz/Base de oito posições,"
        "\nexceto se natureza jurídica do declarante for de"
        "\nadministração pública direta federal ([101-5], [104-0], [107-4] e"
        "\n[116-3]), situação em que o campo deve"
        "\nser preenchido com o CNPJ completo com 14 posições.")
    efdreinf01_ideEstab = fields.Many2one(
        "efdreinf.01.ideestab",
        string="ideEstab", xsd_required=True,
        help="Registro que identifica o estabelecimento que comercializou a"
        "\nprodução")


class IdeEstab(spec_models.AbstractSpecMixin):
    """Registro que identifica o estabelecimento que comercializou a
    produção"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_nrInscEstab = fields.Char(
        string="nrInscEstab",
        xsd_required=True,
        help="Informar o número de inscrição do estabelecimento do"
        "\ncontribuinte declarante de acordo com o tipo de"
        "\ninscrição indicado no campo {tpInscEstab}."
        "\nValidação: A inscrição informada deve ser compatível com o"
        "\n{tpInscEstab} e válido.")
    efdreinf01_boletim = fields.One2many(
        "efdreinf.01.boletim",
        "efdreinf01_boletim_ideEstab_id",
        string="boletim", xsd_required=True
    )
    efdreinf01_receitaTotal = fields.Many2one(
        "efdreinf.01.receitatotal",
        string="Totalização da Receita",
        xsd_required=True)


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_indRetif'

    efdreinf01_nrRecibo = fields.Char(
        string="nrRecibo")
    efdreinf01_dtApuracao = fields.Date(
        string="dtApuracao",
        xsd_required=True)
    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class InfoProc(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a Suspensão da Contribuição
    previdenciária
    Validação: A soma dos valores informados no campo { vlrCPSusp } deste grupo
    deve
    ser igual a { vlrCPSuspTotal} do grupo {receitaTotal}."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoproc'
    _generateds_type = 'infoProcType'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_infoProc_receitaTotal_id = fields.Many2one(
        "efdreinf.01.receitatotal")
    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_codSusp = fields.Char(
        string="codSusp")
    efdreinf01_vlrCPSusp = fields.Char(
        string="vlrCPSusp", xsd_required=True)


class OutrasReceitas(spec_models.AbstractSpecMixin):
    "Outras receitas do espetáculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.outrasreceitas'
    _generateds_type = 'outrasReceitasType'
    _concrete_rec_name = 'efdreinf_tpReceita'

    efdreinf01_outrasReceitas_boletim_id = fields.Many2one(
        "efdreinf.01.boletim")
    efdreinf01_vlrReceita = fields.Char(
        string="vlrReceita",
        xsd_required=True)
    efdreinf01_descReceita = fields.Char(
        string="Descrição da receita",
        xsd_required=True)


class ReceitaIngressos(spec_models.AbstractSpecMixin):
    "Receita da Venda de Ingressos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.receitaingressos'
    _generateds_type = 'receitaIngressosType'
    _concrete_rec_name = 'efdreinf_tpIngresso'

    efdreinf01_receitaIngressos_boletim_id = fields.Many2one(
        "efdreinf.01.boletim")
    efdreinf01_descIngr = fields.Char(
        string="Descrição do tipo de ingresso",
        xsd_required=True)
    efdreinf01_qtdeIngrVenda = fields.Integer(
        string="Número de ingressos colocados à venda",
        xsd_required=True)
    efdreinf01_qtdeIngrVendidos = fields.Integer(
        string="Número de ingressos vendidos",
        xsd_required=True,
        help="Número de ingressos vendidos"
        "\nValidação: Não pode ser superior ao valor informado em"
        "\n{qtdeIngrVenda}")
    efdreinf01_qtdeIngrDev = fields.Integer(
        string="Número de ingressos devolvidos",
        xsd_required=True,
        help="Número de ingressos devolvidos"
        "\nValidação: Não pode ser superior ao valor informado em"
        "\n{qtdeIngrVenda}")
    efdreinf01_precoIndiv = fields.Char(
        string="precoIndiv",
        xsd_required=True)
    efdreinf01_vlrTotal = fields.Char(
        string="vlrTotal", xsd_required=True)


class ReceitaTotal(spec_models.AbstractSpecMixin):
    "Totalização da Receita"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.receitatotal'
    _generateds_type = 'receitaTotalType'
    _concrete_rec_name = 'efdreinf_vlrReceitaTotal'

    efdreinf01_vlrReceitaTotal = fields.Char(
        string="vlrReceitaTotal",
        xsd_required=True)
    efdreinf01_vlrCP = fields.Char(
        string="vlrCP", xsd_required=True)
    efdreinf01_vlrCPSuspTotal = fields.Char(
        string="vlrCPSuspTotal")
    efdreinf01_vlrReceitaClubes = fields.Char(
        string="vlrReceitaClubes",
        xsd_required=True)
    efdreinf01_vlrRetParc = fields.Char(
        string="vlrRetParc",
        xsd_required=True)
    efdreinf01_infoProc = fields.One2many(
        "efdreinf.01.infoproc",
        "efdreinf01_infoProc_receitaTotal_id",
        string="infoProc",
        help="Informações de processos relacionados a Suspensão da"
        "\nContribuição previdenciária"
        "\nValidação: A soma dos valores informados no campo { vlrCPSusp }"
        "\ndeste grupo deve"
        "\nser igual a { vlrCPSuspTotal} do grupo {receitaTotal}."
    )
