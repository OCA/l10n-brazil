import {
    advanceTime,
    animationFrame,
    describe,
    expect,
    press,
    queryAll,
    queryFirst,
    queryOne,
    test,
} from "@odoo/hoot";
import {
    contains,
    defineModels,
    fields,
    getFacetTexts,
    models,
    mountView,
    onRpc,
} from "@web/../tests/web_test_helpers";
import {UNDO_DELAY} from "@l10n_br_dda/dda_inbox_service.esm";
import {defineMailModels} from "@mail/../tests/mail_test_helpers";

describe.current.tags("desktop");

const MODEL = "l10n_br_dda.debit";

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

class DdaDebit extends models.Model {
    _name = MODEL;

    beneficiary_name = fields.Char({string: "Beneficiary"});
    amount = fields.Float({string: "Amount"});
    state = fields.Selection({
        string: "State",
        selection: [
            ["new", "New"],
            ["suggested", "Suggested"],
            ["suspect", "Suspect"],
        ],
    });
    recommended_label = fields.Char({string: "Label"});
    recommended_action = fields.Selection({
        string: "Recommended action",
        selection: [
            ["link", "Link"],
            ["link_many", "Link many"],
            ["create_bill", "Create bill"],
            ["review", "Review"],
            ["verify", "Verify"],
            ["add_to_payment", "Add to payment"],
            ["none", "None"],
        ],
    });

    _records = [
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
    ];
}

defineMailModels();
defineModels([DdaDebit]);

const ARCH = `
    <list js_class="dda_inbox_list">
        <field name="beneficiary_name"/>
        <field name="amount"/>
        <field name="recommended_label" column_invisible="1"/>
        <field name="recommended_action" widget="dda_recommended_action"/>
    </list>`;

let calls = [];

function rowSelector(position) {
    return ".o_data_row:nth-child(" + position + ")";
}

async function pressKey(hotkey) {
    await press(hotkey);
    await animationFrame();
    await animationFrame();
}

function methodCalls(method) {
    return calls.filter((call) => call.method === method);
}

function lastArgs(method) {
    const found = methodCalls(method);
    return found.length ? found[found.length - 1].args : null;
}

function notificationText() {
    return queryOne(".o_notification_content").textContent;
}

async function makeInbox(responses = {}) {
    calls = [];
    const answers = {
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
        ...responses,
    };
    onRpc(MODEL, "*", (params) => {
        if (params.method in answers) {
            calls.push({method: params.method, args: params.args});
            const answer = answers[params.method];
            return typeof answer === "function" ? answer(params) : answer;
        }
        return null;
    });
    await mountView({type: "list", resModel: MODEL, arch: ARCH});
    // The search box is focused on load and protects the keys typed in it.
    document.activeElement.blur();
}

describe("panel", () => {
    test("renders the counters and the source chips", async () => {
        await makeInbox();

        expect(".o_dda_dashboard").toHaveCount(1);
        expect(queryAll(".o_dda_counter").map((el) => el.dataset.key)).toEqual([
            "new",
            "due_7",
            "divergence",
            "suspect",
            "overdue",
        ]);
        expect(".o_dda_counter[data-key='new'] .o_dda_counter_value").toHaveText("3");
        expect(".o_dda_counter[data-key='suspect']").toHaveClass("o_dda_counter_alert");
        expect(".o_dda_counter[data-key='overdue']").not.toHaveClass(
            "o_dda_counter_alert"
        );

        const error = ".o_dda_source[data-key='connection:5']";
        expect(error).toHaveClass("o_dda_source_error");
        // The state is upper case on screen (CSS), the text stays as written.
        expect(queryOne(error + " .o_dda_source_state").textContent).toBe("Error");
        expect(error).toHaveAttribute("title", "Authorization expired");
        expect(error).toBeEnabled();
        expect(
            queryOne(error + " .o_dda_source_sync").textContent.startsWith("synced")
        ).toBe(true);

        const ok = ".o_dda_source[data-key='cnab:1']";
        expect(ok).toHaveClass("o_dda_source_ok");
        expect(ok).not.toBeEnabled();
        expect(ok + " .o_dda_source_sync").toHaveText("never synced");
    });

    test("a counter applies its domain and a second click removes it", async () => {
        await makeInbox();
        expect(".o_data_row").toHaveCount(6);

        await contains(".o_dda_counter[data-key='suspect']").click();
        expect(".o_data_row").toHaveCount(1);
        expect(getFacetTexts()).toEqual(["Suspects"]);
        expect(".o_dda_counter[data-key='suspect']").toHaveClass(
            "o_dda_counter_active"
        );
        expect(".o_dda_counter[data-key='suspect']").toHaveAttribute(
            "aria-pressed",
            "true"
        );

        await contains(".o_dda_counter[data-key='suspect']").click();
        expect(".o_data_row").toHaveCount(6);
        expect(getFacetTexts()).toEqual([]);
        expect(".o_dda_counter[data-key='suspect']").not.toHaveClass(
            "o_dda_counter_active"
        );
    });

    test("another counter replaces the active one", async () => {
        await makeInbox();

        await contains(".o_dda_counter[data-key='suspect']").click();
        await contains(".o_dda_counter[data-key='divergence']").click();
        expect(getFacetTexts()).toEqual(["With divergence"]);
        expect(".o_data_row").toHaveCount(1);
        expect(".o_dda_counter_active").toHaveCount(1);
    });

    test("the panel is refreshed when the list reloads", async () => {
        await makeInbox();
        const before = methodCalls("dda_dashboard").length;

        await contains(".o_dda_counter[data-key='new']").click();
        expect(methodCalls("dda_dashboard").length > before).toBe(true);
    });
});

