/** @odoo-module **/
// Copyright 2026-TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

/**
 * Fiscal line form dialogs (sale/purchase/invoice/blanket) inject many x2many
 * fields. On NewId parents this breaks discard/reopen in two ways:
 *
 * 1. Record.discard → __syncData builds StaticList from BM values that are
 *    commands/raw data without a list datapoint handle →
 *    "Datapoint needs load params or handle".
 * 2. Opening the form via duplicateDatapoint calls generateDefaultValues for
 *    missing form fields. Discard uses rollback:true against a stale
 *    _savePoint (line creation defaults), wiping product_id / prices when
 *    reopening.
 *
 * Important: BasicModel.get() turns a falsy x2many into `[]`. That array is
 * truthy but has no `.id`, so clearing BM values to false is not enough — the
 * core still enters `new StaticList({handle: undefined})`. We temporarily
 * remove those fields from activeFields (fieldNames is a getter over its keys)
 * while calling the original __syncData, then install empty stubs on this.data.
 *
 * Note: async patches must bind this._super before the first await — Odoo's
 * patch helper clears _super when the sync wrapper returns the Promise.
 */

/* eslint-disable sort-imports */

import {patch} from "@web/core/utils/patch";
import {Record, RelationalModel} from "@web/views/basic_relational_model";

function makeEmptyX2MStub() {
    return {
        __bm_handle__: null,
        records: [],
        __syncData() {
            // No-op: incomplete x2many has no owl StaticList to sync.
        },
    };
}

function isListDatapoint(bm, value) {
    return (
        typeof value === "string" &&
        bm.localData[value] &&
        bm.localData[value].type === "list"
    );
}

patch(RelationalModel.prototype, "l10n_br_fiscal.X2ManyFormSavePoint", {
    async duplicateDatapoint(record, params) {
        // Bind before await: patch clears this._super when the Promise is returned.
        const _super = this._super.bind(this);
        // Snapshot current list values before generateDefaultValues / reload
        // of form-only fiscal fields. X2ManyFieldDialog.discard rolls back to
        // this savePoint; without it, Discard restores creation defaults and
        // the next open shows an empty line.
        await this.__bm__.save(record.__bm_handle__, {
            savePoint: true,
            viewType: params.viewMode || "form",
        });
        return _super(...arguments);
    },
});

patch(Record.prototype, "l10n_br_fiscal.RecordSafeX2ManySync", {
    __syncData(...args) {
        const _super = this._super.bind(this);
        const bm = this.model.__bm__;
        const element = bm.localData[this.__bm_handle__];
        const unsafeFields = [];

        if (element && element.type === "record" && this.fieldNames) {
            const changes = element._changes || {};
            for (const fieldName of this.fieldNames) {
                const fieldDef = element.fields[fieldName];
                if (
                    !fieldDef ||
                    (fieldDef.type !== "one2many" && fieldDef.type !== "many2many")
                ) {
                    continue;
                }
                const raw =
                    fieldName in changes ? changes[fieldName] : element.data[fieldName];
                // Missing handle OR non-list value: get() yields [] / raw data
                // without `.id` and core StaticList construction crashes.
                if (!isListDatapoint(bm, raw)) {
                    unsafeFields.push(fieldName);
                }
            }
        }

        if (!unsafeFields.length) {
            return _super(...args);
        }

        // FieldNames is a getter over Object.keys(activeFields) — remove unsafe
        // fields from activeFields for the duration of the core sync.
        const savedActiveFields = {};
        for (const fieldName of unsafeFields) {
            if (fieldName in this.activeFields) {
                savedActiveFields[fieldName] = this.activeFields[fieldName];
                delete this.activeFields[fieldName];
            }
        }
        try {
            _super(...args);
        } finally {
            Object.assign(this.activeFields, savedActiveFields);
        }

        // Object.assign in core still copied get()'s [] for skipped fields.
        for (const fieldName of unsafeFields) {
            this.data[fieldName] = makeEmptyX2MStub();
        }
    },
});
