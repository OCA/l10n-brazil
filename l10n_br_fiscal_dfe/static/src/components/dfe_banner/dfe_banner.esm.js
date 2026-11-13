/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {deserializeDateTime, formatDateTime} from "@web/core/l10n/dates";
import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";

/**
 * DF-e distribution panel shown above the third-party document lists.
 *
 * The state comes from ``res.company.dfe_get_banner_data``, which returns raw
 * values: datetimes in the server format and counters as integers. Formatting
 * happens here so dates follow the user's locale and timezone.
 */
export class DfeBanner extends Component {
    static template = "l10n_br_fiscal_dfe.DfeBanner";
    static props = {
        fiscalType: String,
        reload: {type: Function, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({data: null});

        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.data = await this.orm.call("res.company", "dfe_get_banner_data", [
            this.props.fiscalType,
        ]);
    }

    formatDateTime(value) {
        return value ? formatDateTime(deserializeDateTime(value)) : "-";
    }

    get inactivityMessage() {
        const {never_queried, inactivity_days} = this.state.data;
        if (never_queried) {
            return _t(
                "DF-e distribution has never been queried. Configure and run the first query to start receiving documents."
            );
        }
        return _t(
            "Last DF-e query was %(days)s days ago. After 60 days of inactivity, SEFAZ stops generating NSUs for this CNPJ (no retroactive recovery).",
            {days: inactivity_days}
        );
    }

    async reload() {
        await Promise.all([
            this.loadData(),
            this.props.reload ? this.props.reload() : Promise.resolve(),
        ]);
    }

    async callAction(method) {
        const action = await this.orm.call("res.company", method, [
            this.props.fiscalType,
        ]);
        if (!action) {
            return this.reload();
        }
        // A wizard refreshes once the user is done with it; anything else
        // (a cooldown notification, for instance) is already over by then.
        if (action.type === "ir.actions.act_window" && action.target === "new") {
            return this.action.doAction(action, {onClose: () => this.reload()});
        }
        await this.action.doAction(action);
        return this.reload();
    }

    onSearchAll() {
        return this.callAction("dfe_action_search_all");
    }

    onSpecificSearch() {
        return this.callAction("dfe_action_specific_search");
    }

    openAction(actionId) {
        return this.action.doAction(actionId);
    }
}
