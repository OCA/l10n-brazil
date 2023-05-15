# Copyright 2022 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated by https://github.com/akretion/xsdata-odoo
#
import textwrap
from odoo import fields, models

from .cte_tipos_basico_v3_00 import INFESPECIE_TPESPECIE

from .tipos_geral_cte_v3_00 import TUF

__NAMESPACE__ = "http://www.portalfiscal.inf.br/cte"

"Descrição do Evento - “Informações da GTV”"
EVGTV_DESCEVENTO = [
    ("Informações da GTV", "Informações da GTV"),
    ("Informacoes da GTV", "Informacoes da GTV"),
]


class EvGtv(models.AbstractModel):
    "Schema XML de validação do evento informações da GTV 110170"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.30.evgtv"
    _inherit = "spec.mixin.cte"
    _binding_type = "EvGtv"

    cte30_descEvento = fields.Selection(
        EVGTV_DESCEVENTO,
        string="Descrição do Evento",
        xsd_required=True,
        help="Descrição do Evento - “Informações da GTV”",
    )

    cte30_infGTV = fields.One2many(
        "cte.30.infgtv", "cte30_infGTV_evGTV_id", string="Grupo de Informações das GTV"
    )


class InfGtv(models.AbstractModel):
    "Grupo de Informações das GTV"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.30.infgtv"
    _inherit = "spec.mixin.cte"
    _binding_type = "EvGtv.InfGtv"

    cte30_infGTV_evGTV_id = fields.Many2one(
        comodel_name="cte.30.evgtv", xsd_implicit=True, ondelete="cascade"
    )
    cte30_nDoc = fields.Char(string="Número da GTV", xsd_required=True)

    cte30_id = fields.Char(
        string="Identificador para diferenciar GTV",
        xsd_required=True,
        help=(
            "Identificador para diferenciar GTV de mesmo número (Usar número "
            "do AIDF ou  identificador interno da empresa),"
        ),
    )

    cte30_serie = fields.Char(string="Série")

    cte30_subserie = fields.Char(string="Subsérie")

    cte30_dEmi = fields.Date(
        string="Data de Emissão",
        xsd_required=True,
        xsd_type="TData",
        help="Data de Emissão\nFormato AAAA-MM-DD",
    )

    cte30_nDV = fields.Char(string="Número Dígito Verificador", xsd_required=True)

    cte30_qCarga = fields.Float(
        string="Quantidade de volumes/malotes",
        xsd_required=True,
        xsd_type="TDec_1104",
        digits=(
            11,
            4,
        ),
    )

    cte30_infEspecie = fields.One2many(
        "cte.30.infgtv_infespecie",
        "cte30_infEspecie_infGTV_id",
        string="Informações das Espécies transportadas",
    )

    cte30_rem = fields.Many2one(
        comodel_name="cte.30.infgtv_rem",
        string="Informações do Remetente da GTV",
        xsd_required=True,
    )

    cte30_dest = fields.Many2one(
        comodel_name="cte.30.infgtv_dest",
        string="Informações do Destinatário da GTV",
        xsd_required=True,
    )

    cte30_placa = fields.Char(string="Placa do veículo", xsd_type="TPlaca")

    cte30_UF = fields.Selection(
        TUF,
        string="UF em que veículo está licenciado",
        xsd_type="TUf",
        help=(
            "UF em que veículo está licenciado\nSigla da UF de licenciamento "
            "do veículo."
        ),
    )

    cte30_RNTRC = fields.Char(string="RNTRC do transportador")


