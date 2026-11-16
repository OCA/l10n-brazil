// Copyright 2026 KMEE
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {_t} from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";

// Copy buttons of the portal "How to pay" card (Pix code, digitable line).
publicWidget.registry.BoletoCopy = publicWidget.Widget.extend({
    selector: "#boleto_titles",
    events: {
        "click .o_boleto_copy": "_onClickCopy",
    },

    async _onClickCopy(ev) {
        const button = ev.currentTarget;
        const text = button.dataset.copy || "";
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            // Without a secure context the clipboard API is missing.
            const area = document.createElement("textarea");
            area.value = text;
            document.body.appendChild(area);
            area.select();
            document.execCommand("copy");
            area.remove();
        }
        const label = button.querySelector(".o_boleto_copy_label");
        if (!label) {
            return;
        }
        if (!button.dataset.label) {
            button.dataset.label = label.textContent;
        }
        label.textContent = _t("Copied");
        clearTimeout(this._restore);
        this._restore = setTimeout(() => {
            label.textContent = button.dataset.label;
        }, 2000);
    },
});

export default publicWidget.registry.BoletoCopy;
