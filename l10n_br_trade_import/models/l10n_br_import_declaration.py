# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

from odoo import models, fields, api, _

from odoo.exceptions import UserError


class ImportDeclaration(models.Model):
    _name = "l10n_br_trade_import.declaration"
    _description = "Import Declaration"
    _rec_name = "document_number"
    _order = 'document_date desc, document_number desc, id desc'

    document_number = fields.Char(
        required=True,
        help="Number of Import Document"
    )

    document_date = fields.Date(
        required=True,
        help="Document Registration Date"
    )

    # Local de desembaraço Aduaneiro
    customs_clearance_location = fields.Char(
        required=True,
        help="Customs Clearance Location"
    )

    # Estado onde ocorreu o Desembaraço Aduaneiro
    customs_clearance_state_id = fields.Many2one(
        comodel_name="res.country.state",
        required=True,
        domain=[("country_id.code", "=", "BR")],
        help="State where Customs Clearance occurred"
    )

    # Data do Desembaraço Aduaneiro
    customs_clearance_date = fields.Date(
        required=True,
        help="Customs Clearance Date"
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
        required=True,
        string="International Transport Route",
        help="International transport route reported in the Import Declaration (DI)"
    )

    # Valor da AFRMM - Adicional ao Frete para Renovação da
    # Marinha Mercante
    afrmm_value = fields.Float(
        string="AFRMM",
        help="Additional Freight for Merchant Navy Renewal"
    )

    # Forma de importação quanto a intermediação
    intermediary_type = fields.Selection(
        selection=[
            ("conta_propria", "Conta Própria"),
            ("conta_ordem", "Conta e Ordem"),
            ("encomenda", "Encomenda"),
        ],
        required=True,
        string="Intermediation",
        help="Form of import regarding intermediation"
    )

    # Parceiro adquirente ou encomendante
    third_party_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Acquirer or the Orderer",
        help="Acquirer or the Orderer Partner.\n"
        "Required when intermediation is 'Conta e Ordem' or 'Encomenda'"
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

    @api.constrains("intermediary_type", "third_party_partner_id")
    def _check_third_party_partner_id(self):
        for di in self:
            if (
                di.intermediary_type in ["conta_ordem", "encomenda"]
                and not di.third_party_partner_id
            ):
                raise UserError(_(
                    "When the intermediation is 'Conta e Ordem' or 'Encomenda' "
                    "you must provide the Acquirer or Orderer's information"
                ))

    @api.constrains("transportation_type", "afrmm_value")
    def _check_AFRMM_value(self):
        for di in self:
            if (
                di.transportation_type == "maritime"
                and di.afrmm_value == 0
            ):
                raise UserError(_(
                    "When the international transport route is 'Maritime'\n"
                    "You must inform the AFRMM value.")
                )
