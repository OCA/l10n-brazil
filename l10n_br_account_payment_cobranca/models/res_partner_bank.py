# Copyright 2012 KMEE - Fernando Marcato Rodrigues
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""

    _inherit = "res.partner.bank"

    codigo_da_empresa = fields.Integer(
        "Código da empresa",
        size=20,
        help="Será informado pelo banco depois do cadastro do beneficiário "
        "na agência",
    )

    tipo_de_conta = fields.Selection(
        selection=[
            ("01", "Conta corrente individual"),
            ("02", "Conta poupança individual"),
            ("03", "Conta depósito judicial/Depósito em consignação " "individual"),
            ("11", "Conta corrente conjunta"),
            ("12", "Conta poupança conjunta"),
            ("13", "Conta depósito judicial/Depósito em consignação " "conjunta"),
        ],
        string="Tipo de Conta",
        default="01",
    )

    bra_number = fields.Char(size=5)
