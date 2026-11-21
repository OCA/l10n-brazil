/** @odoo-module **/
/* global QUnit */

import {UNDO_DELAY, ddaInboxService} from "@l10n_br_dda/dda_inbox_service.esm";
import {
    click,
    getFixture,
    nextTick,
    patchWithCleanup,
    triggerEvent,
    triggerHotkey,
} from "@web/../tests/helpers/utils";
import {makeView, setupViewRegistries} from "@web/../tests/views/helpers";
import {browser} from "@web/core/browser/browser";
import {getFacetTexts} from "@web/../tests/search/helpers";
import {registry} from "@web/core/registry";
import {tooltipService} from "@web/core/tooltip/tooltip_service";
import {uiService} from "@web/core/ui/ui_service";

const serviceRegistry = registry.category("services");
const MODEL = "l10n_br_dda.debit";
const CALL_KW = "/web/dataset/call_kw/" + MODEL + "/";

const DASHBOARD = {
    counters: {new: 3, due_7: 2, divergence: 1, suspect: 1, overdue: 0},
    domains: {
        new: [["state", "=", "new"]],
        due_7: [["amount", ">", 100]],
        divergence: [["id", "=", 1]],
        suspect: [["state", "=", "suspect"]],
        overdue: [["id", "=", -1]],
    },
    sources: [
        {
            key: "connection:5",
            name: "BTG Pactual",
            state: "error",
            last_sync: "2026-10-26 06:00:00",
            message: "Authorization expired",
            action: {type: "ir.actions.act_window_close"},
        },
        {
            key: "cnab:1",
            name: "CNAB return",
            state: "ok",
            last_sync: false,
            message: "",
            action: false,
        },
    ],
    currency: {symbol: "R$", position: "before"},
};

const ARCH = `
    <tree js_class="dda_inbox_list">
        <field name="beneficiary_name"/>
        <field name="amount"/>
        <field name="recommended_label" invisible="1"/>
        <field name="recommended_action" widget="dda_recommended_action"/>
    </tree>`;

let serverData = null;
let target = null;
let calls = [];
let responses = {};

function rowSelector(position) {
    return ".o_data_row:nth-child(" + position + ")";
}

async function press(hotkey) {
    triggerHotkey(hotkey);
    await nextTick();
    await nextTick();
}

function methodCalls(method) {
    return calls.filter((call) => call.route === CALL_KW + method);
}

function lastArgs(method) {
    const found = methodCalls(method);
    return found.length ? found[found.length - 1].args.args : null;
}

async function makeInbox() {
    const view = await makeView({
        type: "list",
        resModel: MODEL,
        serverData,
        arch: ARCH,
        mockRPC(route, args) {
            calls.push({route, args});
            if (args.method && args.method in responses) {
                const response = responses[args.method];
                return typeof response === "function" ? response(args) : response;
            }
            return undefined;
        },
    });
    // The search box is focused on load and protects the keys typed in it.
    document.activeElement.blur();
    return view;
}

