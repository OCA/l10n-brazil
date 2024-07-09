# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# Copyright (C) 2024-Today - KMEE (<https://kmee.com.br>).
# @author Luis Felipe Miléo <mileo@kmee.com.br>

import base64

from xsdata.formats.dataclass.parsers import XmlParser

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..utils.lista_declaracoes import ListaDeclaracoes

READONLY_STATES = {
    "open": [("readonly", True)],
    "cancelled": [("readonly", True)],
    "locked": [("readonly", True)],
}


class ImportDeclaration(models.Model):
    _name = "l10n_br_trade_import.declaration"
    _description = "Import Declaration"
    _rec_name = "document_number"
    _order = "document_date desc, document_number desc, id desc"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    document_number = fields.Char(
        states=READONLY_STATES, help="Number of Import Document"
    )

    document_date = fields.Date(
        states=READONLY_STATES, help="Document Registration Date"
    )

    # Local de desembaraço Aduaneiro
    customs_clearance_location = fields.Char(
        states=READONLY_STATES, help="Customs Clearance Location"
    )

    # Estado onde ocorreu o Desembaraço Aduaneiro
    customs_clearance_state_id = fields.Many2one(
        comodel_name="res.country.state",
        states=READONLY_STATES,
        domain=[("country_id.code", "=", "BR")],
        help="State where Customs Clearance occurred",
    )

    # Data do Desembaraço Aduaneiro
    customs_clearance_date = fields.Date(
        states=READONLY_STATES, help="Customs Clearance Date"
    )

    # Via de transporte internacional informada na Declaração
    # de Importação (DI)
    transportation_type = fields.Selection(
        selection=[
            ("maritime", "Maritime"),
            ("fluvial", "Fluvial"),
            ("lacustrine", "Lacustrine"),
            ("aerial", "Aerial"),
            ("postal", "Postal"),
            ("rail", "Rail"),
            ("road", "Road"),
            ("conduit", "Conduct/Transmission Network"),
            ("own_means", "Own Means"),
            ("fict_in_out", "Fictitious In/Out"),
            ("courier", "Courier"),
            ("in_hands", "In hands"),
            ("towing", "By towing."),
        ],
        states=READONLY_STATES,
        string="International Transport Route",
        help="International transport route reported in the Import Declaration (DI)",
    )

    # Valor da AFRMM - Adicional ao Frete para Renovação da
    # Marinha Mercante
    afrmm_value = fields.Float(
        string="AFRMM", help="Additional Freight for Merchant Navy Renewal"
    )

    # Forma de importação quanto a intermediação
    intermediary_type = fields.Selection(
        selection=[
            ("conta_propria", "Conta Própria"),
            ("conta_ordem", "Conta e Ordem"),
            ("encomenda", "Encomenda"),
        ],
        states=READONLY_STATES,
        string="Intermediation",
        help="Form of import regarding intermediation",
    )

    # Parceiro adquirente ou encomendante
    third_party_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Acquirer or the Orderer",
        help="Acquirer or the Orderer Partner.\n"
        "Required when intermediation is 'Conta e Ordem' or 'Encomenda'",
    )

    # Exportador
    exporting_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Exporting",
    )

    addition_ids = fields.One2many(
        comodel_name="l10n_br_trade_import.addition",
        inverse_name="import_declaration_id",
        string="Additions",
    )

    is_imported = fields.Boolean(
        string="Is Imported",
        readonly=True,
    )

    declaration_file = fields.Binary(
        string="Imported File",
        attachment=True,
    )

    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        readonly=True,
        ondelete="restrict",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("locked", "Loked"),
            ("canceled", "Canceled"),
        ],
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )

    @api.constrains("intermediary_type", "third_party_partner_id")
    def _check_third_party_partner_id(self):
        for di in self:
            if (
                di.intermediary_type in ["conta_ordem", "encomenda"]
                and not di.third_party_partner_id
            ):
                raise UserError(
                    _(
                        "When the intermediation is 'Conta e Ordem' or 'Encomenda' "
                        "you must provide the Acquirer or Orderer's information"
                    )
                )

    @api.constrains("transportation_type", "afrmm_value")
    def _check_AFRMM_value(self):
        for di in self:
            if di.transportation_type == "maritime" and di.afrmm_value == 0:
                raise UserError(
                    _(
                        "When the international transport route is 'Maritime'\n"
                        "You must inform the AFRMM value."
                    )
                )

    def action_confirm(self):
        self.write({"state": "done"})

    def action_generate_invoice(self):
        self.ensure_one()
        if self.state != "done":
            raise UserError(_("Only done declarations can generate invoices."))
        self.account_move_id = self.env["account.move"].create(
            {
                "type": "in_invoice",
                "partner_id": self.exporting_partner_id.id,
                "invoice_date": self.document_date,
                "invoice_origin": self.document_number,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Import Declaration",
                            "quantity": 1,
                            "price_unit": sum(
                                addition.value for addition in self.addition_ids
                            ),
                        },
                    )
                ],
            }
        )

    def action_back2draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "canceled"})

    def import_declaration(self, declaration_file):
        file_content = base64.b64decode(declaration_file)
        # try:

        xml_data = file_content.decode("utf-8")
        # Create an XML parser
        parser = XmlParser()
        # Parse XML data into data class
        declaration_list = parser.from_string(xml_data, ListaDeclaracoes)
        vals = self._parse_declaration(declaration_list)
        return self.create(vals)

        # except Exception:
        #     raise UserError(_("Invalid XML file"))

    def _parse_declaration(self, declaracoes):
        if declaracoes.declaracao_importacao:
            lista_mercadorias = []

            for adicao in declaracoes.declaracao_importacao.adicao:
                for mercadoria in adicao.mercadoria:
                    lista_mercadorias.append(
                        {
                            # "import_declaration_id": self.id,
                            "addition_number": adicao.numero_adicao,
                            "addtion_sequence": int(mercadoria.numero_sequencial_item),
                            "product_description": mercadoria.descricao_mercadoria,
                            "product_qty": mercadoria.quantidade,
                            "product_uom": mercadoria.unidade_medida,
                            "product_price_unit": mercadoria.valor_unitario,
                        }
                    )

            vals = {
                "document_number": declaracoes.declaracao_importacao.numero_di,
                # "document_date": declaracoes.declaracao_importacao.data_registro,
                "is_imported": True,
                "addition_ids": [(0, 0, x) for x in lista_mercadorias],
                # "customs_clearance_location":
                #   declaracoes.declaracao_importacao.local_desembaraco,
                # "customs_clearance_state_id":
                #   declaracoes.declaracao_importacao.estado_desembaraco,
                # "customs_clearance_date":
                #   declaracoes.declaracao_importacao.data_desembaraco,
                # "transportation_type":
                #   declaracoes.declaracao_importacao.via_transporte,
                # "afrmm_value": declaracoes.declaracao_importacao.valor_afrmm,
                # "intermediary_type":
                #   declaracoes.declaracao_importacao.tipo_intermediacao,
                # "third_party_partner_id":
                #   declaracoes.declaracao_importacao.parceiro_intermediacao,
                # "exporting_partner_id":
                #   declaracoes.declaracao_importacao.exportador,
            }
            return vals
