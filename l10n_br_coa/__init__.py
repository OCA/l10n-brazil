from . import models


def install_chart_template(env, chart_template_id, desired_tax_frameworks):
    """Install chart template in desired companies"""
    original_company_id = env.user.company_id
    for company_id in env["res.company"].search([]):
        country_code =company_id.country_id.code
        if country_code and country_code.upper() == "BR" and \
                company_id.tax_framework in desired_tax_frameworks:
            if company_id.chart_template_id != chart_template_id:
                env.user.company_ids |= company_id
                env.user.company_id = company_id
                if chart_template_id.existing_accounting(company_id):
                    journal_ids = env['account.journal'].search([
                        ('company_id', '=', company_id.id)
                    ]).filtered(lambda journal: not journal.update_posted)
                    journal_ids.write({'update_posted': True})
                    model_to_check = ['account.bank.statement',
                                      'account.invoice', 'account.move.line',
                                      'account.payment']
                    for model in model_to_check:
                        records = env[model].search([
                            ('company_id', '=', company_id.id)
                        ])
                        if model == 'account.bank.statement':
                            records.mapped(
                                'line_ids').button_cancel_reconciliation()
                        elif model == 'account.invoice':
                            records.action_cancel()
                            records.action_invoice_draft()
                            records.write({'move_name': False})
                        records.unlink()
                    journal_ids.write({'update_posted': False})
                chart_template_id.load_for_current_company(15.0, 15.0)

        if env['ir.module.module'].search_count([
            ('name', '=', 'l10n_br_account'),
            ('state', '=', 'installed'),
        ]):
            from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
            load_fiscal_taxes(env, chart_template_id)

    env.user.company_id = original_company_id
