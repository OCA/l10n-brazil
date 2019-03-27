# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:48 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtInfoContri'

    efdreinf01_evtInfoContri = fields.Many2one(
        "efdreinf.01.evtinfocontri",
        string="evtInfoContri",
        xsd_required=True)


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'efdreinf_idePeriodo'

    efdreinf01_idePeriodo = fields.Many2one(
        "efdreinf.01.ideperiodo2",
        string="Período de validade das informações alteradas",
        xsd_required=True)
    efdreinf01_infoCadastro = fields.Many2one(
        "efdreinf.01.infocadastro5",
        string="Informações do contribuinte",
        xsd_required=True)
    efdreinf01_novaValidade = fields.Many2one(
        "efdreinf.01.novavalidade",
        string="Novo período de validade das informações")


class Contato(spec_models.AbstractSpecMixin):
    "Informações de contato"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.contato'
    _generateds_type = 'contatoType'
    _concrete_rec_name = 'efdreinf_nmCtt'

    efdreinf01_nmCtt = fields.Char(
        string="Nome do contato na empresa",
        xsd_required=True,
        help="Nome do contato na empresa. Pessoa responsável por ser o"
        "\ncontato do contribuinte com a Receita Federal do"
        "\nBrasil relativamente à EFD-Reinf.")
    efdreinf01_cpfCtt = fields.Char(
        string="Preencher com o número do CPF do contato",
        xsd_required=True)
    efdreinf01_foneFixo = fields.Char(
        string="Informar o número do telefone",
        help="Informar o número do telefone, com DDD.")
    efdreinf01_foneCel = fields.Char(
        string="Telefone celular, com DDD.")
    efdreinf01_email = fields.Char(
        string="Endereço eletrônico.")


class Contato11(spec_models.AbstractSpecMixin):
    "Informações de contato"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.contato11'
    _generateds_type = 'contatoType11'
    _concrete_rec_name = 'efdreinf_nmCtt'

    efdreinf01_nmCtt = fields.Char(
        string="Nome do contato no contribuinte",
        xsd_required=True,
        help="Nome do contato no contribuinte. Pessoa responsável por ser o"
        "\ncontato do contribuinte com a Receita Federal do"
        "\nBrasil relativamente à EFD-Reinf.")
    efdreinf01_cpfCtt = fields.Char(
        string="Número do CPF do contato.",
        xsd_required=True)
    efdreinf01_foneFixo = fields.Char(
        string="Informar o número do telefone",
        help="Informar o número do telefone, com DDD.")
    efdreinf01_foneCel = fields.Char(
        string="Informar o número do telefone celular",
        help="Informar o número do telefone celular, com DDD.")
    efdreinf01_email = fields.Char(
        string="Endereço eletrônico do contato.")


