/** @odoo-module **/

import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {formatFloat} from "@web/views/fields/formatters";
import {registry} from "@web/core/registry";
import {sprintf} from "@web/core/utils/strings";

export const DDA_MODEL = "l10n_br_dda.debit";
export const DDA_CHANGED = "L10N_BR_DDA:CHANGED";
export const UNDO_DELAY = 10000;

// What "action_apply_recommended" does in batch, by recommended action. The
// other ones (review, verify, add_to_payment, none) are skipped by the server.
const BATCH_ACTIONS = {
    link: "linked",
    link_many: "linked",
    create_bill: "bills",
};
// Recommended actions that open the match wizard (the user has to choose).
const WIZARD_ACTIONS = ["link_many", "review"];

// Expected result of a batch, only to ask for confirmation.
export function batchPreview(records) {
    const counts = {linked: 0, bills: 0};
    let skipped = 0;
    let total = 0;
    for (const record of records) {
        const kind = BATCH_ACTIONS[record.data.recommended_action];
        if (kind) {
            counts[kind] += 1;
            total += record.data.amount || 0;
        } else {
            skipped += 1;
        }
    }
    return {...counts, skipped, total, count: records.length};
}

export const ddaInboxService = {
    dependencies: ["orm", "notification", "action", "dialog"],

    start(env, {orm, notification, action, dialog}) {
        let last = null;
        let closeUndo = null;
        let currency = null;

        function changed() {
            env.bus.trigger(DDA_CHANGED);
        }

        function formatAmount(amount) {
            const value = formatFloat(amount || 0, {digits: [16, 2]});
            if (!currency || !currency.symbol) {
                return value;
            }
            return currency.position === "after"
                ? value + " " + currency.symbol
                : currency.symbol + " " + value;
        }

        function summaryMessage(summary) {
            return sprintf(
                _t(
                    "%(linked)s linked, %(bills)s bills created, %(ignored)s ignored, %(skipped)s skipped. Total: %(total)s"
                ),
                {
                    linked: summary.linked || 0,
                    bills: summary.bills || 0,
                    ignored: summary.ignored || 0,
                    skipped: summary.skipped || 0,
                    total: formatAmount(summary.total_amount),
                }
            );
        }

        function undoReport(done, total) {
            if (done === total) {
                notification.add(_t("Action undone."), {type: "success"});
            } else if (done) {
                notification.add(
                    sprintf(
                        _t(
                            "%(done)s of %(total)s actions undone. The others can no longer be reverted."
                        ),
                        {done, total}
                    ),
                    {type: "warning"}
                );
            } else {
                notification.add(
                    _t(
                        "Could not undo: the bill is already in an exported payment order or was changed."
                    ),
                    {type: "warning"}
                );
            }
        }

        // "action_undo" works on one boleto at a time, so a batch is undone
        // boleto by boleto.
        async function undo() {
            if (!last) {
                notification.add(_t("Nothing to undo."), {type: "info"});
                return false;
            }
            const {resModel, ids} = last;
            last = null;
            if (closeUndo) {
                closeUndo();
                closeUndo = null;
            }
            let done = 0;
            for (const id of ids) {
                if (await orm.call(resModel, "action_undo", [[id]])) {
                    done += 1;
                }
            }
            changed();
            undoReport(done, ids.length);
            return done === ids.length;
        }

        function showUndo(title, message) {
            if (closeUndo) {
                closeUndo();
            }
            const close = notification.add(message, {
                title,
                type: "success",
                sticky: true,
                buttons: [
                    {
                        name: _t("Undo"),
                        primary: true,
                        onClick: () => {
                            close();
                            return undo();
                        },
                    },
                ],
            });
            closeUndo = close;
            browser.setTimeout(close, UNDO_DELAY);
        }

        async function openWizard(id, method, resModel = DDA_MODEL) {
            const result = await orm.call(resModel, method, [[id]]);
            if (result && result.type) {
                await action.doAction(result, {onClose: changed});
            }
        }

        // Runs a method that is undoable and tells the user, with the undo button.
        async function runUndoable(ids, method, message, resModel = DDA_MODEL) {
            await orm.call(resModel, method, [ids]);
            last = {resModel, ids: [...ids]};
            changed();
            showUndo(_t("Done"), message);
        }

        async function applyRecommended(ids, resModel = DDA_MODEL) {
            const result = await orm.call(resModel, "action_apply_recommended", [ids]);
            if (result && result.type) {
                await action.doAction(result, {onClose: changed});
                return null;
            }
            const summary = result || {};
            changed();
            if (
                (summary.linked || 0) + (summary.bills || 0) + (summary.ignored || 0) >
                0
            ) {
                last = {resModel, ids: [...ids]};
                showUndo(_t("Recommended actions applied"), summaryMessage(summary));
            } else {
                notification.add(
                    _t("Nothing was applied: the selected bills need your review."),
                    {type: "warning"}
                );
            }
            return summary;
        }

        function confirmVerified(id, resModel) {
            return new Promise((resolve) => {
                dialog.add(
                    ConfirmationDialog,
                    {
                        title: _t("Confirm before paying"),
                        body: _t(
                            "This bill is flagged as suspicious. Confirm with the supplier before marking it as verified."
                        ),
                        confirmLabel: _t("Mark as verified"),
                        confirm: () =>
                            runUndoable(
                                [id],
                                "action_mark_verified",
                                _t("The bill was marked as verified."),
                                resModel
                            ),
                        cancel: () => resolve(false),
                    },
                    {onClose: resolve}
                );
            });
        }

        function runRecommended(id, recommendedAction, resModel = DDA_MODEL) {
            if (!recommendedAction || recommendedAction === "none") {
                return Promise.resolve();
            }
            if (WIZARD_ACTIONS.includes(recommendedAction)) {
                return openWizard(id, "action_open_match_wizard", resModel);
            }
            if (recommendedAction === "verify") {
                return confirmVerified(id, resModel);
            }
            if (recommendedAction === "add_to_payment") {
                return runUndoable(
                    [id],
                    "action_add_to_payment_order",
                    _t("The bill was added to the payment order."),
                    resModel
                );
            }
            return applyRecommended([id], resModel);
        }

        async function loadDashboard(resModel = DDA_MODEL) {
            const data = await orm.call(resModel, "dda_dashboard", []);
            currency = data.currency || null;
            return data;
        }

        return {
            applyRecommended,
            formatAmount,
            loadDashboard,
            openWizard,
            runRecommended,
            summaryMessage,
            undo,
            get hasUndo() {
                return Boolean(last);
            },
        };
    },
};

registry.category("services").add("dda_inbox", ddaInboxService);
