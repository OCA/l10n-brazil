odoo.define("l10n_br_pos_nfce.utils", function (require) {
    "use strict";

    require("web.dom_ready");

    const ESTADOS_IBGE = {
        11: ["RO", "Rondônia"],
        12: ["AC", "Acre"],
        13: ["AM", "Amazonas"],
        14: ["RR", "Roraima"],
        15: ["PA", "Pará"],
        16: ["AP", "Amapá"],
        17: ["TO", "Tocantins"],
        21: ["MA", "Maranhão"],
        22: ["PI", "Piauí"],
        23: ["CE", "Ceará"],
        24: ["RN", "Rio Grande do Norte"],
        25: ["PB", "Paraíba"],
        26: ["PE", "Pernambuco"],
        27: ["AL", "Alagoas"],
        28: ["SE", "Sergipe"],
        29: ["BA", "Bahia"],
        31: ["MG", "Minas Gerais"],
        32: ["ES", "Espírito Santo"],
        33: ["RJ", "Rio de Janeiro"],
        35: ["SP", "São Paulo"],
        41: ["PR", "Paraná"],
        42: ["SC", "Santa Catarina"],
        43: ["RS", "Rio Grande do Sul"],
        50: ["MS", "Mato Grosso do Sul"],
        51: ["MT", "Mato Grosso"],
        52: ["GO", "Goiás"],
        53: ["DF", "Distrito Federal"],
    };

    const EDOC_PREFIXO = {
        55: "NFe",
        65: "NFCE",
    };

    function modulo11(base) {
        const pesos = "23456789".repeat(Math.floor(base.length / 8) + 1);
        const acumulado = base
            .split("")
            .reverse()
            .map((a, i) => parseInt(a, 10) * parseInt(pesos[i], 10))
            .reduce((acc, val) => acc + val, 0);
        const digito = 11 - (acumulado % 11);
        return digito >= 10 ? 0 : digito;
    }

    class ChaveEdoc {
        constructor(
            chave = false,
            codigoUF = false,
            anoMes = false,
            cnpjCpfEmitente = false,
            modeloDocumento = false,
            numeroSerie = false,
            numeroDocumento = false,
            formaEmissao = 1,
            codigoAleatorio = false,
            validar = false
        ) {
            if (!chave) {
                if (
                    !(
                        codigoUF &&
                        anoMes &&
                        cnpjCpfEmitente &&
                        modeloDocumento &&
                        numeroSerie &&
                        numeroDocumento
                    )
                ) {
                    throw new Error(
                        "ChaveEdoc: Parâmetros insuficientes para gerar chave"
                    );
                }

                let campos = codigoUF.toString().padStart(2, "0");
                campos += anoMes.toString();
                campos += cnpjCpfEmitente
                    .toString()
                    .replace(/^\d]/g, "")
                    .padStart(14, "0");
                campos += modeloDocumento.toString().padStart(2, "0");
                campos += numeroSerie.toString().padStart(3, "0");
                campos += numeroDocumento.toString().padStart(9, "0");
                campos += formaEmissao.toString().padStart(1, "0");

                if (!codigoAleatorio) {
                    codigoAleatorio = this.calculoCodigoAleatorio(campos);
                }

                campos += codigoAleatorio.toString().padStart(8, "0");
                campos += modulo11(campos).toString();

                this.modeloDocumento = parseInt(
                    campos.substring(...ChaveEdoc.MODELO),
                    10
                );
                this.prefixo = EDOC_PREFIXO[this.modeloDocumento] || "";
                this.chaveGerada = campos;

                if (validar) {
                    this.validar();
                }
            } else {
                const regex = /^\d{44}$/;
                const match = regex.exec(chave);
                if (!match) {
                    throw new Error("ChaveEdoc: Chave inválida");
                }
            }
        }

        calculoCodigoAleatorio(campos) {
            let soma = 0;
            for (let i = 0; i < campos.length; i++) {
                soma += parseInt(campos[i], 10) ** (3 ** 2);
            }

            const TAMANHO_CODIGO =
                ChaveEdoc.CODIGO[ChaveEdoc.CODIGO.length - 1] - ChaveEdoc.CODIGO[0];

            let codigo = soma.toString();
            if (codigo.length > TAMANHO_CODIGO) {
                codigo = codigo.slice(-TAMANHO_CODIGO);
            } else {
                codigo = codigo.padStart(TAMANHO_CODIGO, "0");
            }

            this._codigoAleatorio = codigo;

            return codigo;
        }

        validar() {
            return true;
        }

        get generatedChave() {
            return this._generatedChave;
        }

        set chaveGerada(textChave) {
            this._generatedChave = textChave;
        }

        get codigoAleatorio() {
            return this._codigoAleatorio;
        }
    }

    ChaveEdoc.CUF = [0, 2];
    ChaveEdoc.AAMM = [2, 6];
    ChaveEdoc.CNPJ_CPF = [6, 20];
    ChaveEdoc.MODELO = [20, 22];
    ChaveEdoc.SERIE = [22, 25];
    ChaveEdoc.NUMERO = [25, 34];
    ChaveEdoc.FORMA = [34, 35];
    ChaveEdoc.CODIGO = [35, 43];
    ChaveEdoc.DV = [43];

    return {
        ChaveEdoc: ChaveEdoc,
        ESTADOS_IBGE: ESTADOS_IBGE,
    };
});