QUnit.module("l10n_br_dda", (hooks) => {
    hooks.beforeEach(() => {
        calls = [];
        responses = {
            dda_dashboard: DASHBOARD,
            action_apply_recommended: {
                linked: 1,
                bills: 0,
                ignored: 0,
                skipped: 0,
                total_amount: 100,
            },
            action_undo: true,
            action_mark_verified: true,
            action_add_to_payment_order: true,
            action_open_match_wizard: {type: "ir.actions.act_window_close"},
            action_open_ignore_wizard: {type: "ir.actions.act_window_close"},
        };
        serverData = {
            models: {
                [MODEL]: {
                    fields: {
                        beneficiary_name: {string: "Beneficiary", type: "char"},
                        amount: {string: "Amount", type: "float"},
                        state: {
                            string: "State",
                            type: "selection",
                            selection: [
                                ["new", "New"],
                                ["suggested", "Suggested"],
                                ["suspect", "Suspect"],
                            ],
                        },
                        recommended_label: {string: "Label", type: "char"},
                        recommended_action: {
                            string: "Recommended action",
                            type: "selection",
                            selection: [
                                ["link", "Link"],
                                ["link_many", "Link many"],
                                ["create_bill", "Create bill"],
                                ["review", "Review"],
                                ["verify", "Verify"],
                                ["add_to_payment", "Add to payment"],
                                ["none", "None"],
                            ],
                        },
                    },
                    records: [
                        {
                            id: 1,
                            beneficiary_name: "Acme Supplies",
                            amount: 100,
                            state: "suggested",
                            recommended_action: "link",
                            recommended_label: "Link to NF 1234",
                        },
                        {
                            id: 2,
                            beneficiary_name: "Beta Ltda",
                            amount: 250.5,
                            state: "new",
                            recommended_action: "create_bill",
                            recommended_label: "Create bill",
                        },
                        {
                            id: 3,
                            beneficiary_name: "Gamma SA",
                            amount: 80,
                            state: "suspect",
                            recommended_action: "verify",
                            recommended_label: "Verify supplier",
                        },
                        {
                            id: 4,
                            beneficiary_name: "Delta Co",
                            amount: 10,
                            state: "new",
                            recommended_action: "link_many",
                            recommended_label: "3 candidates",
                        },
                        {
                            id: 5,
                            beneficiary_name: "Epsilon",
                            amount: 5,
                            state: "new",
                            recommended_action: "none",
                            recommended_label: "",
                        },
                        {
                            id: 6,
                            beneficiary_name: "Zeta Ltda",
                            amount: 40,
                            state: "suggested",
                            recommended_action: "add_to_payment",
                            recommended_label: "Add to payment order",
                        },
                    ],
                },
            },
        };
        setupViewRegistries();
        serviceRegistry.add("ui", uiService);
        serviceRegistry.add("tooltip", tooltipService);
        serviceRegistry.add("dda_inbox", ddaInboxService);
        target = getFixture();
    });

    QUnit.module("DdaInboxList panel");

    QUnit.test("renders the counters and the source chips", async function (assert) {
        await makeInbox();

        assert.containsOnce(target, ".o_dda_dashboard");
        assert.deepEqual(
            [...target.querySelectorAll(".o_dda_counter")].map((el) => el.dataset.key),
            ["new", "due_7", "divergence", "suspect", "overdue"]
        );
        assert.strictEqual(
            target.querySelector(".o_dda_counter[data-key='new'] .o_dda_counter_value")
                .textContent,
            "3"
        );
        assert.hasClass(
            target.querySelector(".o_dda_counter[data-key='suspect']"),
            "o_dda_counter_alert",
            "a positive suspects counter is highlighted"
        );
        assert.doesNotHaveClass(
            target.querySelector(".o_dda_counter[data-key='overdue']"),
            "o_dda_counter_alert",
            "a zero counter is not highlighted"
        );

        const error = target.querySelector(".o_dda_source[data-key='connection:5']");
        assert.hasClass(error, "o_dda_source_error");
        assert.strictEqual(
            error.querySelector(".o_dda_source_state").textContent,
            "Error"
        );
        assert.strictEqual(error.title, "Authorization expired");
        assert.notOk(error.disabled, "a source with an action is clickable");
        assert.ok(
            error.querySelector(".o_dda_source_sync").textContent.startsWith("synced"),
            "shows the relative time of the last sync"
        );

        const ok = target.querySelector(".o_dda_source[data-key='cnab:1']");
        assert.hasClass(ok, "o_dda_source_ok");
        assert.ok(ok.disabled, "a source without action is not clickable");
        assert.strictEqual(
            ok.querySelector(".o_dda_source_sync").textContent,
            "never synced"
        );
    });

    QUnit.test(
        "a counter applies its domain and a second click removes it",
        async function (assert) {
            await makeInbox();
            assert.containsN(target, ".o_data_row", 6);

            await click(target, ".o_dda_counter[data-key='suspect']");
            assert.containsOnce(target, ".o_data_row");
            assert.deepEqual(getFacetTexts(target), ["Suspects"]);
            assert.hasClass(
                target.querySelector(".o_dda_counter[data-key='suspect']"),
                "o_dda_counter_active"
            );
            assert.strictEqual(
                target
                    .querySelector(".o_dda_counter[data-key='suspect']")
                    .getAttribute("aria-pressed"),
                "true"
            );

            await click(target, ".o_dda_counter[data-key='suspect']");
            assert.containsN(target, ".o_data_row", 6);
            assert.deepEqual(getFacetTexts(target), []);
            assert.doesNotHaveClass(
                target.querySelector(".o_dda_counter[data-key='suspect']"),
                "o_dda_counter_active"
            );
        }
    );

    QUnit.test("the panel is refreshed when the list reloads", async function (assert) {
        await makeInbox();
        const before = methodCalls("dda_dashboard").length;

        await click(target, ".o_dda_counter[data-key='new']");
        assert.ok(
            methodCalls("dda_dashboard").length > before,
            "the dashboard is fetched again after a search"
        );
    });

    QUnit.module("DdaRecommendedAction widget");

    QUnit.test(
        "shows the label and hides the button when there is no action",
        async function (assert) {
            await makeInbox();

            assert.strictEqual(
                target.querySelector(rowSelector(1) + " .o_dda_recommended_action")
                    .textContent,
                "Link to NF 1234"
            );
            assert.strictEqual(
                target.querySelector(rowSelector(4) + " .o_dda_recommended_action")
                    .dataset.action,
                "link_many"
            );
            assert.containsNone(target, rowSelector(5) + " .o_dda_recommended_action");
        }
    );

    QUnit.test(
        "applies the action for one record and offers undo",
        async function (assert) {
            await makeInbox();

            await click(target, rowSelector(1) + " .o_dda_recommended_action");
            assert.deepEqual(lastArgs("action_apply_recommended"), [[1]]);
            assert.containsOnce(target, ".o_notification");
            assert.ok(
                target
                    .querySelector(".o_notification_content")
                    .textContent.includes("1 linked, 0 bills created"),
                "the notification carries the summary"
            );
            assert.ok(
                target
                    .querySelector(".o_notification_content")
                    .textContent.includes("R$ 100.00"),
                "the total uses the currency of the dashboard"
            );
            assert.containsOnce(target, ".o_notification_buttons button");

            await click(target, ".o_notification_buttons button");
            assert.deepEqual(lastArgs("action_undo"), [[1]]);
            assert.containsOnce(target, ".o_notification");
            assert.strictEqual(
                target.querySelector(".o_notification_content").textContent,
                "Action undone."
            );
        }
    );

    QUnit.test("the undo offer lasts ten seconds", async function (assert) {
        const timers = [];
        const realSetTimeout = browser.setTimeout.bind(browser);
        patchWithCleanup(browser, {
            setTimeout(fn, delay, ...rest) {
                if (delay === UNDO_DELAY) {
                    timers.push(fn);
                    return 0;
                }
                return realSetTimeout(fn, delay, ...rest);
            },
        });
        await makeInbox();

        await click(target, rowSelector(1) + " .o_dda_recommended_action");
        assert.strictEqual(UNDO_DELAY, 10000);
        assert.strictEqual(timers.length, 1, "one 10 s timer closes the notification");
        assert.containsOnce(target, ".o_notification");

        timers[0]();
        await nextTick();
        assert.containsNone(target, ".o_notification");
    });

    QUnit.test("undoing a batch reverts boleto by boleto", async function (assert) {
        responses.action_undo = (args) => args.args[0][0] !== 2;
        responses.action_apply_recommended = {
            linked: 1,
            bills: 1,
            ignored: 0,
            skipped: 0,
            total_amount: 350.5,
        };
        await makeInbox();

        await click(target, rowSelector(1) + " .o_list_record_selector input");
        await click(target, rowSelector(2) + " .o_list_record_selector input");
        await click(target, ".o_dda_apply_selected");
        await click(target, ".o_dda_batch_confirm");
        await click(target, ".o_notification_buttons button");

        assert.deepEqual(
            methodCalls("action_undo").map((call) => call.args.args),
            [[[1]], [[2]]],
            "action_undo takes one boleto at a time"
        );
        assert.ok(
            target
                .querySelector(".o_notification_content")
                .textContent.startsWith("1 of 2")
        );
    });

    QUnit.test("an undo refused by the server is reported", async function (assert) {
        responses.action_undo = false;
        await makeInbox();

        await click(target, rowSelector(1) + " .o_dda_recommended_action");
        await click(target, ".o_notification_buttons button");
        assert.ok(
            target
                .querySelector(".o_notification_content")
                .textContent.startsWith("Could not undo")
        );
    });

    QUnit.test(
        "an action that needs a choice opens the wizard",
        async function (assert) {
            await makeInbox();

            await click(target, rowSelector(4) + " .o_dda_recommended_action");
            assert.deepEqual(lastArgs("action_open_match_wizard"), [[4]]);
            assert.strictEqual(methodCalls("action_apply_recommended").length, 0);
        }
    );

    QUnit.test(
        "a suspicious bill asks for confirmation first",
        async function (assert) {
            await makeInbox();

            await click(target, rowSelector(3) + " .o_dda_recommended_action");
            assert.containsOnce(target, ".modal");
            assert.strictEqual(methodCalls("action_mark_verified").length, 0);

            await click(target, ".modal-footer .btn-secondary");
            assert.containsNone(target, ".modal");
            assert.strictEqual(methodCalls("action_mark_verified").length, 0);

            await click(target, rowSelector(3) + " .o_dda_recommended_action");
            await click(target, ".modal-footer .btn-primary");
            assert.deepEqual(lastArgs("action_mark_verified"), [[3]]);
            assert.strictEqual(
                methodCalls("action_apply_recommended").length,
                0,
                "the server skips verify in a batch, so the button calls the right method"
            );
            assert.containsOnce(
                target,
                ".o_notification_buttons button",
                "can be undone"
            );
        }
    );

    QUnit.test("add to payment order calls its own method", async function (assert) {
        await makeInbox();

        await click(target, rowSelector(6) + " .o_dda_recommended_action");
        assert.deepEqual(lastArgs("action_add_to_payment_order"), [[6]]);
        assert.strictEqual(methodCalls("action_apply_recommended").length, 0);
        assert.containsOnce(target, ".o_notification_buttons button", "can be undone");
    });

    QUnit.test(
        "an empty result warns instead of offering undo",
        async function (assert) {
            responses.action_apply_recommended = {
                linked: 0,
                bills: 0,
                ignored: 0,
                skipped: 1,
                total_amount: 0,
            };
            await makeInbox();

            await click(target, rowSelector(2) + " .o_dda_recommended_action");
            assert.containsOnce(target, ".o_notification");
            assert.containsNone(target, ".o_notification_buttons button");
        }
    );

    QUnit.module("DdaInboxList shortcuts");

    QUnit.test("j and k move the focused row", async function (assert) {
        await makeInbox();
        assert.containsNone(target, ".o_dda_row_focus");

        await press("j");
        assert.hasClass(target.querySelector(rowSelector(1)), "o_dda_row_focus");

        await press("j");
        assert.hasClass(target.querySelector(rowSelector(2)), "o_dda_row_focus");
        assert.containsOnce(target, ".o_dda_row_focus");

        await press("k");
        assert.hasClass(target.querySelector(rowSelector(1)), "o_dda_row_focus");

        await press("k");
        assert.hasClass(
            target.querySelector(rowSelector(1)),
            "o_dda_row_focus",
            "stays on the first row"
        );
    });

    QUnit.test(
        "Enter runs the recommended action of the focused row",
        async function (assert) {
            await makeInbox();

            await press("Enter");
            assert.strictEqual(
                methodCalls("action_apply_recommended").length,
                0,
                "nothing happens without a focused row"
            );

            await press("j");
            await press("j");
            await press("Enter");
            assert.deepEqual(lastArgs("action_apply_recommended"), [[2]]);
        }
    );

    QUnit.test(
        "Enter on a cell runs the action instead of opening the record",
        async function (assert) {
            await makeInbox();

            const cell = target.querySelector(rowSelector(2) + " td.o_data_cell");
            await triggerEvent(cell, null, "keydown", {key: "Enter", bubbles: true});
            assert.deepEqual(lastArgs("action_apply_recommended"), [[2]]);
            assert.hasClass(target.querySelector(rowSelector(2)), "o_dda_row_focus");
        }
    );

    QUnit.test("v and i open the wizards for the focused row", async function (assert) {
        await makeInbox();

        await press("v");
        assert.strictEqual(methodCalls("action_open_match_wizard").length, 0);

        await press("j");
        await press("v");
        assert.deepEqual(lastArgs("action_open_match_wizard"), [[1]]);

        await press("i");
        assert.deepEqual(lastArgs("action_open_ignore_wizard"), [[1]]);
    });

    QUnit.test("z undoes the last action of the session", async function (assert) {
        await makeInbox();

        await press("z");
        assert.strictEqual(methodCalls("action_undo").length, 0, "nothing to undo yet");
        assert.strictEqual(
            target.querySelector(".o_notification_content").textContent,
            "Nothing to undo."
        );

        await click(target, rowSelector(1) + " .o_dda_recommended_action");
        await press("z");
        assert.deepEqual(lastArgs("action_undo"), [[1]]);
        assert.containsNone(target, ".o_notification_buttons button");
    });

    QUnit.test("the help button lists the shortcuts", async function (assert) {
        await makeInbox();

        await click(target, ".o_dda_help");
        assert.containsOnce(target, ".modal .o_dda_shortcuts");
        assert.deepEqual(
            [...target.querySelectorAll(".o_dda_shortcuts kbd")].map(
                (el) => el.textContent
            ),
            ["j", "k", "Enter", "v", "i", "z"]
        );
        await click(target, ".o_dda_shortcuts_close");
        assert.containsNone(target, ".modal");
    });

    QUnit.module("DdaInboxList batch");

    QUnit.test("the batch dialog summarizes before applying", async function (assert) {
        responses.action_apply_recommended = {
            linked: 2,
            bills: 1,
            ignored: 0,
            skipped: 1,
            total_amount: 360.5,
        };
        await makeInbox();
        assert.containsNone(target, ".o_dda_apply_selected");

        for (const position of [1, 2, 4, 5]) {
            await click(
                target,
                rowSelector(position) + " .o_list_record_selector input"
            );
        }
        await click(target, ".o_dda_apply_selected");

        assert.containsOnce(target, ".modal .o_dda_batch_summary");
        assert.deepEqual(
            [...target.querySelectorAll(".o_dda_batch_lines li")].map((el) =>
                el.textContent.replace(/\s+/g, " ").trim()
            ),
            [
                "2 will be linked to a bill",
                "1 new bills will be created",
                "1 need your review and will be skipped",
            ]
        );
        assert.ok(
            target
                .querySelector(".o_dda_batch_total")
                .textContent.includes("R$ 360.50"),
            "shows the total of what will be applied"
        );
        assert.strictEqual(methodCalls("action_apply_recommended").length, 0);

        await click(target, ".o_dda_batch_confirm");
        assert.deepEqual(
            lastArgs("action_apply_recommended")[0].slice().sort(),
            [1, 2, 4, 5]
        );
        assert.containsNone(target, ".modal");
        assert.ok(
            target
                .querySelector(".o_notification_content")
                .textContent.includes("2 linked, 1 bills created, 0 ignored, 1 skipped")
        );
    });

    QUnit.test("cancelling the batch dialog changes nothing", async function (assert) {
        await makeInbox();

        await click(target, rowSelector(1) + " .o_list_record_selector input");
        await click(target, ".o_dda_apply_selected");
        await click(target, ".o_dda_batch_cancel");
        assert.containsNone(target, ".modal");
        assert.strictEqual(methodCalls("action_apply_recommended").length, 0);
    });
});
