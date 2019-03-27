# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:51 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtServPrest'

    efdreinf01_evtServPrest = fields.Many2one(
        "efdreinf.01.evtservprest",
        string="evtServPrest",
        xsd_required=True)


class EvtServPrest(spec_models.AbstractSpecMixin):
    """Evento Serviços Prestados (Cessão de Mão de Obra ou
    Empreitada)Identificação única do evento."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtservprest'
    _generateds_type = 'evtServPrestType'
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
    efdreinf01_infoServPrest = fields.Many2one(
        "efdreinf.01.infoservprest",
        string="infoServPrest",
        xsd_required=True)


class IdeContri(spec_models.AbstractSpecMixin):
    "Informações de identificação do contribuinte"
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


class IdeEstabPrest(spec_models.AbstractSpecMixin):
    """Registro que identifica o estabelecimento "prestador" de serviços
    mediante cessão de mão de obra."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestabprest'
    _generateds_type = 'ideEstabPrestType'
    _concrete_rec_name = 'efdreinf_tpInscEstabPrest'

    efdreinf01_tpInscEstabPrest = fields.Integer(
        string="tpInscEstabPrest",
        xsd_required=True)
    efdreinf01_nrInscEstabPrest = fields.Char(
        string="nrInscEstabPrest",
        xsd_required=True,
        help="Informar o número de inscrição do contribuinte de acordo com"
        "\no tipo de inscrição indicado no campo"
        "\n{tpInscEstabPrest}")
    efdreinf01_ideTomador = fields.Many2one(
        "efdreinf.01.idetomador",
        string="ideTomador",
        xsd_required=True)


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
    efdreinf01_procEmi = fields.Integer(
        string="procEmi", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class IdeTomador(spec_models.AbstractSpecMixin):
    "Identificação dos tomadores dos serviços"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idetomador'
    _generateds_type = 'ideTomadorType'
    _concrete_rec_name = 'efdreinf_tpInscTomador'

    efdreinf01_nrInscTomador = fields.Char(
        string="Indicar o número de inscrição do tomador",
        xsd_required=True,
        help="Indicar o número de inscrição do tomador, conforme indicado"
        "\nno campo {tpInscTomador}")
    efdreinf01_vlrTotalBruto = fields.Char(
        string="Preencher com o valor bruto da(s) nota(s) fiscal(is)",
        xsd_required=True)
    efdreinf01_vlrTotalBaseRet = fields.Char(
        string="vlrTotalBaseRet",
        xsd_required=True,
        help="Preencher com a soma da base de cálculo da retenção da"
        "\ncontribuição previdenciária das notas fiscais"
        "\nemitidas para o contratante")
    efdreinf01_vlrTotalRetPrinc = fields.Char(
        string="vlrTotalRetPrinc",
        xsd_required=True,
        help="Soma do valor da retenção das notas fiscais de serviço"
        "\nemitidas para o contratante")
    efdreinf01_vlrTotalRetAdic = fields.Char(
        string="Soma do valor do adicional de retenção das notas fiscais")
    efdreinf01_vlrTotalNRetPrinc = fields.Char(
        string="vlrTotalNRetPrinc",
        help="Valor da retenção principal que deixou de ser efetuada pelo"
        "\ncontratante ou que foi depositada"
        "\nem juízo em decorrência da decisão judicial")
    efdreinf01_vlrTotalNRetAdic = fields.Char(
        string="vlrTotalNRetAdic",
        help="Valor da retenção adicional que deixou de ser efetuada pelo"
        "\ncontratante ou que foi depositada"
        "\nem juízo em decorrência da decisão judicial")
    efdreinf01_nfs = fields.One2many(
        "efdreinf.01.nfs",
        "efdreinf01_nfs_ideTomador_id",
        string="nfs", xsd_required=True
    )
    efdreinf01_infoProcRetPr = fields.One2many(
        "efdreinf.01.infoprocretpr",
        "efdreinf01_infoProcRetPr_ideTomador_id",
        string="infoProcRetPr"
    )
    efdreinf01_infoProcRetAd = fields.One2many(
        "efdreinf.01.infoprocretad",
        "efdreinf01_infoProcRetAd_ideTomador_id",
        string="infoProcRetAd"
    )


class InfoProcRetAd(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a não retenção de contribuição
    previdenciária adicional
    Validação: A soma dos valores informados no campo {valorAdic} deste grupo
    deve ser igual a {vlrTotalNRetAdic}."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoprocretad'
    _generateds_type = 'infoProcRetAdType'
    _concrete_rec_name = 'efdreinf_tpProcRetAdic'

    efdreinf01_infoProcRetAd_ideTomador_id = fields.Many2one(
        "efdreinf.01.idetomador")
    efdreinf01_nrProcRetAdic = fields.Char(
        string="Informar o número do processo administrativo/judicial",
        xsd_required=True)
    efdreinf01_codSuspAdic = fields.Char(
        string="Código do Indicativo da Suspensão",
        help="Código do Indicativo da Suspensão, atribuído pelo"
        "\ncontribuinte. Este campo deve ser utilizado se,"
        "\nnum mesmo processo, houver mais de uma matéria tributária objeto de"
        "\ncontestação e as decisões forem diferentes para cada uma.")
    efdreinf01_valorAdic = fields.Char(
        string="valorAdic", xsd_required=True)


class InfoProcRetPr(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a não retenção de contribuição
    previdenciária"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoprocretpr'
    _generateds_type = 'infoProcRetPrType'
    _concrete_rec_name = 'efdreinf_tpProcRetPrinc'

    efdreinf01_infoProcRetPr_ideTomador_id = fields.Many2one(
        "efdreinf.01.idetomador")
    efdreinf01_nrProcRetPrinc = fields.Char(
        string="Informar o número do processo administrativo/judicial",
        xsd_required=True)
    efdreinf01_codSuspPrinc = fields.Char(
        string="Código do Indicativo da Suspensão",
        help="Código do Indicativo da Suspensão, atribuído pelo"
        "\ncontribuinte."
        "\nEste campo deve ser utilizado se, num mesmo processo, houver mais"
        "\nde uma matéria tributária"
        "\nobjeto de contestação e as decisões forem diferentes para cada uma.")
    efdreinf01_valorPrinc = fields.Char(
        string="valorPrinc",
        xsd_required=True)


class InfoServPrest(spec_models.AbstractSpecMixin):
    """Informação dos Serviços Prestados (Cessão de Mão de Obra ou
    Empreitada)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoservprest'
    _generateds_type = 'infoServPrestType'
    _concrete_rec_name = 'efdreinf_ideEstabPrest'

    efdreinf01_ideEstabPrest = fields.Many2one(
        "efdreinf.01.ideestabprest",
        string="ideEstabPrest",
        xsd_required=True)


class InfoTpServ(spec_models.AbstractSpecMixin):
    "Informações sobre os tipos de Serviços constantes da Nota Fiscal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infotpserv'
    _generateds_type = 'infoTpServType'
    _concrete_rec_name = 'efdreinf_tpServico'

    efdreinf01_infoTpServ_nfs_id = fields.Many2one(
        "efdreinf.01.nfs")
    efdreinf01_tpServico = fields.Char(
        string="Informar o tipo de serviço",
        xsd_required=True,
        help="Informar o tipo de serviço, conforme tabela 6.")
    efdreinf01_vlrBaseRet = fields.Char(
        string="Base de cálculo da retenção da contribuição previdenciária",
        xsd_required=True)
    efdreinf01_vlrRetencao = fields.Char(
        string="vlrRetencao",
        xsd_required=True,
        help="Preencher com o valor da retenção apurada de acordo com o que"
        "\ndetermina a legislação vigente"
        "\nrelativa aos serviços contidos na nota fiscal/fatura."
        "\nValidação: Não pode ser maior que 11% de {vlrBaseRet}.")
    efdreinf01_vlrRetSub = fields.Char(
        string="vlrRetSub",
        help="Informar o valor da retenção destacada na(s) nota"
        "\nfiscal(ais), relativo aos serviços subcontratados, se"
        "\nhouver,"
        "\nque irá deduzir a retenção apurada no mês, desde que todos os"
        "\ndocumentos envolvidos se refiram à mesma competência"
        "\ne ao mesmo serviço, conforme disciplina a legislação.")
    efdreinf01_vlrNRetPrinc = fields.Char(
        string="vlrNRetPrinc",
        help="Valor da retenção principal que deixou de ser efetuada pelo"
        "\ncontratante ou que foi depositada em juízo"
        "\nem decorrência de decisão judicial/administrativa."
        "\nValidação: Não pode ser maior que {vlrRetencao}")
    efdreinf01_vlrServicos15 = fields.Char(
        string="vlrServicos15",
        help="Valor dos Serviços prestados por segurados em condições"
        "\nespeciais, cuja atividade permita"
        "\nconcessão de aposentadoria especial após 15 anos de contribuição")
    efdreinf01_vlrServicos20 = fields.Char(
        string="vlrServicos20",
        help="Valor dos Serviços prestados por segurados em condições"
        "\nespeciais, cuja atividade permita"
        "\nconcessão de aposentadoria especial após 20 anos de contribuição")
    efdreinf01_vlrServicos25 = fields.Char(
        string="vlrServicos25",
        help="Valor dos Serviços prestados por segurados em condições"
        "\nespeciais, cuja atividade permita"
        "\nconcessão de aposentadoria especial após 25 anos de contribuição")
    efdreinf01_vlrAdicional = fields.Char(
        string="Adicional apurado de retenção da nota fiscal",
        help="Adicional apurado de retenção da nota fiscal, caso os"
        "\nserviços tenham sido prestados sob condições"
        "\nespeciais que ensejem aposentadoria especial aos trabalhadores após"
        "\n15, 20, ou 25 anos de contribuição.")
    efdreinf01_vlrNRetAdic = fields.Char(
        string="vlrNRetAdic",
        help="Valor da retenção adicional que deixou de ser efetuada pelo"
        "\ncontratante ou que foi depositada em juízo"
        "\nem decorrência de decisão judicial/administrativa."
        "\nValidação: Não pode ser maior que {vlrAdicional}")


class Nfs(spec_models.AbstractSpecMixin):
    "Notas Fiscais do Prestador de Serviços"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.nfs'
    _generateds_type = 'nfsType'
    _concrete_rec_name = 'efdreinf_serie'

    efdreinf01_nfs_ideTomador_id = fields.Many2one(
        "efdreinf.01.idetomador")
    efdreinf01_serie = fields.Char(
        string="serie", xsd_required=True,
        help="Informar o número de série da nota fiscal/fatura ou do Recibo"
        "\nProvisório de Serviço - RPS ou de outro documento"
        "\nfiscal válido. Preencher com 0 (zero) caso não exista"
        "\nnúmero de série.")
    efdreinf01_numDocto = fields.Char(
        string="numDocto", xsd_required=True,
        help="Número da Nota Fiscal/Fatura ou outro documento fiscal"
        "\nválido, como Recibo Provisório de Serviço - RPS, CT-e"
        "\nOS, entre outros.")
    efdreinf01_dtEmissaoNF = fields.Date(
        string="dtEmissaoNF",
        xsd_required=True,
        help="Data de Emissão da Nota Fiscal/Fatura ou do Recibo Provisório"
        "\nde Serviço - RPS ou de outro documento fiscal válido."
        "\nValidação: O mês/ano informado deve ser igual ao mês/ano indicado"
        "\nno registro de abertura do arquivo.")
    efdreinf01_vlrBruto = fields.Char(
        string="vlrBruto", xsd_required=True,
        help="Preencher com o valor bruto da nota fiscal ou do Recibo"
        "\nProvisório de Serviço - RPS ou de outro documento"
        "\nfiscal válido.")
    efdreinf01_obs = fields.Char(
        string="Observações")
    efdreinf01_infoTpServ = fields.One2many(
        "efdreinf.01.infotpserv",
        "efdreinf01_infoTpServ_nfs_id",
        string="infoTpServ",
        xsd_required=True
    )
