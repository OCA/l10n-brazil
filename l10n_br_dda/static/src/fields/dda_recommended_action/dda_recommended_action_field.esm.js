/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

// Bootstrap button style by recommended action: primary for the one-click
// cases, neutral when the user has to choose, warning when it is a risk.
const BUTTON_CLASS = {
    link: "btn-primary",
    create_bill: "btn-primary",
    add_to_payment: "btn-primary",
    link_many: "btn-secondary",
    review: "btn-secondary",
    verify: "btn-warning",
};

export class DdaRecommendedActionField extends Component {
    setup() {
        this.ddaInbox = useService("dda_inbox");
        this.state = useState({busy: false});
    }

    get visible() {
        return Boolean(this.props.value) && this.props.value !== "none";
    }

    get label() {
        const data = this.props.record.data;
        if (data.recommended_label) {
            return data.recommended_label;
        }
        const field = this.props.record.fields[this.props.name];
        const choice = (field.selection || []).find(
            (item) => item[0] === this.props.value
        );
        return choice ? choice[1] : this.props.value;
    }

    get buttonClass() {
        return BUTTON_CLASS[this.props.value] || "btn-secondary";
    }

    async onClick() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            await this.ddaInbox.runRecommended(
                this.props.record.resId,
                this.props.value,
                this.props.record.resModel
            );
        } finally {
            this.state.busy = false;
        }
    }
}
DdaRecommendedActionField.template = "l10n_br_dda.RecommendedActionField";
DdaRecommendedActionField.props = {...standardFieldProps};
DdaRecommendedActionField.displayName = _lt("Recommended action");
DdaRecommendedActionField.supportedTypes = ["selection"];

registry.category("fields").add("dda_recommended_action", DdaRecommendedActionField);
