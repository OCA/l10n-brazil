# Copyright (C) 2026 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models
from odoo.tools import float_repr

PIX_GUI = "br.gov.bcb.pix"
MERCHANT_ACCOUNT_INFORMATION_TAG = 26
ADDITIONAL_DATA_FIELD_TAG = 62
GUI_SUBTAG = 0
KEY_SUBTAG = 1
REFERENCE_LABEL_SUBTAG = 5
# The BR Code requires field 62 even without a txid, and then the value is "***".
REFERENCE_LABEL_EMPTY = "***"
# The Central Bank accepts 0000: the code belongs to the acquirer, not to Pix.
DEFAULT_MERCHANT_CATEGORY_CODE = "0000"
# Positions of the transaction amount and of the additional data field in the
# list account_qr_code_emv builds.
AMOUNT_INDEX = 5
ADDITIONAL_DATA_INDEX = 9


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.depends("country_code")
    @api.depends_context("company")
    def _compute_display_qr_setting(self):
        brazilian = self.filtered(lambda bank: bank.country_code == "BR")
        brazilian.display_qr_setting = True
        return super(ResPartnerBank, self - brazilian)._compute_display_qr_setting()

    def _get_merchant_account_info(self):
        if self.country_code != "BR":
            return super()._get_merchant_account_info()
        key = self._get_pix_key()
        if not key:
            return None, None
        merchant_account_info = self._serialize(GUI_SUBTAG, PIX_GUI) + self._serialize(
            KEY_SUBTAG, key
        )
        return MERCHANT_ACCOUNT_INFORMATION_TAG, merchant_account_info

    def _get_pix_key(self):
        """Chave Pix da conta, ou a do parceiro quando a conta nao tem uma propria.

        The key is not a field of this table: it lives on res.partner.pix, which
        l10n_br_base already validates per type. partner_pix_ids is the link to the
        bank account; when no key was tied to the account, the partner's first one is
        used, which is the common case of a company with a single key.
        """
        self.ensure_one()
        pix = self.partner_pix_ids[:1] or self.partner_id.pix_key_ids[:1]
        return pix.key if pix else False

    def _get_additional_data_field(self, comment):
        if self.country_code != "BR":
            return super()._get_additional_data_field(comment)
        return self._serialize(REFERENCE_LABEL_SUBTAG, comment or REFERENCE_LABEL_EMPTY)

    def _get_qr_code_vals_list(self, *args, **kwargs):
        """Two decimals on the amount and field 62 always present.

        Neither is guaranteed by the base module: it prints the amount as the
        float happens to be, so 745.10 travels as 745.1, and it drops field 62
        when the account carries no reference. The BR Code fixes both, and the
        bank app answers an invalid code without saying which field is wrong.
        """
        vals = super()._get_qr_code_vals_list(*args, **kwargs)
        if self.country_code != "BR":
            return vals

        tag, amount = vals[AMOUNT_INDEX]
        if isinstance(amount, int | float):
            vals[AMOUNT_INDEX] = (tag, float_repr(amount, 2))

        tag, additional_data = vals[ADDITIONAL_DATA_INDEX]
        if not additional_data:
            vals[ADDITIONAL_DATA_INDEX] = (
                tag,
                self._get_additional_data_field(REFERENCE_LABEL_EMPTY),
            )
        return vals

    def _get_merchant_category_code(self):
        if self.country_code != "BR":
            return super()._get_merchant_category_code()
        return DEFAULT_MERCHANT_CATEGORY_CODE

    def _get_error_messages_for_qr(self, qr_method, debtor_partner, currency):
        if qr_method == "emv_qr" and self.country_code == "BR":
            if currency.name != "BRL":
                return self.env._("Pix is only available in BRL.")
            if not self._get_pix_key():
                return self.env._(
                    "The bank account %(account)s has no Pix key. Register one "
                    "under the partner's Pix Keys and link it to this account.",
                    account=self.acc_number,
                )
        return super()._get_error_messages_for_qr(qr_method, debtor_partner, currency)

    def _check_for_qr_code_errors(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if qr_method == "emv_qr" and self.country_code == "BR":
            # proxy_type/proxy_value do not apply to Pix: the key comes from
            # res.partner.pix and is already validated per type. The base check would
            # ask for both empty fields and refuse a QR code that is valid.
            if not self._get_pix_key():
                return self.env._(
                    "The bank account %(account)s has no Pix key.",
                    account=self.acc_number,
                )
            if not self.partner_id.city:
                return self.env._("Missing Merchant City.")
            return None
        return super()._check_for_qr_code_errors(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )
