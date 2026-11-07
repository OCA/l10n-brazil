/** @odoo-module **/

import {Component, onWillStart, onWillUpdateProps, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {deserializeDateTime} from "@web/core/l10n/dates";
import {useService} from "@web/core/utils/hooks";

export const DOMAIN_PART = "dda_counter";

const COUNTER_KEYS = ["new", "due_7", "divergence", "suspect", "overdue"];
// Counters that need attention when above zero.
const ALERT_KEYS = ["suspect", "overdue"];

export class DdaDashboard extends Component {
    setup() {
        this.ddaInbox = useService("dda_inbox");
        this.action = useService("action");
        this.state = useState({data: null, error: false});
        onWillStart(() => this.load());
        onWillUpdateProps((nextProps) => {
            if (
                nextProps.version !== this.props.version ||
                nextProps.records !== this.props.records
            ) {
                return this.load();
            }
            return null;
        });
    }

    async load() {
        try {
            this.state.data = await this.ddaInbox.loadDashboard(this.props.resModel);
            this.state.error = false;
        } catch (error) {
            // The panel is informative: a failure must never break the list.
            this.state.error = true;
            console.warn("DDA dashboard unavailable", error);
        }
    }

    get counterLabels() {
        return {
            new: _t("New"),
            due_7: _t("Due in 7 days"),
            divergence: _t("With divergence"),
            suspect: _t("Suspects"),
            overdue: _t("Overdue without action"),
        };
    }

    get activeKey() {
        const part = this.env.searchModel.getDomainPart(DOMAIN_PART);
        return part ? part.key : null;
    }

    get counters() {
        const data = this.state.data;
        if (!data) {
            return [];
        }
        const labels = this.counterLabels;
        const active = this.activeKey;
        return COUNTER_KEYS.filter((key) => key in data.counters).map((key) => {
            const value = data.counters[key];
            return {
                key,
                value,
                label: labels[key],
                active: active === key,
                alert: ALERT_KEYS.includes(key) && value > 0,
            };
        });
    }

    get sources() {
        const data = this.state.data;
        return data ? data.sources || [] : [];
    }

    sourceMeta(source) {
        const meta = {
            ok: {icon: "fa-check-circle", text: _t("OK"), className: "o_dda_source_ok"},
            warning: {
                icon: "fa-exclamation-triangle",
                text: _t("Attention"),
                className: "o_dda_source_warning",
            },
            error: {
                icon: "fa-times-circle",
                text: _t("Error"),
                className: "o_dda_source_error",
            },
        };
        return meta[source.state] || meta.warning;
    }

    relativeSync(source) {
        if (!source.last_sync) {
            return _t("never synced");
        }
        const date = deserializeDateTime(source.last_sync);
        return _t("synced") + " " + date.toRelative();
    }

    onCounterClick(item) {
        const searchModel = this.env.searchModel;
        if (item.active) {
            searchModel.setDomainParts({[DOMAIN_PART]: null});
            return;
        }
        searchModel.setDomainParts({
            [DOMAIN_PART]: {
                key: item.key,
                domain: this.state.data.domains[item.key],
                facetLabel: item.label,
            },
        });
    }

    onSourceClick(source) {
        if (source.action) {
            this.action.doAction(source.action);
        }
    }
}
DdaDashboard.template = "l10n_br_dda.Dashboard";
DdaDashboard.props = {
    resModel: String,
    version: Number,
    records: {type: Array, optional: true},
};
