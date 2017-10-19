# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class WizardAccountFiscalPositionRuleTest(TransactionCase):
    """Test the wizard 'wizard.account.fiscal.position.rule' """
    def test_wizard_fiscal_position_rule(self):

        #Definition wizard context
        wizard_account_fiscal_position_rule_test = self.env[
            'wizard.account.fiscal.position.rule'].with_context({
                'active_ids': [self.env.ref('account_fiscal_position_rule.menu_action_account_fiscal_position_rule_template_form').id],
                'active_id': self.env.ref('account_fiscal_position_rule.menu_action_account_fiscal_position_rule_template_form').id,
                })

        #Create Wizard and execute action_create() method
        wizard_account_fiscal_position_rule_test.create({
            'company_id': self.env.ref('base.main_company').id
            }).action_create()
