odoo.define('l10n_br_portal.l10n_br_portal', function (require) {
'use strict';
    require('web.dom_ready');

    if (!$('.o_portal').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_portal'");
    }

    if ($('.o_portal_details').length) {
        var state_options = $("select[name='city_id']:enabled option:not(:first)");
        $('.o_portal_details').on('change', "select[name='state_id']", function () {
            var select = $("select[name='city_id']");
            state_options.detach();
            var displayed_state = state_options.filter("[data-state_id="+($(this).val() || 0)+"]");
            var nb = displayed_state.appendTo(select).show().size();
            select.parent().toggle(nb>=1);
        });
        $('.o_portal_details').find("select[name='state_id']").change();
    }

});
