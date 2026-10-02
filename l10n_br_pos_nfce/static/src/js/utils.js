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

    // Inteiro uniforme em [0, limite), limite <= 2 ** 32. Descarta o que sobra
    // acima do maior multiplo de limite para nao haver vies de modulo.
    function randomBelow(limite) {
        const maximo = Math.floor(2 ** 32 / limite) * limite;
        const buffer = new Uint32Array(1);
        do {
            window.crypto.getRandomValues(buffer);
        } while (buffer[0] >= maximo);
        return buffer[0] % limite;
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
            // FIXME: Alterar a verificação condicional
            // eslint-disable-next-line no-negated-condition
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

                let aleatorio = "";
                if (!codigoAleatorio) {
                    aleatorio = this.gerarCodigoAleatorio(campos);
                }

                campos += aleatorio.toString().padStart(8, "0");
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

        // Codigo numerico da chave (cNF): aleatorio, gerado com crypto, sem
        // derivar dos campos publicos da chave. Descarta os valores que a regra
        // B03-10 da NT 2019.001 rejeita (rejeicao 897): digitos todos iguais,
        // sequencia crescente e codigo igual ao numero do documento.
        gerarCodigoAleatorio(campos) {
            const TAMANHO_CODIGO =
                ChaveEdoc.CODIGO[ChaveEdoc.CODIGO.length - 1] - ChaveEdoc.CODIGO[0];
            const numero = parseInt(campos.substring(...ChaveEdoc.NUMERO), 10);
            let codigo = "";
            do {
                codigo = randomBelow(10 ** TAMANHO_CODIGO)
                    .toString()
                    .padStart(TAMANHO_CODIGO, "0");
            } while (new Set(codigo).size === 1 || "01234567890123456789".includes(codigo) || parseInt(codigo, 10) === numero);

            this._codigoAleatorio = codigo;

            return codigo;
        }

        validar() {
            return true;
        }

        get generatedChave() {
            return this._generatedChave;
        }

        // FIXME: Alterar a classe para que o nome do campo não seja o mesmo
        //  da função.
        // eslint-disable-next-line accessor-pairs
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
