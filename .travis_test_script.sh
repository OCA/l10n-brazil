#!/usr/bin/env bash

cd ../openerp
pwd
ls ..

./openerp-server --db_user=postgres --db_user=openerp --db_password=admin --db_host=localhost --stop-after-init --test-enable --addons-path=../fiscal_rules,../l10n_br_core,../server-env-tools -i l10n_br_base,l10n_br_crm_zip,l10n_br_data_base,l10n_br_account,l10n_br_sale_stock,l10n_br_delivery,l10n_br_purchase,l10n_br_account_payment,10n_br_account_voucher -d l10n_br_test > >(tee stdout.log)

if $(grep -v mail stdout.log | grep -q ERROR)
then
exit 1
else
exit 0
fi
