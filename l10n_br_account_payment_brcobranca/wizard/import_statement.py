# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class CreditPartnerStatementImporter(models.TransientModel):
    _inherit = "credit.statement.import"

    def import_statement(self):
        """This Function import credit card agency statement"""
        moves = self.env["account.move"]
        cnab_logs = self.env["l10n_br_cnab.return.log"]
        for importer in self:
            journal = importer.journal_id
            ftype = importer._check_extension()
            result = journal.with_context(
                file_name=importer.file_name
            ).multi_move_import(importer.input_statement, ftype.replace(".", ""))
            if len(result) > 1 or result._name == "account.move":
                moves |= result
            if result._name == "l10n_br_cnab.return.log":
                cnab_logs |= result

        if moves:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "account.action_move_journal_line"
            )
            if len(moves) > 1:
                action["domain"] = [("id", "in", moves.ids)]
                ref = self.env.ref("account.view_move_tree")
                action["views"] = [(ref.id, "tree")]
                action["res_id"] = moves.ids[0] if moves else False
                # Removendo Filtros da Visão, valor padrão vem
                # {'search_default_misc_filter':1, 'view_no_maturity': True}
                action["context"] = {"view_no_maturity": True}
            else:
                ref = self.env.ref("account.view_move_form")
                action["views"] = [(ref.id, "form")]
                action["res_id"] = moves.id if moves else False
            return action
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_account_payment_order.l10n_br_cnab_return_log_action"
            )
            if len(cnab_logs) > 1:
                action["domain"] = [("id", "in", cnab_logs.id)]
            ref = self.env.ref(
                "l10n_br_account_payment_order.l10n_br_cnab_return_log_form_view"
            )
            action["views"] = [(ref.id, "form")]
            action["res_id"] = cnab_logs.id if cnab_logs else False
            return action
