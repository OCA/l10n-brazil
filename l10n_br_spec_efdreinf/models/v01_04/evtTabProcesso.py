# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:54 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtTabProcesso'

    efdreinf01_evtTabProcesso = fields.Many2one(
        "efdreinf.01.evttabprocesso",
        string="evtTabProcesso",
        xsd_required=True)


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração de informações já existentes"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'efdreinf_ideProcesso'

    efdreinf01_ideProcesso = fields.Many2one(
        "efdreinf.01.ideprocesso1",
        string="Grupo de informações de identificação do processo",
        xsd_required=True,
        help="Grupo de informações de identificação do processo,"
        "\napresentando número e período de"
        "\nvalidade do registro cujas informações serão alteradas pelos dados"
        "\nconstantes neste evento.")
    efdreinf01_novaValidade = fields.Many2one(
        "efdreinf.01.novavalidade",
        string="novaValidade")


class DadosProcJud(spec_models.AbstractSpecMixin):
    "Informações Complementares do Processo Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.dadosprocjud'
    _generateds_type = 'dadosProcJudType'
    _concrete_rec_name = 'efdreinf_ufVara'

    efdreinf01_ufVara = fields.Char(
        string="Identificação da Unidade da Federação",
        xsd_required=True,
        help="Identificação da Unidade da Federação-UF da Seção Judiciária")
    efdreinf01_codMunic = fields.Char(
        string="Código do município",
        xsd_required=True,
        help="Código do município, conforme tabela do IBGE")
    efdreinf01_idVara = fields.Char(
        string="Código de Identificação da Vara.",
        xsd_required=True)


class DadosProcJud12(spec_models.AbstractSpecMixin):
    "Informações Complementares do Processo Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.dadosprocjud12'
    _generateds_type = 'dadosProcJudType12'
    _concrete_rec_name = 'efdreinf_ufVara'

    efdreinf01_ufVara = fields.Char(
        string="Identificação da Unidade da Federação",
        xsd_required=True,
        help="Identificação da Unidade da Federação-UF da Seção Judiciária")
    efdreinf01_codMunic = fields.Char(
        string="Código do município",
        xsd_required=True,
        help="Código do município, conforme tabela do IBGE")
    efdreinf01_idVara = fields.Char(
        string="Código de Identificação da Vara.",
        xsd_required=True)


class EvtTabProcesso(spec_models.AbstractSpecMixin):
    "Identificação única do evento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evttabprocesso'
    _generateds_type = 'evtTabProcessoType'
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
    efdreinf01_infoProcesso = fields.Many2one(
        "efdreinf.01.infoprocesso",
        string="infoProcesso",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    _description = 'exclusao'
    _name = 'efdreinf.01.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'efdreinf_ideProcesso'

    efdreinf01_ideProcesso = fields.Many2one(
        "efdreinf.01.ideprocesso18",
        string="ideProcesso",
        xsd_required=True,
        help="Grupo de informações que identifica o processo que será"
        "\nexcluído.")


class IdeContri(spec_models.AbstractSpecMixin):
    _description = 'idecontri'
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True,
        help="Informar o número de inscrição do contribuinte de acordo com"
        "\no tipo de inscrição indicado no campo {tpInsc}."
        "\nSe for um CNPJ deve ser informada apenas a Raiz/Base de oito"
        "\nposições, exceto se natureza jurídica de"
        "\nadministração pública ([101-5], [104-0], [107-4], [116-3]),"
        "\nsituação em que o campo deve ser preenchido"
        "\ncom o CNPJ completo com 14 posições.")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_tpAmb'

    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="Versão do processo de emissão do evento",
        xsd_required=True,
        help="Versão do processo de emissão do evento. Informar a versão do"
        "\naplicativo emissor do evento")


