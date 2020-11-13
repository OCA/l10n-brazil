# Copyright (C) 2020 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource
import base64
import datetime


class TestCnabFile(TransactionCase):
    """Tests for import bank statement cnab file format
    (account.bank.statement.import)
    """

    def setUp(self):
        super().setUp()
        self.absi_model = self.env['account.bank.statement.import']
        self.abs_model = self.env['account.bank.statement']
        self.j_model = self.env['account.journal']
        self.absl_model = self.env['account.bank.statement.line']
        cur = self.env.ref('base.BRL')
        cur.active = True
        self.env.ref('base.main_company').currency_id = cur.id
        bank = self.env['res.partner.bank'].create({
            'acc_number': '1405431',
            'partner_id': self.env.ref('base.main_partner').id,
            'company_id': self.env.ref('base.main_company').id,
            'bank_id': self.env.ref('base.res_bank_1').id,
        })
        self.env['account.journal'].create({
            'name': 'Bank Journal TEST CNAB',
            'code': 'BNK077',
            'type': 'bank',
            'bank_account_id': bank.id,
        })

    def test_cnab_file_import(self):
        cnab_file_path = get_module_resource(
            'l10n_br_account_bank_statement_import_cnab',
            'tests/test_cnab_file/', 'cnab240segmentoE.txt')
        cnab_file = base64.b64encode(open(cnab_file_path, 'rb').read())
        bank_statement = self.absi_model.create(
            dict(data_file=cnab_file))
        bank_statement.import_file()
        bank_st_record = self.abs_model.search(
            [('name', 'like', '000001405431')])[0]
        self.assertEqual(bank_st_record.balance_start, 7328.46)
        self.assertEqual(bank_st_record.balance_end_real, 9992.20)

        line = self.absl_model.search([
            ('name', 'ilike', 'RESGATE'),
            ('statement_id', '=', bank_st_record.id)])[0]
        self.assertEqual(line.amount, 2000)
        self.assertEqual(line.date, datetime.date(2020, 8, 20))
