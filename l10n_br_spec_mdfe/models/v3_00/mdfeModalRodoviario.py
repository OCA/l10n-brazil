# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 24 01:00:23 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Tipo Sigla da UF
TUf = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AM", "AM"),
    ("AP", "AP"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MG", "MG"),
    ("MS", "MS"),
    ("MT", "MT"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("PR", "PR"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("RS", "RS"),
    ("SC", "SC"),
    ("SE", "SE"),
    ("SP", "SP"),
    ("TO", "TO"),
    ("EX", "EX"),
]

# Tipo de Carroceria
tpCar_veicTracao = [
    ("00", "00"),
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
]

# Tipo de Carroceria
tpCar_veicReboque = [
    ("00", "00"),
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
]

# Tipo Proprietário
tpProp_prop = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
]

# Tipo Proprietário
tpProp_prop = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
]

# Tipo de Rodado
tpRod_veicTracao = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
]


class Condutor(spec_models.AbstractSpecMixin):
    "Informações do(s) Condutor(s) do veículo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.condutor'
    _generateds_type = 'condutorType'
    _concrete_rec_name = 'mdfe_xNome'

    mdfe30_condutor_veicTracao_id = fields.Many2one(
        "mdfe.30.veictracao")
    mdfe30_xNome = fields.Char(
        string="Nome do Condutor", xsd_required=True)
    mdfe30_CPF = fields.Char(
        string="CPF do Condutor", xsd_required=True)


class Disp(spec_models.AbstractSpecMixin):
    "Informações dos dispositivos do Vale Pedágio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.disp'
    _generateds_type = 'dispType'
    _concrete_rec_name = 'mdfe_CNPJForn'

    mdfe30_disp_valePed_id = fields.Many2one(
        "mdfe.30.valeped")
    mdfe30_choice2 = fields.Selection([
        ('mdfe30_CNPJPg', 'CNPJPg'),
        ('mdfe30_CPFPg', 'CPFPg')],
        "CNPJPg/CPFPg",
        default="mdfe30_CNPJPg")
    mdfe30_CNPJForn = fields.Char(
        string="CNPJ da empresa fornecedora do Vale",
        xsd_required=True,
        help="CNPJ da empresa fornecedora do Vale-Pedágio")
    mdfe30_CNPJPg = fields.Char(
        choice='2',
        string="CNPJ do responsável pelo pagamento do Vale",
        help="CNPJ do responsável pelo pagamento do Vale-Pedágio")
    mdfe30_CPFPg = fields.Char(
        choice='2',
        string="CNPJ do responsável pelo pagamento do Vale",
        help="CNPJ do responsável pelo pagamento do Vale-Pedágio")
    mdfe30_nCompra = fields.Char(
        string="Número do comprovante de compra",
        xsd_required=True)
    mdfe30_vValePed = fields.Monetary(
        digits=2, string="Valor do Vale-Pedagio",
        xsd_required=True)


class InfANTT(spec_models.AbstractSpecMixin):
    "Grupo de informações para Agência Reguladora"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infantt'
    _generateds_type = 'infANTTType'
    _concrete_rec_name = 'mdfe_RNTRC'

    mdfe30_RNTRC = fields.Char(
        string="Registro Nacional de Transportadores Rodoviários de Carga")
    mdfe30_infCIOT = fields.One2many(
        "mdfe.30.infciot",
        "mdfe30_infCIOT_infANTT_id",
        string="Dados do CIOT"
    )
    mdfe30_valePed = fields.Many2one(
        "mdfe.30.valeped",
        string="Informações de Vale Pedágio")
    mdfe30_infContratante = fields.One2many(
        "mdfe.30.infcontratante",
        "mdfe30_infContratante_infANTT_id",
        string="infContratante",
        help="Grupo de informações dos contratantes do serviço de"
        "\ntransporte"
    )


