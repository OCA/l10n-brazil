// Copyright 2026 KMEE
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.en.html)

import {accountTaxHelpers} from "@account/helpers/account_tax";
import {patch} from "@web/core/utils/patch";

// Mirror of the guard in l10n_br_coa/models/account_tax.py. A withholding or
// deductible tax carries a single tax repartition line with a negative factor,
// so the branch that keeps factors >= 0 hands over an empty list while the delta
// still holds the whole tax amount. Indexing that empty list throws while the
// user is still editing the invoice, before any save.
patch(accountTaxHelpers, {
    distribute_delta_amount_smoothly(precision_digits, delta_amount, target_factors) {
        if (!target_factors.length) {
            return [];
        }
        return super.distribute_delta_amount_smoothly(
            precision_digits,
            delta_amount,
            target_factors
        );
    },
});
