import {Component} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";

export const DDA_SHORTCUTS = [
    {key: "j", label: _t("Move to the next bill")},
    {key: "k", label: _t("Move to the previous bill")},
    {key: "Enter", label: _t("Run the recommended action of the focused bill")},
    {key: "v", label: _t("Open the link wizard for the focused bill")},
    {key: "i", label: _t("Ignore the focused bill")},
    {key: "z", label: _t("Undo the last action")},
];

export class DdaBatchSummaryDialog extends Component {
    static template = "l10n_br_dda.BatchSummaryDialog";
    static components = {Dialog};
    static props = {
        close: Function,
        preview: Object,
        totalText: {type: String, optional: true},
        confirm: Function,
    };

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
export class DdaShortcutsDialog extends Component {
    static template = "l10n_br_dda.ShortcutsDialog";
    static components = {Dialog};
    static props = {close: Function};

    get shortcuts() {
        return DDA_SHORTCUTS;
    }
}
