odoo.define('sped_cfe.cfe_sat', function (require) {
    "use strict";

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var Model = require('web.Model');
    var Session = require('web.Session');

    var Cfe_sat = Widget.extend({
        template: "Cfe-sat-status",
        init: function (parent, options) {
           this._super(parent);
        },
        start: function() {
            var self = this;
            return this._super(this);
        },
        connect: function (url) {
            return new Session(undefined, url, {use_cors: true});
        },
        chamada_api_cfe_sat: function (params, url){
            var self = this;
            self.connection = self.connect("http://localhost:5000");
            var session_id = self.session.session_id;
            var parameters = params || {};
            var url_session = "http://localhost:5000" + url + "?session_id=" + session_id;
            return $.ajax({
                url: url_session,
                data: parameters,
                type: "POST",
                dataType: 'json',
                traditional: true,
                contentType: "application/x-www-form-urlencoded",
                xhrFields: {
                    withCredentials: false
                },
                crossDomain: true
            })
        },
        consultar_cfe_sat: function (params) {
            var self = this;
            var url = "/hub/v1/consultarsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
                return (new Model('res.users')).call('search_read', [[['id', '=', 1]]]).then(function (result) {
                    alert(result[0].display_name);
                }, function (error) {
                    alert(error);
                });
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        enviar_dados_venda: function (params) {
            var self = this;
            var url = "/hub/v1/enviardadosvenda";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        cancelar_ultima_venda: function (params) {
            var self = this;
            var url = "/hub/v1/cancelarultimavenda";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        comunicar_certificado_icpbrasil: function (params) {
            var self = this;
            var url = "/hub/v1/comunicarcertificadoicpbrasil";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        teste_fim_a_fim: function (params) {
            var self = this;
            var url = "/hub/v1/testefimafim";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        consultar_status_operacional: function (params) {
            var self = this;
            var url = "/hub/v1/consultarstatusoperacional";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        consultar_numero_sessao: function (params) {
            var self = this;
            var url = "/hub/v1/consultarnumerosessao";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        configurar_interface_de_rede: function (params) {
            var self = this;
            var url = "/hub/v1/configurarinterfacederede";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        associar_assinatura: function (params) {
            var self = this;
            var url = "/hub/v1/associarassinatura";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        atualizar_software_sat: function (params) {
            var self = this;
            var url = "/hub/v1/atualizarsoftwaresat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        extrair_logs: function (params) {
            var self = this;
            var url = "/hub/v1/extrairlogs";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        bloquear_sat: function (params) {
            var self = this;
            var url = "/hub/v1/bloquearsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        desbloquear_sat: function (params) {
            var self = this;
            var url = "/hub/v1/desbloquearsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        trocar_codigo_de_ativacao: function (params) {
            var self = this;
            var url = "/hub/v1/trocarcodigodeativacao";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },

    });

    SystrayMenu.Items.push(Cfe_sat);

    return Cfe_sat;
});
