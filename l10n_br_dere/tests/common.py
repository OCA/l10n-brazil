# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from erpbrasil.assinatura import misc

from odoo import Command
from odoo.tests import TransactionCase


class DereCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.activity_admin = cls.env.ref("l10n_br_dere.activity_31_02a")
        cls.activity_operator = cls.env.ref("l10n_br_dere.activity_31_05a")
        cls.tax_admin_fee = cls.env.ref("l10n_br_dere.tax_120110006")
        cls.company.write(
            {
                "dere_reg_trib_princ": "2",
                "dere_reg_trib_secund": False,
                "dere_ind_nat_trib": "0",
                "dere_plano_cta_ref": "4",
                "dere_freq_encerr": "M",
                "dere_tp_amb": "2",
                "dere_activity_ids": [Command.set(cls.activity_admin.ids)],
                "dere_client_id": "demo-client",
                "dere_client_secret": "demo-secret",
            }
        )
        if not cls.company.certificate_nfe_id and not cls.company.certificate_ecnpj_id:
            certificate = cls.env["l10n_br_fiscal.certificate"].create(
                {
                    "type": "nf-e",
                    "subtype": "a1",
                    "password": "123456",
                    "file": misc.create_fake_certificate_file(
                        True,
                        "123456",
                        "EMISSOR A TESTE",
                        "BR",
                        "CERTIFICADO VALIDO TESTE",
                    ),
                }
            )
            cls.company.certificate_nfe_id = certificate
        cls.parent_account = cls.env["account.account"].create(
            {
                "name": "Health revenue",
                "code": "DERE31",
                "account_type": "income",
                "company_ids": [Command.set(cls.company.ids)],
                "l10n_br_dere_cta_interna": "31",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "12011",
                "l10n_br_dere_ind_cta": "S",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "4",
                "l10n_br_dere_nivel_cta": 1,
            }
        )
        cls.fee_account = cls.env["account.account"].create(
            {
                "name": "Administration fees",
                "code": "DERE311",
                "account_type": "income",
                "company_ids": [Command.set(cls.company.ids)],
                "l10n_br_dere_cta_interna": "311",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "120110006",
                "l10n_br_dere_ind_cta": "A",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "4",
                "l10n_br_dere_cod_trib": cls.tax_admin_fee.id,
                "l10n_br_dere_cta_sup_id": cls.parent_account.id,
                "l10n_br_dere_nivel_cta": 2,
            }
        )
        cls.equity_account = cls.env["account.account"].create(
            {
                "name": "Unmapped continuity",
                "code": "DERE21",
                "account_type": "equity",
                "company_ids": [Command.set(cls.company.ids)],
                "l10n_br_dere_cta_interna": "21",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "2",
                "l10n_br_dere_ind_cta": "A",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "3",
                "l10n_br_dere_nivel_cta": 1,
            }
        )
        cls.receivable = cls.env["account.account"].create(
            {
                "name": "DeRE receivable",
                "code": "DERE11",
                "account_type": "asset_receivable",
                "reconcile": True,
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.pass_through_account = cls.env["account.account"].create(
            {
                "name": "Amounts due to operators",
                "code": "DERE22",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_ids": [Command.set(cls.company.ids)],
                "l10n_br_dere_cta_interna": "22",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "2",
                "l10n_br_dere_ind_cta": "A",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "2",
                "l10n_br_dere_nivel_cta": 1,
            }
        )
        cls.journal = cls.env["account.journal"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type", "=", "general"),
            ],
            limit=1,
        )
        if not cls.journal:
            cls.journal = cls.env["account.journal"].create(
                {
                    "name": "DeRE miscellaneous",
                    "code": "DER",
                    "type": "general",
                    "company_id": cls.company.id,
                }
            )

    def _event_receipt(self, event_type, period="2026-10"):
        code = event_type.replace("D-", "")
        return f"{code}-{period.replace('-', '')}-{'0' * 19}"

    def _accept_event(self, declaration, event_type):
        event = declaration.event_ids.filtered(
            lambda ev: ev.event_type == event_type
        ).sorted("id")[-1:]
        event.write(
            {
                "state": "accepted",
                "nr_recibo": self._event_receipt(event_type, declaration.per_apur),
                "cd_retorno": "1",
            }
        )
        return event

    def _nfe_access_key(self, number=1):
        cnpj = re.sub(r"[^0-9]", "", self.company._dere_cnpj() or "12345678000195")
        cnpj = cnpj.zfill(14)[:14]
        body = f"352611{cnpj}55" + "001" + f"{number:09d}" + "1" + "12345678"
        total = 0
        weight = 2
        for digit in reversed(body):
            total += int(digit) * weight
            weight = 2 if weight == 9 else weight + 1
        rest = total % 11
        check = 0 if rest < 2 else 11 - rest
        return f"{body}{check}"

    def _closing_receipt(self, period="2026-10"):
        return self._event_receipt("D-1199", period)

    def _accept_closing(self, declaration):
        event = declaration.event_ids.filtered(
            lambda ev: ev.event_type == "D-1199"
        ).sorted("id")[-1:]
        declaration.apply_return(
            event,
            "1",
            nr_recibo=self._closing_receipt(declaration.per_apur),
        )
        return event

    def _create_declaration(self, period="2026-10"):
        vals = {
            "company_id": self.company.id,
            "per_apur": period,
        }
        if re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", period):
            vals["ini_valid"] = f"{period}-01"
        return self.env["l10n_br_dere.declaration"].create(vals)

    def _post_entry(self, date, debit_account, credit_account, amount, ref="DeRE"):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "ref": ref,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": debit_account.id,
                            "name": ref,
                            "debit": amount,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": credit_account.id,
                            "name": ref,
                            "debit": 0.0,
                            "credit": amount,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _post_billing_split(self, date, billed, fee, ref="DeRE billing split"):
        pass_through = billed - fee
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "ref": ref,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.receivable.id,
                            "name": ref,
                            "debit": billed,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.fee_account.id,
                            "name": "Administration fee",
                            "debit": 0.0,
                            "credit": fee,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.pass_through_account.id,
                            "name": "Pass-through to operators",
                            "debit": 0.0,
                            "credit": pass_through,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move
