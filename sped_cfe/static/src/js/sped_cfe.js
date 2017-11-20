odoo.define('sped_cfe.sped_sat', function (require) {
    "use strict";

    var form_widget = require('web.form_widgets');
    var Cfe_sat = require('sped_cfe.cfe_sat');

    form_widget.WidgetButton.include({
        start: function() {
            var self = this;
            this.cfe_sat = new Cfe_sat(this);
            this.funcoes_sat = [
                'consultar_cfe_sat',
                'comunicar_certificado_icpbrasil',
                'enviar_dados_venda',
                'cancelar_ultima_venda',
                'teste_fim_a_fim',
                'consultar_status_operacional',
                'consultar_numero_sessao',
                'configurar_interface_de_rede',
                'associar_assinatura',
                'atualizar_software_sat',
                'extrair_logs',
                'bloquear_sat',
                'trocar_codigo_de_ativacao'
            ];
            return this._super(this);
        },
        preparar_parametros: function() {
            var self = this;
            var parametros = {
                'numero_caixa': 1,
            };
            if (this.node.attrs.custom == "enviar_dados_venda") {
                parametros["venda_id"] = self.view.datarecord.id;
            }
            return parametros
        },
        on_click: function() {
            var self = this;
            if (this.funcoes_sat.indexOf(this.node.attrs.custom) >= 0) {
                var params = self.preparar_parametros();
                this.cfe_sat[this.node.attrs.custom](params);
            } else {
                this._super();
            }
        }
    });
});