class InfCIOT(spec_models.AbstractSpecMixin):
    "Dados do CIOT"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infciot'
    _generateds_type = 'infCIOTType'
    _concrete_rec_name = 'mdfe_CIOT'

    mdfe30_infCIOT_infANTT_id = fields.Many2one(
        "mdfe.30.infantt")
    mdfe30_choice1 = fields.Selection([
        ('mdfe30_CPF', 'CPF'),
        ('mdfe30_CNPJ', 'CNPJ')],
        "CPF/CNPJ",
        default="mdfe30_CPF")
    mdfe30_CIOT = fields.Char(
        string="Código Identificador da Operação de Transporte",
        xsd_required=True)
    mdfe30_CPF = fields.Char(
        choice='1',
        string="Número do CPF responsável pela geração do CIOT",
        xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        choice='1',
        string="Número do CNPJ responsável pela geração do CIOT",
        xsd_required=True)


class InfContratante(spec_models.AbstractSpecMixin):
    "Grupo de informações dos contratantes do serviço de transporte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.infcontratante'
    _generateds_type = 'infContratanteType'
    _concrete_rec_name = 'mdfe_CPF'

    mdfe30_infContratante_infANTT_id = fields.Many2one(
        "mdfe.30.infantt")
    mdfe30_choice3 = fields.Selection([
        ('mdfe30_CPF', 'CPF'),
        ('mdfe30_CNPJ', 'CNPJ')],
        "CPF/CNPJ",
        default="mdfe30_CPF")
    mdfe30_CPF = fields.Char(
        choice='3',
        string="Número do CPF do contratente do serviço",
        xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        choice='3',
        string="Número do CNPJ do contratante do serviço",
        xsd_required=True)


class LacRodo(spec_models.AbstractSpecMixin):
    "Lacres"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.lacrodo'
    _generateds_type = 'lacRodoType'
    _concrete_rec_name = 'mdfe_nLacre'

    mdfe30_lacRodo_rodo_id = fields.Many2one(
        "mdfe.30.rodo")
    mdfe30_nLacre = fields.Char(
        string="Número do Lacre", xsd_required=True)


class Prop(spec_models.AbstractSpecMixin):
    """Proprietários do Veículo.
    Só preenchido quando o veículo não pertencer à empresa emitente do MDF-e"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.prop'
    _generateds_type = 'propType'
    _concrete_rec_name = 'mdfe_CPF'

    mdfe30_choice4 = fields.Selection([
        ('mdfe30_CPF', 'CPF'),
        ('mdfe30_CNPJ', 'CNPJ')],
        "CPF/CNPJ",
        default="mdfe30_CPF")
    mdfe30_CPF = fields.Char(
        choice='4',
        string="Número do CPF", xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        choice='4',
        string="Número do CNPJ", xsd_required=True)
    mdfe30_RNTRC = fields.Char(
        string="Registro Nacional dos Transportadores Rodoviários de Carga",
        xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão Social ou Nome do proprietário",
        xsd_required=True)
    mdfe30_IE = fields.Char(
        string="Inscrição Estadual")
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF")
    mdfe30_tpProp = fields.Selection(
        tpProp_prop,
        string="Tipo Proprietário", xsd_required=True)


class Prop8(spec_models.AbstractSpecMixin):
    """Proprietários do Veículo.
    Só preenchido quando o veículo não pertencer à empresa emitente do MDF-e"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.prop8'
    _generateds_type = 'propType8'
    _concrete_rec_name = 'mdfe_CPF'

    mdfe30_choice5 = fields.Selection([
        ('mdfe30_CPF', 'CPF'),
        ('mdfe30_CNPJ', 'CNPJ')],
        "CPF/CNPJ",
        default="mdfe30_CPF")
    mdfe30_CPF = fields.Char(
        choice='5',
        string="Número do CPF", xsd_required=True)
    mdfe30_CNPJ = fields.Char(
        choice='5',
        string="Número do CNPJ", xsd_required=True)
    mdfe30_RNTRC = fields.Char(
        string="Registro Nacional dos Transportadores Rodoviários de Carga",
        xsd_required=True)
    mdfe30_xNome = fields.Char(
        string="Razão Social ou Nome do proprietário",
        xsd_required=True)
    mdfe30_IE = fields.Char(
        string="Inscrição Estadual")
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF")
    mdfe30_tpProp = fields.Selection(
        tpProp_prop,
        string="Tipo Proprietário", xsd_required=True)