describe("recommended action widget", () => {
    test("shows the label and hides the button when there is no action", async () => {
        await makeInbox();

        expect(rowSelector(1) + " .o_dda_recommended_action").toHaveText(
            "Link to NF 1234"
        );
        expect(rowSelector(4) + " .o_dda_recommended_action").toHaveAttribute(
            "data-action",
            "link_many"
        );
        expect(rowSelector(5) + " .o_dda_recommended_action").toHaveCount(0);
    });

    test("applies the action for one record and offers undo", async () => {
        await makeInbox();

        await contains(rowSelector(1) + " .o_dda_recommended_action").click();
        expect(lastArgs("action_apply_recommended")).toEqual([[1]]);
        expect(".o_notification").toHaveCount(1);
        expect(notificationText()).toInclude("1 linked, 0 bills created");
        expect(notificationText()).toInclude("R$ 100.00");
        expect(".o_notification_buttons button").toHaveCount(1);

        await contains(".o_notification_buttons button").click();
        expect(lastArgs("action_undo")).toEqual([[1]]);
        expect(".o_notification").toHaveCount(1);
        expect(".o_notification_content").toHaveText("Action undone.");
    });

    test("the undo offer lasts ten seconds", async () => {
        await makeInbox();

        await contains(rowSelector(1) + " .o_dda_recommended_action").click();
        expect(UNDO_DELAY).toBe(10000);
        expect(".o_notification").toHaveCount(1);

        await advanceTime(UNDO_DELAY - 100);
        expect(".o_notification").toHaveCount(1);
        await advanceTime(100);
        await animationFrame();
        expect(".o_notification").toHaveCount(0);
    });

    test("undoing a batch reverts boleto by boleto", async () => {
        await makeInbox({
            action_undo: (params) => params.args[0][0] !== 2,
            action_apply_recommended: {
                linked: 1,
                bills: 1,
                ignored: 0,
                skipped: 0,
                total_amount: 350.5,
            },
        });

        await contains(rowSelector(1) + " .o_list_record_selector input").click();
        await contains(rowSelector(2) + " .o_list_record_selector input").click();
        await contains(".o_dda_apply_selected").click();
        await contains(".o_dda_batch_confirm").click();
        await contains(".o_notification_buttons button").click();

        expect(methodCalls("action_undo").map((call) => call.args)).toEqual([
            [[1]],
            [[2]],
        ]);
        expect(notificationText().startsWith("1 of 2")).toBe(true);
    });

    test("an undo refused by the server is reported", async () => {
        await makeInbox({action_undo: false});

        await contains(rowSelector(1) + " .o_dda_recommended_action").click();
        await contains(".o_notification_buttons button").click();
        expect(notificationText().startsWith("Could not undo")).toBe(true);
    });

    test("an action that needs a choice opens the wizard", async () => {
        await makeInbox();

        await contains(rowSelector(4) + " .o_dda_recommended_action").click();
        expect(lastArgs("action_open_match_wizard")).toEqual([[4]]);
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);
    });

    test("a suspicious bill asks for confirmation first", async () => {
        await makeInbox();

        await contains(rowSelector(3) + " .o_dda_recommended_action").click();
        expect(".modal").toHaveCount(1);
        expect(methodCalls("action_mark_verified")).toHaveLength(0);

        await contains(".modal-footer .btn-secondary").click();
        expect(".modal").toHaveCount(0);
        expect(methodCalls("action_mark_verified")).toHaveLength(0);

        await contains(rowSelector(3) + " .o_dda_recommended_action").click();
        await contains(".modal-footer .btn-primary").click();
        expect(lastArgs("action_mark_verified")).toEqual([[3]]);
        // The server skips verify in a batch, so the button calls its own method.
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);
        expect(".o_notification_buttons button").toHaveCount(1);
    });

    test("add to payment order calls its own method", async () => {
        await makeInbox();

        await contains(rowSelector(6) + " .o_dda_recommended_action").click();
        expect(lastArgs("action_add_to_payment_order")).toEqual([[6]]);
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);
        expect(".o_notification_buttons button").toHaveCount(1);
    });

    test("an empty result warns instead of offering undo", async () => {
        await makeInbox({
            action_apply_recommended: {
                linked: 0,
                bills: 0,
                ignored: 0,
                skipped: 1,
                total_amount: 0,
            },
        });

        await contains(rowSelector(2) + " .o_dda_recommended_action").click();
        expect(".o_notification").toHaveCount(1);
        expect(".o_notification_buttons button").toHaveCount(0);
    });
});

