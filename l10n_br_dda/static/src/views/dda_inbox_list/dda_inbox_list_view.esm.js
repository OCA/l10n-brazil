/** @odoo-module **/

import {DDA_CHANGED, DDA_MODEL, batchPreview} from "@l10n_br_dda/dda_inbox_service.esm";
import {
    DdaBatchSummaryDialog,
    DdaShortcutsDialog,
} from "@l10n_br_dda/views/dda_inbox_list/dda_dialogs.esm";
import {useBus, useService} from "@web/core/utils/hooks";
import {useEffect, useState, useSubEnv} from "@odoo/owl";
import {DdaDashboard} from "@l10n_br_dda/views/dda_inbox_list/dda_dashboard.esm";
import {ListController} from "@web/views/list/list_controller";
import {ListRenderer} from "@web/views/list/list_renderer";
import {getActiveHotkey} from "@web/core/hotkeys/hotkey_service";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";

const INTERACTIVE = "button, a, input, select, textarea, [role='menuitem']";

/**
 * @param {EventTarget} target
 * @returns {Boolean} true when the key press is not aimed at a control
 */
function isPlainTarget(target) {
    if (!(target instanceof HTMLElement) || target === document.body) {
        return true;
    }
    return !target.closest(INTERACTIVE);
}

export class DdaInboxListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.inbox = this.env.ddaInbox ? useState(this.env.ddaInbox.inbox) : null;
    }

    getRowClass(record) {
        const classNames = super.getRowClass(record);
        if (this.inbox && this.inbox.focusedId === record.resId) {
            return classNames + " o_dda_row_focus";
        }
        return classNames;
    }

    onCellKeydown(ev, group = null, record = null) {
        const inbox = this.env.ddaInbox;
        if (
            inbox &&
            record &&
            !this.props.list.editedRecord &&
            getActiveHotkey(ev) === "enter"
        ) {
            if (!isPlainTarget(ev.target)) {
                // Let the button or link under the cursor handle the key.
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            inbox.inbox.focusedId = record.resId;
            inbox.runRecommended(record);
            return;
        }
        super.onCellKeydown(ev, group, record);
    }
}

export class DdaInboxListController extends ListController {
    setup() {
        super.setup();
        this.ddaInbox = useService("dda_inbox");
        this.inbox = useState({focusedId: null, version: 0});
        useSubEnv({ddaInbox: this});

        useBus(this.env.bus, DDA_CHANGED, () => this.reload());

        const options = {allowRepeat: true};
        useHotkey("j", () => this.moveFocus(1), options);
        useHotkey("k", () => this.moveFocus(-1), options);
        useHotkey("enter", () => this.runFocused(), {
            validate: (target) => isPlainTarget(target),
        });
        useHotkey("v", () => this.openFocusedWizard("action_open_match_wizard"));
        useHotkey("i", () => this.openFocusedWizard("action_open_ignore_wizard"));
        useHotkey("z", () => this.ddaInbox.undo());

        useEffect(
            () => {
                const root = this.rootRef.el;
                if (!root || !this.inbox.focusedId) {
                    return;
                }
                const row = root.querySelector(".o_data_row.o_dda_row_focus");
                if (row && row.scrollIntoView) {
                    row.scrollIntoView({block: "nearest"});
                }
            },
            () => [this.inbox.focusedId]
        );
    }

    get resModel() {
        return this.props.resModel || DDA_MODEL;
    }

    get focusedRecord() {
        return (
            this.model.root.records.find((rec) => rec.resId === this.inbox.focusedId) ||
            null
        );
    }

    async reload() {
        await this.model.root.load();
        this.inbox.version += 1;
        this.model.notify();
    }

    moveFocus(delta) {
        const records = this.model.root.records;
        if (!records.length) {
            return;
        }
        const index = records.findIndex((rec) => rec.resId === this.inbox.focusedId);
        const next =
            index === -1 ? 0 : Math.min(Math.max(index + delta, 0), records.length - 1);
        this.inbox.focusedId = records[next].resId;
    }

    runRecommended(record) {
        return this.ddaInbox.runRecommended(
            record.resId,
            record.data.recommended_action,
            this.resModel
        );
    }

    runFocused() {
        const record = this.focusedRecord;
        return record ? this.runRecommended(record) : null;
    }

    openFocusedWizard(method) {
        const record = this.focusedRecord;
        return record
            ? this.ddaInbox.openWizard(record.resId, method, this.resModel)
            : null;
    }

    async onClickApplySelected() {
        const root = this.model.root;
        let preview = batchPreview(root.selection);
        if (root.isDomainSelected) {
            // Only the loaded page is known: keep the counts out of the dialog.
            preview = {
                linked: 0,
                bills: 0,
                skipped: 0,
                total: 0,
                count: root.count,
            };
        }
        this.dialogService.add(DdaBatchSummaryDialog, {
            preview,
            totalText: this.ddaInbox.formatAmount(preview.total),
            confirm: async () => {
                const ids = await root.getResIds(true);
                await this.ddaInbox.applyRecommended(ids, this.resModel);
            },
        });
    }

    onClickHelp() {
        this.dialogService.add(DdaShortcutsDialog, {});
    }
}
DdaInboxListController.template = "l10n_br_dda.InboxListView";
DdaInboxListController.components = {
    ...ListController.components,
    DdaDashboard,
};

export const ddaInboxListView = {
    ...listView,
    Controller: DdaInboxListController,
    Renderer: DdaInboxListRenderer,
    buttonTemplate: "l10n_br_dda.InboxListView.Buttons",
};

registry.category("views").add("dda_inbox_list", ddaInboxListView);
