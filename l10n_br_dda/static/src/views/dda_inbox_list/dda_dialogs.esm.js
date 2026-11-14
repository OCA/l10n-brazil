/** @odoo-module **/

import {_lt, _t} from "@web/core/l10n/translation";
import {Component} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";

export const DDA_SHORTCUTS = [
    {key: "j", label: _lt("Move to the next bill")},
    {key: "k", label: _lt("Move to the previous bill")},
    {key: "Enter", label: _lt("Run the recommended action of the focused bill")},
    {key: "v", label: _lt("Open the link wizard for the focused bill")},
    {key: "i", label: _lt("Ignore the focused bill")},
    {key: "z", label: _lt("Undo the last action")},
];

export class DdaBatchSummaryDialog extends Component {
    setup() {
        this.busy = false;
    }

    get lines() {
        const {linked, bills, skipped} = this.props.preview;
        return [
            {key: "linked", count: linked, label: _t("will be linked to a bill")},
            {key: "bills", count: bills, label: _t("new bills will be created")},
            {
                key: "skipped",
                count: skipped,
                label: _t("need your review and will be skipped"),
            },
        ].filter((line) => line.count);
    }

    async onConfirm(ev) {
        if (this.busy) {
            return;
        }
        this.busy = true;
        ev.currentTarget.disabled = true;
        try {
            await this.props.confirm();
        } finally {
            this.props.close();
        }
    }
}
DdaBatchSummaryDialog.template = "l10n_br_dda.BatchSummaryDialog";
DdaBatchSummaryDialog.components = {Dialog};
DdaBatchSummaryDialog.props = {
    close: Function,
    preview: Object,
    totalText: {type: String, optional: true},
    confirm: Function,
};

export class DdaShortcutsDialog extends Component {
    get shortcuts() {
        return DDA_SHORTCUTS;
    }
}
DdaShortcutsDialog.template = "l10n_br_dda.ShortcutsDialog";
DdaShortcutsDialog.components = {Dialog};
DdaShortcutsDialog.props = {close: Function};