describe("shortcuts", () => {
    test("j and k move the focused row", async () => {
        await makeInbox();
        expect(".o_dda_row_focus").toHaveCount(0);

        await pressKey("j");
        expect(rowSelector(1)).toHaveClass("o_dda_row_focus");

        await pressKey("j");
        expect(rowSelector(2)).toHaveClass("o_dda_row_focus");
        expect(".o_dda_row_focus").toHaveCount(1);

        await pressKey("k");
        expect(rowSelector(1)).toHaveClass("o_dda_row_focus");

        await pressKey("k");
        expect(rowSelector(1)).toHaveClass("o_dda_row_focus");
    });

    test("Enter runs the recommended action of the focused row", async () => {
        await makeInbox();

        await pressKey("Enter");
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);

        await pressKey("j");
        await pressKey("j");
        await pressKey("Enter");
        expect(lastArgs("action_apply_recommended")).toEqual([[2]]);
    });

    test("Enter on a cell runs the action instead of opening the record", async () => {
        await makeInbox();

        queryFirst(rowSelector(2) + " td.o_data_cell").focus();
        await pressKey("Enter");
        expect(lastArgs("action_apply_recommended")).toEqual([[2]]);
        expect(rowSelector(2)).toHaveClass("o_dda_row_focus");
    });

    test("v and i open the wizards for the focused row", async () => {
        await makeInbox();

        await pressKey("v");
        expect(methodCalls("action_open_match_wizard")).toHaveLength(0);

        await pressKey("j");
        await pressKey("v");
        expect(lastArgs("action_open_match_wizard")).toEqual([[1]]);

        await pressKey("i");
        expect(lastArgs("action_open_ignore_wizard")).toEqual([[1]]);
    });

    test("z undoes the last action of the session", async () => {
        await makeInbox();

        await pressKey("z");
        expect(methodCalls("action_undo")).toHaveLength(0);
        expect(".o_notification_content").toHaveText("Nothing to undo.");

        await contains(rowSelector(1) + " .o_dda_recommended_action").click();
        await pressKey("z");
        expect(lastArgs("action_undo")).toEqual([[1]]);
        expect(".o_notification_buttons button").toHaveCount(0);
    });

    test("the help button lists the shortcuts", async () => {
        await makeInbox();

        await contains(".o_dda_help").click();
        expect(".modal .o_dda_shortcuts").toHaveCount(1);
        expect(queryAll(".o_dda_shortcuts kbd").map((el) => el.textContent)).toEqual([
            "j",
            "k",
            "Enter",
            "v",
            "i",
            "z",
        ]);
        await contains(".o_dda_shortcuts_close").click();
        expect(".modal").toHaveCount(0);
    });
});

describe("batch", () => {
    test("the batch dialog summarizes before applying", async () => {
        await makeInbox({
            action_apply_recommended: {
                linked: 2,
                bills: 1,
                ignored: 0,
                skipped: 1,
                total_amount: 360.5,
            },
        });
        expect(".o_dda_apply_selected").toHaveCount(0);

        for (const position of [1, 2, 4, 5]) {
            await contains(
                rowSelector(position) + " .o_list_record_selector input"
            ).click();
        }
        await contains(".o_dda_apply_selected").click();

        expect(".modal .o_dda_batch_summary").toHaveCount(1);
        expect(
            queryAll(".o_dda_batch_lines li").map((el) =>
                el.textContent.replace(/\s+/g, " ").trim()
            )
        ).toEqual([
            "2 will be linked to a bill",
            "1 new bills will be created",
            "1 need your review and will be skipped",
        ]);
        expect(".o_dda_batch_total").toHaveText(/R\$ 360\.50/);
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);

        await contains(".o_dda_batch_confirm").click();
        expect(lastArgs("action_apply_recommended")[0].slice().sort()).toEqual([
            1, 2, 4, 5,
        ]);
        expect(".modal").toHaveCount(0);
        expect(notificationText()).toInclude(
            "2 linked, 1 bills created, 0 ignored, 1 skipped"
        );
    });

    test("cancelling the batch dialog changes nothing", async () => {
        await makeInbox();

        await contains(rowSelector(1) + " .o_list_record_selector input").click();
        await contains(".o_dda_apply_selected").click();
        await contains(".o_dda_batch_cancel").click();
        expect(".modal").toHaveCount(0);
        expect(methodCalls("action_apply_recommended")).toHaveLength(0);
    });
});
