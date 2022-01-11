odoo.define("payment_pagseguro.tour", function (require){
    "use strict";

    var core = require('web.core');
    var tour = require('web_tour.tour');
    var base = require("web_editor.base");
    var rpc = require('web.rpc');
    var _t = core._t;

    tour.register('shop_buy_with_pagseguro', {
        url: "/shop",
        test: true,
        wait_for: base.ready(),
        debug: true,
    },
        [
            {
                content: "Update acquirer token",
                trigger: 'form input[name="search"]',
                run: function(){
                    var args = [
                        [['provider', '=', 'pagseguro']],
                    ];
                    rpc.query({
                        'model':'payment.acquirer',
                        'method': 'search',
                        'args': args,
                    }).then(function (acquirer){
                        return rpc.query({
                            'model': 'payment.acquirer',
                            'method': 'write',
                            'args': [acquirer, {
                                'pagseguro_token': "8EC2714B10DC42DE882BC341A5366899",
                            }],
                        });
                    });
                },
            },
            {
                content: "search conference chair",
                trigger: 'form input[name="search"]',
                run: "text conference chair",
            },
            {
                content: "search conference chair",
                trigger: 'form:has(input[name="search"]) .oe_search_button',
            },
            {
                content: "select conference chair",
                trigger: '.oe_product_cart:first a:contains("Conference Chair")',
            },
            {
                content: "select Conference Chair Steel",
                extra_trigger: '#product_detail',
                trigger: 'label:contains(Steel) input',
            },
            {
                content: "click on add to cart",
                extra_trigger: 'label:contains(Steel) input:propChecked',
                trigger: '#product_detail form[action^="/shop/cart/update"] .btn-primary',
            },
            {
                content: "click in modal on 'Proceed to checkout' button",
                trigger: 'button:contains("Proceed to Checkout")',
            },
            {
                content: "go to checkout",
                trigger: 'a[href*="/shop/checkout"]',
            },
            {
                content: "select payment",
                trigger: '#payment_method label:contains("Pagseguro")',
            },
            {
                content: "Card security code",
                trigger: '#cc_cvc',
                run: function(){
                    $('#cc_cvc')[0].value = '123'
                    $('#cc_expiry')[0].value = '12/2030'
                    $('#cc_holder_name')[0].value = 'VISA'
                    $('#cc_number')[0].value = '4111111111111111'
                },
            },
            {
                content: "Pay Now",
                //Either there are multiple payment methods, and one is checked, either there is only one, and therefore there are no radio inputs
                extra_trigger: '#payment_method label:contains("Pagseguro") input:checked,#payment_method:not(:has("input:radio:visible"))',
                trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
            },
            {
                content: "finish",
                trigger: '.oe_website_sale:contains("Pending... The order will be validated after the payment.")',
                // Leave /shop/confirmation to prevent RPC loop to /shop/payment/get_status.
                // The RPC could be handled in python while the tour is killed (and the session), leading to crashes
                run: function () {
                    window.location.href = '/aboutus'; // Redirect in JS to avoid the RPC loop (20x1sec)
                },
                timeout: 30000,
            },
            {
                content: "wait page loaded",
                trigger: 'h3:contains("Great products for great people")',
                run: function () {}, // it's a check
            },
        ]
    );

});