class Rodo(spec_models.AbstractSpecMixin):
    "Informações do modal Rodoviário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.rodo'
    _generateds_type = 'rodo'
    _concrete_rec_name = 'mdfe_infANTT'

    mdfe30_infANTT = fields.Many2one(
        "mdfe.30.infantt",
        string="infANTT")
    mdfe30_veicTracao = fields.Many2one(
        "mdfe.30.veictracao",
        string="veicTracao", xsd_required=True)
    mdfe30_veicReboque = fields.One2many(
        "mdfe.30.veicreboque",
        "mdfe30_veicReboque_rodo_id",
        string="veicReboque"
    )
    mdfe30_codAgPorto = fields.Char(
        string="codAgPorto")
    mdfe30_lacRodo = fields.One2many(
        "mdfe.30.lacrodo",
        "mdfe30_lacRodo_rodo_id",
        string="lacRodo"
    )


class ValePed(spec_models.AbstractSpecMixin):
    """Informações de Vale PedágioOutras informações sobre Vale-Pedágio
    obrigatório que não tenham campos específicos devem ser informadas no
    campo de observações gerais de uso livre pelo contribuinte, visando
    atender as determinações legais vigentes."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.valeped'
    _generateds_type = 'valePedType'
    _concrete_rec_name = 'mdfe_disp'

    mdfe30_disp = fields.One2many(
        "mdfe.30.disp",
        "mdfe30_disp_valePed_id",
        string="Informações dos dispositivos do Vale Pedágio",
        xsd_required=True
    )


class VeicReboque(spec_models.AbstractSpecMixin):
    "Dados dos reboques"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.veicreboque'
    _generateds_type = 'veicReboqueType'
    _concrete_rec_name = 'mdfe_cInt'

    mdfe30_veicReboque_rodo_id = fields.Many2one(
        "mdfe.30.rodo")
    mdfe30_cInt = fields.Char(
        string="Código interno do veículo")
    mdfe30_placa = fields.Char(
        string="Placa do veículo", xsd_required=True)
    mdfe30_RENAVAM = fields.Char(
        string="RENAVAM do veículo")
    mdfe30_tara = fields.Char(
        string="Tara em KG", xsd_required=True)
    mdfe30_capKG = fields.Char(
        string="Capacidade em KG", xsd_required=True)
    mdfe30_capM3 = fields.Char(
        string="Capacidade em M3")
    mdfe30_prop = fields.Many2one(
        "mdfe.30.prop8",
        string="Proprietários do Veículo.",
        help="Proprietários do Veículo."
        "\nSó preenchido quando o veículo não pertencer à empresa emitente do"
        "\nMDF-e")
    mdfe30_tpCar = fields.Selection(
        tpCar_veicReboque,
        string="Tipo de Carroceria", xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF em que veículo está licenciado",
        xsd_required=True)


class VeicTracao(spec_models.AbstractSpecMixin):
    "Dados do Veículo com a Tração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'mdfe.30.veictracao'
    _generateds_type = 'veicTracaoType'
    _concrete_rec_name = 'mdfe_cInt'

    mdfe30_cInt = fields.Char(
        string="Código interno do veículo")
    mdfe30_placa = fields.Char(
        string="Placa do veículo", xsd_required=True)
    mdfe30_RENAVAM = fields.Char(
        string="RENAVAM do veículo")
    mdfe30_tara = fields.Char(
        string="Tara em KG", xsd_required=True)
    mdfe30_capKG = fields.Char(
        string="Capacidade em KG")
    mdfe30_capM3 = fields.Char(
        string="Capacidade em M3")
    mdfe30_prop = fields.Many2one(
        "mdfe.30.prop",
        string="Proprietários do Veículo.",
        help="Proprietários do Veículo."
        "\nSó preenchido quando o veículo não pertencer à empresa emitente do"
        "\nMDF-e")
    mdfe30_condutor = fields.One2many(
        "mdfe.30.condutor",
        "mdfe30_condutor_veicTracao_id",
        string="Informações do(s) Condutor(s) do veículo",
        xsd_required=True
    )
    mdfe30_tpRod = fields.Selection(
        tpRod_veicTracao,
        string="Tipo de Rodado", xsd_required=True)
    mdfe30_tpCar = fields.Selection(
        tpCar_veicTracao,
        string="Tipo de Carroceria", xsd_required=True)
    mdfe30_UF = fields.Selection(
        TUf,
        string="UF em que veículo está licenciado",
        xsd_required=True)