class IdeProcesso(spec_models.AbstractSpecMixin):
    """Informações de identificação do Processo e validade das informações que
    estão sendo incluídas"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideprocesso'
    _generateds_type = 'ideProcessoType'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_iniValid = fields.Date(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
    efdreinf01_fimValid = fields.Date(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver. Formato AAAA-MM.")
    efdreinf01_infoSusp = fields.One2many(
        "efdreinf.01.infosusp",
        "efdreinf01_infoSusp_ideProcesso_id",
        string="Informações de Suspensão de Exigibilidade de tributos",
        xsd_required=True
    )
    efdreinf01_dadosProcJud = fields.Many2one(
        "efdreinf.01.dadosprocjud",
        string="Informações Complementares do Processo Judicial")


class IdeProcesso1(spec_models.AbstractSpecMixin):
    """Grupo de informações de identificação do processo, apresentando número e
    período de
    validade do registro cujas informações serão alteradas pelos dados
    constantes neste evento."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideprocesso1'
    _generateds_type = 'ideProcessoType1'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_iniValid = fields.Date(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
    efdreinf01_fimValid = fields.Date(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver. Formato AAAA-MM.")
    efdreinf01_infoSusp = fields.One2many(
        "efdreinf.01.infosusp7",
        "efdreinf01_infoSusp_ideProcesso1_id",
        string="Informações de Suspensão de Exigibilidade de tributos",
        xsd_required=True
    )
    efdreinf01_dadosProcJud = fields.Many2one(
        "efdreinf.01.dadosprocjud12",
        string="Informações Complementares do Processo Judicial")


class IdeProcesso18(spec_models.AbstractSpecMixin):
    "Grupo de informações que identifica o processo que será excluído."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideprocesso18'
    _generateds_type = 'ideProcessoType18'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_iniValid = fields.Date(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
    efdreinf01_fimValid = fields.Date(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver. Formato AAAA-MM.")


class Inclusao(spec_models.AbstractSpecMixin):
    _description = 'inclusao'
    _name = 'efdreinf.01.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'efdreinf_ideProcesso'

    efdreinf01_ideProcesso = fields.Many2one(
        "efdreinf.01.ideprocesso",
        string="ideProcesso",
        xsd_required=True,
        help="Informações de identificação do Processo e validade das"
        "\ninformações que estão sendo incluídas")


class InfoProcesso(spec_models.AbstractSpecMixin):
    _description = 'infoprocesso'
    _name = 'efdreinf.01.infoprocesso'
    _generateds_type = 'infoProcessoType'
    _concrete_rec_name = 'efdreinf_inclusao'

    efdreinf01_choice1 = fields.Selection([
        ('efdreinf01_inclusao', 'inclusao'),
        ('efdreinf01_alteracao', 'alteracao'),
        ('efdreinf01_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="efdreinf01_inclusao")
    efdreinf01_inclusao = fields.Many2one(
        "efdreinf.01.inclusao",
        choice='1',
        string="inclusao", xsd_required=True)
    efdreinf01_alteracao = fields.Many2one(
        "efdreinf.01.alteracao",
        choice='1',
        string="Alteração de informações já existentes",
        xsd_required=True,
        help="Alteração de informações já existentes")
    efdreinf01_exclusao = fields.Many2one(
        "efdreinf.01.exclusao",
        choice='1',
        string="exclusao", xsd_required=True)


class InfoSusp(spec_models.AbstractSpecMixin):
    "Informações de Suspensão de Exigibilidade de tributos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infosusp'
    _generateds_type = 'infoSuspType'
    _concrete_rec_name = 'efdreinf_codSusp'

    efdreinf01_infoSusp_ideProcesso_id = fields.Many2one(
        "efdreinf.01.ideprocesso")
    efdreinf01_codSusp = fields.Char(
        string="Código do Indicativo da Suspensão",
        help="Código do Indicativo da Suspensão, atribuído pelo"
        "\ncontribuinte."
        "\nEste campo deve ser utilizado se, num mesmo processo, houver mais"
        "\nde uma matéria"
        "\ntributária objeto de contestação e as decisões forem diferentes"
        "\npara cada uma.")
    efdreinf01_indSusp = fields.Char(
        string="Indicativo de suspensão da exigibilidade",
        xsd_required=True,
        help="Indicativo de suspensão da exigibilidade:"
        "\n01 - Liminar em Mandado de Segurança;"
        "\n02 - Depósito Judicial do Montante Integral"
        "\n03 - Depósito Administrativo do Montante Integral"
        "\n04 - Antecipação de Tutela;"
        "\n05 - Liminar em Medida Cautelar;"
        "\n08 - Sentença em Mandado de Segurança Favorável ao Contribuinte;"
        "\n09 - Sentença em Ação Ordinária Favorável ao Contribuinte e"
        "\nConfirmada pelo TRF;"
        "\n10 - Acórdão do TRF Favorável ao Contribuinte;"
        "\n11 - Acórdão do STJ em Recurso Especial Favorável ao Contribuinte;"
        "\n12 - Acórdão do STF em Recurso Extraordinário Favorável ao"
        "\nContribuinte;"
        "\n13 - Sentença 1ª instância não transitada em julgado com efeito"
        "\nsuspensivo;"
        "\n90 - Decisão Definitiva a favor do contribuinte (Transitada em"
        "\nJulgado);"
        "\n92 - Sem suspensão da exigibilidade")
    efdreinf01_dtDecisao = fields.Date(
        string="Data da decisão",
        xsd_required=True,
        help="Data da decisão, sentença ou despacho administrativo.")
    efdreinf01_indDeposito = fields.Char(
        string="Indicativo de Depósito do Montante Integral",
        xsd_required=True,
        help="Indicativo de Depósito do Montante Integral"
        "\nS - Sim;"
        "\nN - Não.")


class InfoSusp7(spec_models.AbstractSpecMixin):
    "Informações de Suspensão de Exigibilidade de tributos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infosusp7'
    _generateds_type = 'infoSuspType7'
    _concrete_rec_name = 'efdreinf_codSusp'

    efdreinf01_infoSusp_ideProcesso1_id = fields.Many2one(
        "efdreinf.01.ideprocesso1")
    efdreinf01_codSusp = fields.Char(
        string="Código do Indicativo da Suspensão",
        help="Código do Indicativo da Suspensão, atribuído pelo"
        "\ncontribuinte."
        "\nEste campo deve ser utilizado se, num mesmo processo, houver mais"
        "\nde uma matéria"
        "\ntributária objeto de contestação e as decisões forem diferentes"
        "\npara cada uma.")
    efdreinf01_indSusp = fields.Char(
        string="Indicativo de suspensão da exigibilidade",
        xsd_required=True,
        help="Indicativo de suspensão da exigibilidade:"
        "\n01 - Liminar em Mandado de Segurança;"
        "\n02 - Depósito Judicial do Montante Integral"
        "\n03 - Depósito Administrativo do Montante Integral"
        "\n04 - Antecipação de Tutela;"
        "\n05 - Liminar em Medida Cautelar;"
        "\n08 - Sentença em Mandado de Segurança Favorável ao Contribuinte;"
        "\n09 - Sentença em Ação Ordinária Favorável ao Contribuinte e"
        "\nConfirmada pelo TRF;"
        "\n10 - Acórdão do TRF Favorável ao Contribuinte;"
        "\n11 - Acórdão do STJ em Recurso Especial Favorável ao Contribuinte;"
        "\n12 - Acórdão do STF em Recurso Extraordinário Favorável ao"
        "\nContribuinte;"
        "\n13 - Sentença 1ª instância não transitada em julgado com efeito"
        "\nsuspensivo;"
        "\n90 - Decisão Definitiva a favor do contribuinte (Transitada em"
        "\nJulgado);"
        "\n92 - Sem suspensão da exigibilidade")
    efdreinf01_dtDecisao = fields.Date(
        string="Data da decisão",
        xsd_required=True,
        help="Data da decisão, sentença ou despacho administrativo.")
    efdreinf01_indDeposito = fields.Char(
        string="Indicativo de Depósito do Montante Integral",
        xsd_required=True,
        help="Indicativo de Depósito do Montante Integral"
        "\nS - Sim;"
        "\nN - Não.")


class NovaValidade(spec_models.AbstractSpecMixin):
    _description = 'novavalidade'
    _name = 'efdreinf.01.novavalidade'
    _generateds_type = 'novaValidadeType'
    _concrete_rec_name = 'efdreinf_iniValid'

    efdreinf01_iniValid = fields.Date(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
    efdreinf01_fimValid = fields.Date(
        string="fimValid",
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