class EvtInfoContri(spec_models.AbstractSpecMixin):
    "Evento de informações do ContribuinteIdentificador do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtinfocontri'
    _generateds_type = 'evtInfoContriType'
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
    efdreinf01_infoContri = fields.Many2one(
        "efdreinf.01.infocontri",
        string="Informações do contribuinte",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'efdreinf_idePeriodo'

    efdreinf01_idePeriodo = fields.Many2one(
        "efdreinf.01.ideperiodo28",
        string="Período de validade das informações excluídas",
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
        "\no tipo de inscrição indicado no campo {tpInsc}."
        "\nSe for um CNPJ deve ser informada apenas a Raiz/Base de oito"
        "\nposições, exceto se natureza jurídica de administração"
        "\npública"
        "\ndireta federal ([101-5], [104-0], [107-4], [116-3], situação em que"
        "\no campo deve ser preenchido com o CNPJ completo (14"
        "\nposições).")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_tpAmb'

    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_procEmi = fields.Integer(
        string="procEmi", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class IdePeriodo(spec_models.AbstractSpecMixin):
    "Período de validade das informações incluídas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideperiodo'
    _generateds_type = 'idePeriodoType'
    _concrete_rec_name = 'efdreinf_iniValid'

    efdreinf01_iniValid = fields.Char(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento. Formato AAAA-MM.")
    efdreinf01_fimValid = fields.Char(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver.Formato AAAA-MM.")


class IdePeriodo2(spec_models.AbstractSpecMixin):
    "Período de validade das informações alteradas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideperiodo2'
    _generateds_type = 'idePeriodoType2'
    _concrete_rec_name = 'efdreinf_iniValid'

    efdreinf01_iniValid = fields.Char(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento, no formato AAAA-MM.")
    efdreinf01_fimValid = fields.Char(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver, no formato AAAA-MM.")


class IdePeriodo28(spec_models.AbstractSpecMixin):
    "Período de validade das informações excluídas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideperiodo28'
    _generateds_type = 'idePeriodoType28'
    _concrete_rec_name = 'efdreinf_iniValid'

    efdreinf01_iniValid = fields.Char(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento no formato AAAA-MM.")
    efdreinf01_fimValid = fields.Char(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver, no formato AAAA-MM.")


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'efdreinf_idePeriodo'

    efdreinf01_idePeriodo = fields.Many2one(
        "efdreinf.01.ideperiodo",
        string="Período de validade das informações incluídas",
        xsd_required=True)
    efdreinf01_infoCadastro = fields.Many2one(
        "efdreinf.01.infocadastro",
        string="Informações do contribuinte",
        xsd_required=True)


class InfoCadastro(spec_models.AbstractSpecMixin):
    "Informações do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infocadastro'
    _generateds_type = 'infoCadastroType'
    _concrete_rec_name = 'efdreinf_classTrib'

    efdreinf01_classTrib = fields.Char(
        string="classTrib", xsd_required=True,
        help="Preencher com o código correspondente à classificação"
        "\ntributária do contribuinte, conforme Tabela de"
        "\nClassificação Tributária.")
    efdreinf01_indEscrituracao = fields.Integer(
        string="indEscrituracao",
        xsd_required=True,
        help="Indicativo da obrigatoriedade do contribuinte em fazer a sua"
        "\nescrituração contábil na ECD - Escrituração Contábil"
        "\nDigital:"
        "\n0 - Empresa Não obrigada à ECD;"
        "\n1 - Empresa obrigada à ECD.")
    efdreinf01_indDesoneracao = fields.Integer(
        string="Indicativo de desoneração da folha pela CPRB",
        xsd_required=True,
        help="Indicativo de desoneração da folha pela CPRB."
        "\n0 - Não Aplicável;"
        "\n1 - Empresa enquadrada nos termos da Lei 12.546/2011 e alterações.")
    efdreinf01_indAcordoIsenMulta = fields.Integer(
        string="indAcordoIsenMulta",
        xsd_required=True)
    efdreinf01_indSitPJ = fields.Integer(
        string="indSitPJ")
    efdreinf01_contato = fields.Many2one(
        "efdreinf.01.contato",
        string="Informações de contato",
        xsd_required=True)
    efdreinf01_softHouse = fields.One2many(
        "efdreinf.01.softhouse",
        "efdreinf01_softHouse_infoCadastro_id",
        string="softHouse",
        help="Informações da empresa desenvolvedora da aplicação que gera"
        "\nos arquivos."
    )
    efdreinf01_infoEFR = fields.Many2one(
        "efdreinf.01.infoefr",
        string="infoEFR",
        help="Informações de órgãos públicos estaduais e municipais"
        "\nrelativas a Ente Federativo Responsável - EFR")


class InfoCadastro5(spec_models.AbstractSpecMixin):
    "Informações do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infocadastro5'
    _generateds_type = 'infoCadastroType5'
    _concrete_rec_name = 'efdreinf_classTrib'

    efdreinf01_classTrib = fields.Char(
        string="classTrib", xsd_required=True,
        help="Preencher com o código correspondente à classificação"
        "\ntributária do contribuinte, conforme Tabela de"
        "\nClassificação Tributária.")
    efdreinf01_indEscrituracao = fields.Integer(
        string="indEscrituracao",
        xsd_required=True,
        help="Indicativo da obrigatoriedade do contribuinte em fazer a sua"
        "\nescrituração contábil na ECD - Escrituração Contábil"
        "\nDigital:"
        "\n0 - Empresa Não obrigada à ECD;"
        "\n1 - Empresa obrigada à ECD.")
    efdreinf01_indDesoneracao = fields.Integer(
        string="Indicativo de desoneração da folha pela CPRB",
        xsd_required=True,
        help="Indicativo de desoneração da folha pela CPRB."
        "\n0 - Não Aplicável;"
        "\n1 - Empresa enquadrada nos termos da Lei 12.546/2011 e alterações.")
    efdreinf01_indAcordoIsenMulta = fields.Integer(
        string="indAcordoIsenMulta",
        xsd_required=True)
    efdreinf01_indSitPJ = fields.Integer(
        string="indSitPJ")
    efdreinf01_contato = fields.Many2one(
        "efdreinf.01.contato11",
        string="Informações de contato",
        xsd_required=True)
    efdreinf01_softHouse = fields.One2many(
        "efdreinf.01.softhouse17",
        "efdreinf01_softHouse_infoCadastro5_id",
        string="softHouse",
        help="Informações da empresa desenvolvedora da aplicação que gera"
        "\nos arquivos."
    )
    efdreinf01_infoEFR = fields.Many2one(
        "efdreinf.01.infoefr23",
        string="infoEFR",
        help="Informações de órgãos públicos estaduais e municipais"
        "\nrelativas a Ente Federativo Responsável - EFR")


class InfoContri(spec_models.AbstractSpecMixin):
    "Informações do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infocontri'
    _generateds_type = 'infoContriType'
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
        string="Inclusão de novas informações",
        xsd_required=True)
    efdreinf01_alteracao = fields.Many2one(
        "efdreinf.01.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    efdreinf01_exclusao = fields.Many2one(
        "efdreinf.01.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class InfoEFR(spec_models.AbstractSpecMixin):
    """Informações de órgãos públicos estaduais e municipais relativas a Ente
    Federativo Responsável - EFR"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoefr'
    _generateds_type = 'infoEFRType'
    _concrete_rec_name = 'efdreinf_ideEFR'

    efdreinf01_ideEFR = fields.Char(
        string="ideEFR", xsd_required=True,
        help="Informar se o Órgão Público é o Ente Federativo Responsável -"
        "\nEFR ou se é uma unidade administrativa autônoma"
        "\nvinculada a um EFR:"
        "\nS - É EFR;"
        "\nN - Não é EFR.")
    efdreinf01_cnpjEFR = fields.Char(
        string="CNPJ do Ente Federativo Responsável",
        help="CNPJ do Ente Federativo Responsável - EFR")


class InfoEFR23(spec_models.AbstractSpecMixin):
    """Informações de órgãos públicos estaduais e municipais relativas a Ente
    Federativo Responsável - EFR"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoefr23'
    _generateds_type = 'infoEFRType23'
    _concrete_rec_name = 'efdreinf_ideEFR'

    efdreinf01_ideEFR = fields.Char(
        string="ideEFR", xsd_required=True,
        help="Informar se o Órgão Público é o Ente Federativo Responsável -"
        "\nEFR ou se é uma unidade administrativa autônoma"
        "\nvinculada a um EFR:"
        "\nS - É EFR;"
        "\nN - Não é EFR.")
    efdreinf01_cnpjEFR = fields.Char(
        string="CNPJ do Ente Federativo Responsável",
        help="CNPJ do Ente Federativo Responsável - EFR")


class NovaValidade(spec_models.AbstractSpecMixin):
    "Novo período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.novavalidade'
    _generateds_type = 'novaValidadeType'
    _concrete_rec_name = 'efdreinf_iniValid'

    efdreinf01_iniValid = fields.Char(
        string="iniValid", xsd_required=True,
        help="Preencher com o mês e ano de início da validade das"
        "\ninformações prestadas no evento, no formato AAAA-MM.")
    efdreinf01_fimValid = fields.Char(
        string="fimValid",
        help="Preencher com o mês e ano de término da validade das"
        "\ninformações, se houver, no formato AAAA-MM.")


class SoftHouse(spec_models.AbstractSpecMixin):
    """Informações da empresa desenvolvedora da aplicação que gera os
    arquivos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.softhouse'
    _generateds_type = 'softHouseType'
    _concrete_rec_name = 'efdreinf_cnpjSoftHouse'

    efdreinf01_softHouse_infoCadastro_id = fields.Many2one(
        "efdreinf.01.infocadastro")
    efdreinf01_cnpjSoftHouse = fields.Char(
        string="CNPJ da empresa desenvolvedora do software",
        xsd_required=True)
    efdreinf01_nmRazao = fields.Char(
        string="Se pessoa jurídica ou órgão público",
        xsd_required=True,
        help="Se pessoa jurídica ou órgão público, informar a Razão Social."
        "\nCaso contrário, informar o nome do contribuinte.")
    efdreinf01_nmCont = fields.Char(
        string="Nome do contato na empresa.",
        xsd_required=True)
    efdreinf01_telefone = fields.Char(
        string="Informar o número do telefone",
        help="Informar o número do telefone, com DDD.")
    efdreinf01_email = fields.Char(
        string="Endereço eletrônico.")


class SoftHouse17(spec_models.AbstractSpecMixin):
    """Informações da empresa desenvolvedora da aplicação que gera os
    arquivos."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.softhouse17'
    _generateds_type = 'softHouseType17'
    _concrete_rec_name = 'efdreinf_cnpjSoftHouse'

    efdreinf01_softHouse_infoCadastro5_id = fields.Many2one(
        "efdreinf.01.infocadastro5")
    efdreinf01_cnpjSoftHouse = fields.Char(
        string="CNPJ da empresa desenvolvedora do software",
        xsd_required=True)
    efdreinf01_nmRazao = fields.Char(
        string="Informar o nome do contribuinte",
        xsd_required=True,
        help="Informar o nome do contribuinte, no caso de pessoa física, ou"
        "\na razão social, no caso de pessoa jurídica.")
    efdreinf01_nmCont = fields.Char(
        string="Nome do contato na empresa.",
        xsd_required=True)
    efdreinf01_telefone = fields.Char(
        string="Informar o número do telefone",
        help="Informar o número do telefone, com DDD.")
    efdreinf01_email = fields.Char(
        string="Endereço eletrônico.")
