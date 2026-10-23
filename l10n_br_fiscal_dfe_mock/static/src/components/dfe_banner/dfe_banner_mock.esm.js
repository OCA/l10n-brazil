/** @odoo-module **/

import {DfeBanner} from "@l10n_br_fiscal_dfe/components/dfe_banner/dfe_banner.esm";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

/**
 * Mock-mode controls inside the DF-e banner.
 *
 * Until 16.0 the banner was server rendered and this module inherited the
 * ``dfe_document_banner`` QWeb template. In 18.0 the banner is an Owl
 * component, so the controls come from a template extension plus these
 * handlers. The state (``mock_available``/``mock_mode``) is added to
 * ``dfe_get_banner_data`` by this module, and the group is checked again
 * server side, where the real protection lives.
 */
patch(DfeBanner.prototype, {
    get mockActiveMessage() {
        return _t(
            "DF-e queries are answered by the local pool, with no communication with SEFAZ."
        );
    },

    get mockInactiveMessage() {
        return _t("Mock mode is off — DF-e queries reach the real SEFAZ.");
    },

    async callMockAction(method) {
        const action = await this.orm.call("res.company", method, []);
        if (action) {
            await this.action.doAction(action);
        }
        return this.reload();
    },

    onToggleMock() {
        return this.callMockAction("action_toggle_dfe_mock_mode");
    },
});
