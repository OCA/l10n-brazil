# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import _, fields, models

from ...constants.mdfe import OPERATION_TYPE, SITUACAO_MANIFESTACAO, SITUACAO_NFE

_logger = logging.getLogger(__name__)


class MDFe(models.Model):
    _name = "l10n_br_fiscal.mdfe"
    _description = "Recipient Manifestation"

    def name_get(self):
        return [
            (
                rec.id,
                "NFº: {} ({}): {}".format(
                    rec.document_number, rec.cnpj_cpf, rec.company_id.legal_name
                ),
            )
            for rec in self
        ]

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    document_key = fields.Char(
        string="Access Key",
        size=44,
    )
    serie = fields.Char(
        string="Serie",
        size=3,
        index=True,
    )
    document_number = fields.Float(
        string="Document Number",
        index=True,
        digits=(18, 0),
    )
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )
    emitter = fields.Char(
        string="Emitter",
        size=60,
    )
    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        size=18,
    )

    nsu = fields.Char(
        string="NSU",
        size=25,
        index=True,
    )

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        string="Operation Type",
    )

    document_value = fields.Float(
        string="Document Total Value",
        readonly=True,
        digits=(18, 2),
    )

    ie = fields.Char(
        string="Inscrição estadual",
        size=18,
    )
    # TODO: Verificar qual comodel_name utilizar
    # partner_id = fields.Many2one(
    #     comodel_name="l10n_br_fiscal.partner.profile",
    #     string="Supplier",
    # )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier (partner)",
    )

    supplier = fields.Char(
        string="Supplier",
        size=60,
        index=True,
    )

    emission_datetime = fields.Datetime(
        string="Emission Date",
        index=True,
        default=fields.Datetime.now,
    )
    inclusion_datetime = fields.Datetime(
        string="Inclusion Date",
        index=True,
        default=fields.Datetime.now,
    )
    authorization_datetime = fields.Datetime(
        string="Authorization Date",
        index=True,
    )
    cancellation_datetime = fields.Datetime(
        string="Cancellation Date",
        index=True,
    )
    digest_value = fields.Char(
        string="Digest Value",
        size=28,
    )
    inclusion_mode = fields.Char(
        string="Inclusion Mode",
        size=255,
    )
    authorization_protocol = fields.Char(
        string="Authorization protocol",
        size=60,
    )
    cancellation_protocol = fields.Char(
        string="Cancellation protocol",
        size=60,
    )

    document_state = fields.Selection(
        string="Document State",
        selection=SITUACAO_NFE,
        index=True,
    )

    state = fields.Selection(
        string="Manifestation State",
        selection=SITUACAO_MANIFESTACAO,
        index=True,
    )
    dfe_id = fields.Many2one(
        string="DF-e",
        comodel_name="l10n_br_fiscal.dfe",
    )

    def cria_wizard_gerenciamento(self, state=""):

        dados = {
            "manifestacao_ids": [(6, 0, self.ids)],
            "state": state,
        }

        return self.env["wizard.confirma.acao"].create(dados)

    def download_attachment(self, attachment_id=None):

        action = {
            "name": _("Download Attachment"),
            "view_mode": "form",
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "target": "new",
            "flags": {"mode": "readonly"},  # default is 'edit'
            "res_id": attachment_id.id,
        }

        return action