class InfGtvInfEspecie(models.AbstractModel):
    "Informações das Espécies transportadas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.30.infgtv_infespecie"
    _inherit = "spec.mixin.cte"
    _binding_type = "EvGtv.InfGtv.InfEspecie"

    cte30_infEspecie_detGTV_id = fields.Many2one(
        comodel_name="cte.30.detgtv", xsd_implicit=True, ondelete="cascade"
    )
    cte30_infEspecie_infGTV_id = fields.Many2one(
        comodel_name="cte.30.infgtv", xsd_implicit=True, ondelete="cascade"
    )
    cte30_tpEspecie = fields.Selection(
        INFESPECIE_TPESPECIE,
        string="Tipo da Espécie",
        xsd_required=True,
        help=("Tipo da Espécie\n1 - Numerário\n2 - Cheque\n3 - Moeda\n4 - Outros"),
    )

    cte30_vEspecie = fields.Monetary(
        string="Valor Transportada em Espécie indicada",
        xsd_type="TDec_1302",
        currency_field="brl_currency_id",
    )


class InfGtvRem(models.AbstractModel):
    "Informações do Remetente da GTV"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.30.infgtv_rem"
    _inherit = "spec.mixin.cte"
    _binding_type = "EvGtv.InfGtv.Rem"

    cte30_CNPJ = fields.Char(
        string="Número do CNPJ",
        choice="rem",
        xsd_choice_required=True,
        xsd_type="TCnpjOpc",
        help=(
            "Número do CNPJ\nEm caso de empresa não estabelecida no Brasil, "
            "será informado o CNPJ com "
            "zeros.\n\t\t\t\t\t\t\t\t\t\t\t\tInformar os zeros não "
            "significativos."
        ),
    )

    cte30_CPF = fields.Char(
        string="Número do CPF",
        choice="rem",
        xsd_choice_required=True,
        xsd_type="TCpf",
        help="Número do CPF\nInformar os zeros não significativos.",
    )

    cte30_IE = fields.Char(
        string="Inscrição Estadual",
        help=(
            "Inscrição Estadual\nInformar a IE do remetente ou ISENTO se "
            "remetente é contribuinte do ICMS isento de inscrição no cadastro "
            "de contribuintes do ICMS. Caso o remetente não seja contribuinte "
            "do ICMS não informar o conteúdo."
        ),
    )

    cte30_UF = fields.Selection(
        TUF,
        string="Sigla da UF",
        xsd_required=True,
        xsd_type="TUf",
        help="Sigla da UF\nInformar EX para operações com o exterior.",
    )

    cte30_xNome = fields.Char(
        string="Razão social ou nome do remetente", xsd_required=True
    )


class InfGtvDest(models.AbstractModel):
    "Informações do Destinatário da GTV"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.30.infgtv_dest"
    _inherit = "spec.mixin.cte"
    _binding_type = "EvGtv.InfGtv.Dest"

    cte30_CNPJ = fields.Char(
        string="Número do CNPJ",
        choice="dest",
        xsd_choice_required=True,
        xsd_type="TCnpjOpc",
        help=(
            "Número do CNPJ\nEm caso de empresa não estabelecida no Brasil, "
            "será informado o CNPJ com zeros.\n\t\t\t\t\t\t\tInformar os zeros"
            " não significativos."
        ),
    )

    cte30_CPF = fields.Char(
        string="Número do CPF",
        choice="dest",
        xsd_choice_required=True,
        xsd_type="TCpf",
        help="Número do CPF\nInformar os zeros não significativos.",
    )

    cte30_IE = fields.Char(
        string="Inscrição Estadual",
        help=(
            "Inscrição Estadual\nInformar a IE do destinatário ou ISENTO se "
            "remetente é contribuinte do ICMS isento de inscrição no cadastro "
            "de contribuintes do ICMS. Caso o remetente não seja contribuinte "
            "do ICMS não informar o conteúdo."
        ),
    )

    cte30_UF = fields.Selection(
        TUF,
        string="Sigla da UF",
        xsd_required=True,
        xsd_type="TUf",
        help="Sigla da UF\nInformar EX para operações com o exterior.",
    )

    cte30_xNome = fields.Char(
        string="Razão social ou nome do destinatário", xsd_required=True
    )
