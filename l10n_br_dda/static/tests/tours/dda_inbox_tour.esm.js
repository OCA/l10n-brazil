/** @odoo-module **/

import tour from "web_tour.tour";

const ONE_CLICK_ACTION =
    ".o_data_row .o_dda_recommended_action[data-action='link']," +
    ".o_data_row .o_dda_recommended_action[data-action='create_bill']";

// Check-only steps: the legacy tour runner clicks the trigger unless told otherwise.
function noop() {
    return null;
}

function pressKey(key) {
    return () => {
        document.body.dispatchEvent(
            new KeyboardEvent("keydown", {
                key,
                code: "Key" + key.toUpperCase(),
                bubbles: true,
                cancelable: true,
            })
        );
    };
}

tour.register("l10n_br_dda_inbox_tour", {test: true}, [
    {
        content: "The status panel shows the counters",
        trigger: ".o_dda_dashboard .o_dda_counter[data-key='new']",
        run: noop,
    },
    {
        content: "The status panel shows where the bills come from",
        trigger: ".o_dda_dashboard .o_dda_source",
        run: noop,
    },
    {
        content: "Click a counter to filter the list",
        trigger: ".o_dda_counter[data-key='new']",
    },
    {
        content: "The counter is active and the filter is in the search bar",
        trigger: ".o_dda_counter.o_dda_counter_active[data-key='new']",
        extra_trigger: ".o_searchview_facet",
        run: noop,
    },
    {
        content: "Click the counter again to clear the filter",
        trigger: ".o_dda_counter.o_dda_counter_active[data-key='new']",
    },
    {
        content: "The filter is gone",
        trigger: ".o_dda_counter[data-key='new']:not(.o_dda_counter_active)",
        extra_trigger: ".o_searchview:not(:has(.o_searchview_facet))",
        run: noop,
    },
    {
        content: "Open the shortcuts help",
        trigger: ".o_dda_help",
    },
    {
        content: "The help lists the shortcuts; close it",
        trigger: ".o_dda_shortcuts_close",
        extra_trigger: ".o_dda_shortcuts",
    },
    {
        content: "Press j to focus the first row",
        trigger: ".o_data_row",
        run: pressKey("j"),
    },
    {
        content: "The first row is focused",
        trigger: ".o_data_row:first-child.o_dda_row_focus",
        run: noop,
    },
    {
        content: "Press j to move down and k to move back",
        trigger: ".o_data_row:nth-child(2)",
        run: pressKey("j"),
    },
    {
        content: "The second row is focused",
        trigger: ".o_data_row:nth-child(2).o_dda_row_focus",
        run: noop,
    },
    {
        content: "Press k",
        trigger: ".o_data_row:first-child",
        run: pressKey("k"),
    },
    {
        content: "Back to the first row",
        trigger: ".o_data_row:first-child.o_dda_row_focus",
        run: noop,
    },
    {
        content: "Run the recommended action of a bill with a single click",
        trigger: ONE_CLICK_ACTION,
    },
    {
        content: "The notification offers to undo",
        trigger: ".o_notification .o_notification_buttons button:contains('Undo')",
    },
    {
        content: "The undo is confirmed",
        trigger: ".o_notification:contains('Action undone')",
        run: noop,
    },
    {
        content: "Select all bills",
        trigger: "thead .o_list_record_selector input",
    },
    {
        content: "Apply the recommended actions in batch",
        trigger: ".o_dda_apply_selected",
    },
    {
        content: "The batch dialog summarizes before applying",
        trigger: ".o_dda_batch_summary",
        run: noop,
    },
    {
        content: "Cancel the batch",
        trigger: ".o_dda_batch_cancel",
    },
    {
        content: "The list is still there",
        trigger: ".o_dda_dashboard",
        run: noop,
    },
]);
