odoo.define('l10n_br_portal.l10n_br_portal', function (require) {
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');

    if (!$('.o_portal').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_portal'");
    }

    var cleaveCNPJ = new Cleave('.input-cnpj-cpf', {
        blocks: [2, 3, 3, 4, 2],
        delimiters: ['.', '.', '-'],
        numericOnly: true,
        onValueChanged: function (e) {
            if (e.target.rawValue.length > 11) {
                this.properties['blocks'] = [2, 3, 3, 4, 2];
                this.properties['delimiters'] = ['.', '.', '/', '-'];
            } else {
                this.properties['blocks'] = [3, 3, 3, 3];
                this.properties['delimiters'] = ['.', '.', '-'];
            }
        }
    });

    var cleaveZipCode = new Cleave('.input-zipcode', {
        blocks: [5, 3],
        delimiter: '-',
        numericOnly: true,
    });

    if ($('.o_portal_details').length) {
        var state_options = $(
            "select[name='city_id']:enabled option:not(:first)");
        $('.o_portal_details').on(
            'change', "select[name='state_id']", function () {
                var select = $("select[name='city_id']");
                state_options.detach();
                var displayed_state = state_options.filter(
                    "[data-state_id="+($(this).val() || 0)+"]");
                var nb = displayed_state.appendTo(select).show().size();
                select.parent().toggle(nb>=1);
            });
        $('.o_portal_details').find("select[name='state_id']").change();
        $('.o_portal_details').on('change', "input[name='zipcode']",
            function () {
                var vals = {zipcode: $('input[name="zipcode"]').val()};
                console.log("Changing ZIP");
                ajax.jsonRpc("/l10n_br/zip_search", 'call', vals)
                    .then(function (data) {
                        if (data.error) {
                            // TODO: Retornar nos campos error e error_message
                            console.log('Falha ao consultar cep');
                        } else {
                            $('input[name="district"]').val(data.district);
                            $('input[name="street"]').val(data.street);
                            $('select[name="country_id"]').val(data.country_id);
                            $('select[name="country_id"]').change();
                            $('select[name="state_id"]').val(data.state_id);
                            $('select[name="state_id"]').change();
                            $('select[name="city_id"]').val(data.city_id);
                        }
                    });
            });
    }

});
