odoo.define("l10n_br_pos_nfce.nfe-xml", function (require) {
    "use strict";

    const {ESTADOS_IBGE} = require("l10n_br_pos_nfce.utils");

    const BRAZILIAN_STATES_IBGE_CODE_MAP = {
        "Acre (BR)": "12",
        "Alagoas (BR)": "27",
        "Amazonas (BR)": "13",
        "Amapá (BR)": "16",
        "Bahia (BR)": "29",
        "Ceará (BR)": "23",
        "Distrito Federal (BR)": "53",
        "Espírito Santo (BR)": "32",
        "Goiás (BR)": "52",
        "Maranhão (BR)": "21",
        "Minas Gerais (BR)": "31",
        "Mato Grosso do Sul (BR)": "50",
        "Mato Grosso (BR)": "51",
        "Pará (BR)": "15",
        "Paraíba (BR)": "25",
        "Pernambuco (BR)": "26",
        "Piauí (BR)": "22",
        "Paraná (BR)": "41",
        "Rio de Janeiro (BR)": "33",
        "Rio Grande do Norte (BR)": "24",
        "Rondônia (BR)": "11",
        "Roraima (BR)": "14",
        "Rio Grande do Sul (BR)": "43",
        "Santa Catarina (BR)": "42",
        "Sergipe (BR)": "28",
        "São Paulo (BR)": "35",
        "Tocantins (BR)": "17",
    };

    const ESTADO_QRCODE = {
        AC: {
            1: "http://www.sefaznet.ac.gov.br/nfce/qrcode?p=",
            2: "http://www.hml.sefaznet.ac.gov.br/nfce/qrcode?p=",
        },
        AL: {
            1: "http://nfce.sefaz.al.gov.br/QRCode/consultarNFCe.jsp?p=",
            2: "http://nfce.sefaz.al.gov.br/QRCode/consultarNFCe.jsp?p=",
        },
        AM: {
            1: "http://sistemas.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp?p=",
            2: "http://homnfce.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp?p=",
        },
        AP: {
            1: "https://www.sefaz.ap.gov.br/nfce/nfcep.php?p=",
            2: "https://www.sefaz.ap.gov.br/nfcehml/nfce.php?p=",
        },
        BA: {
            1: "http://nfe.sefaz.ba.gov.br/servicos/nfce/qrcode.aspx?p=",
            2: "http://hnfe.sefaz.ba.gov.br/servicos/nfce/qrcode.aspx?p=",
        },
        CE: {
            1: "http://nfce.sefaz.ce.gov.br/pages/ShowNFCe.html?p=",
            2: "http://nfceh.sefaz.ce.gov.br/pages/ShowNFCe.html?p=",
        },
        DF: {
            1: "http://www.fazenda.df.gov.br/nfce/qrcode?p=",
            2: "http://www.fazenda.df.gov.br/nfce/qrcode?p=",
        },
        ES: {
            1: "http://app.sefaz.es.gov.br/ConsultaNFCe?p=",
            2: "http://homologacao.sefaz.es.gov.br/ConsultaNFCe?p=",
        },
        GO: {
            1: "http://nfe.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p=",
            2: "http://homolog.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p=",
        },
        MA: {
            1: "http://nfce.sefaz.ma.gov.br/portal/consultarNFCe.jsp?p=",
            2: "http://homologacao.sefaz.ma.gov.br/portal/consultarNFCe.jsp?p=",
        },
        MG: {
            1: "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=",
            2: "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=",
        },
        MS: {
            1: "http://www.dfe.ms.gov.br/nfce/qrcode?p=",
            2: "http://www.dfe.ms.gov.br/nfce/qrcode?p=",
        },
        MT: {
            1: "http://www.sefaz.mt.gov.br/nfce/consultanfce?p=",
            2: "http://homologacao.sefaz.mt.gov.br/nfce/consultanfce?p=",
        },
        PA: {
            1: "https://appnfc.sefa.pa.gov.br/portal/view/consultas/nfce/nfceForm.seam?p=",
            2: "https://appnfc.sefa.pa.gov.br/portal-homologacao/view/consultas/nfce/nfceForm.seam?p=",
        },
        PB: {
            1: "http://www.sefaz.pb.gov.br/nfce?p=",
            2: "http://www.sefaz.pb.gov.br/nfcehom?p=",
        },
        PE: {
            1: "http://nfce.sefaz.pe.gov.br/nfce/consulta?p=",
            2: "http://nfcehomolog.sefaz.pe.gov.br/nfce/consulta?p=",
        },
        PI: {
            1: "http://www.sefaz.pi.gov.br/nfce/qrcode?p=",
            2: "http://www.sefaz.pi.gov.br/nfce/qrcode?p=",
        },
        PR: {
            1: "http://www.fazenda.pr.gov.br/nfce/qrcode?p=",
            2: "http://www.fazenda.pr.gov.br/nfce/qrcode?p=",
        },
        RJ: {
            1: "http://www4.fazenda.rj.gov.br/consultaNFCe/QRCode?p=",
            2: "http://www4.fazenda.rj.gov.br/consultaNFCe/QRCode?p=",
        },
        RN: {
            1: "http://nfce.set.rn.gov.br/consultarNFCe.aspx?p=",
            2: "http://hom.nfce.set.rn.gov.br/consultarNFCe.aspx?p=",
        },
        RO: {
            1: "http://www.nfce.sefin.ro.gov.br/consultanfce/consulta.jsp?p=",
            2: "http://www.nfce.sefin.ro.gov.br/consultanfce/consulta.jsp?p=",
        },
        RR: {
            1: "https://www.sefaz.rr.gov.br/nfce/servlet/qrcode?p=",
            2: "http://200.174.88.103:8080/nfce/servlet/qrcode?p=",
        },
        RS: {
            1: "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=",
            2: "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=",
        },
        SC: {
            1: "https://sat.sef.sc.gov.br/nfce/consulta?p=",
            2: "https://hom.sat.sef.sc.gov.br/nfce/consulta?p=",
        },
        SE: {
            1: "http://www.nfce.se.gov.br/nfce/qrcode?p=",
            2: "http://www.hom.nfe.se.gov.br/nfce/qrcode?p=",
        },
        SP: {
            1: "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=",
            2: "https://www.homologacao.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=",
        },
        TO: {
            1: "http://www.sefaz.to.gov.br/nfce/qrcode?p=",
            2: "http://homologacao.sefaz.to.gov.br/nfce/qrcode?p=",
        },
    };

    const removePontuaction = (text) => {
        return text.replace(/([^\w ]|_)/g, "");
    };
    class NFeXML {
        constructor(pos, order, chaveEdoc) {
            this.pos = pos;
            this.order = order;
            this.chaveEdoc = chaveEdoc;
            this.date = this.getCurrentDateWithOffsetAndTimezone();
        }

        getCurrentDateWithOffsetAndTimezone() {
            const UTC_OFFSET = -3 * 60;
            const date = new Date(Date.now() + UTC_OFFSET * 60 * 1000);

            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, "0");
            const day = date.getDate().toString().padStart(2, "0");
            const hours = date.getHours().toString().padStart(2, "0");
            const minutes = date.getMinutes().toString().padStart(2, "0");
            const seconds = date.getSeconds().toString().padStart(2, "0");

            const timeZoneOffset = -date.getTimezoneOffset();
            const timeZone = this.formatTimezone(timeZoneOffset);

            return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${timeZone}`;
        }

        formatTimezone(timeZoneOffset) {
            const absOffset = Math.abs(timeZoneOffset);
            const hours = Math.floor(absOffset / 60)
                .toString()
                .padStart(2, "0");
            const minutes = (absOffset % 60).toString().padStart(2, "0");
            const signal = timeZoneOffset < 0 ? "-" : "+";
            return `${signal}${hours}:${minutes}`;
        }

        createNFeXML() {
            const NAMESPACE_XML = "http://www.portalfiscal.inf.br/nfe";
            const VERSION = "4.00";
            const {chaveEdoc} = this;

            const pag = {
                detPag: this.order.get_paymentlines().map((paymentline) => {
                    return this.mountPaymentTag(paymentline);
                }),
            };

            if (this.order.get_change() > 0) {
                pag.vTroco = this.order.get_change().toFixed(2);
            }

            // eslint-disable-next-line no-undef
            return xmlbuilder2.create({
                infNFe: {
                    "@xmlns": NAMESPACE_XML,
                    "@versao": VERSION,
                    "@Id": `NFe${chaveEdoc.generatedChave}`,
                    ide: this.mountIdentificationTag(),
                    emit: this.mountEmitterTag(),
                    dest: this.mountDestinataryTag(),
                    entrega: this.mountDeliveryTag(),
                    det: this.mountOrderLinesTag(),
                    total: this.mountTotalsTag(),
                    transp: this.mountTransportTag(),
                    pag: pag,
                },
            });
        }

        mountIdentificationTag() {
            const NFCeEnvironment = this.pos.config.nfce_environment;
            return {
                cUF: this.getIBGEStateCode(),
                cNF: this.chaveEdoc.codigoAleatorio.toString().padStart(8, "0"),
                natOp: "Venda",
                mod: "65",
                serie: this.pos.config.nfce_document_serie_code,
                nNF: this.order.document_number,
                dhEmi: this.date,
                tpNF: "1",
                idDest: "1",
                cMunFG: this.pos.config.nfce_city_ibge_code,
                tpImp: "4",
                tpEmis: "9",
                cDV: this.chaveEdoc.generatedChave.substr(-1),
                tpAmb: NFCeEnvironment === "1" ? "1" : "2",
                finNFe: "1",
                indFinal: "1",
                indPres: "1",
                procEmi: "0",
                verProc: "Odoo Brasil OCA v14",
                dhCont: this.date,
                xJust: "Sem comunicação com a Internet.",
            };
        }

        getIBGEStateCode() {
            const state = this.pos.company.state_id[1];
            return Object.keys(ESTADOS_IBGE).find(
                (key) => key === BRAZILIAN_STATES_IBGE_CODE_MAP[state]
            );
        }

        mountEmitterTag() {
            const state = this.pos.company.state_id[1];
            const company = this.pos.company;
            return {
                CNPJ: removePontuaction(company.cnpj_cpf),
                xNome: company.legal_name,
                xFant: company.name,
                enderEmit: {
                    xLgr: company.street_name,
                    nro: company.street_number,
                    xBairro: company.district,
                    cMun: company.nfce_city_ibge_code,
                    xMun: company.city_id[1],
                    UF: ESTADOS_IBGE[BRAZILIAN_STATES_IBGE_CODE_MAP[state]][0],
                    CEP: removePontuaction(company.zip),
                    cPais: "1058",
                    xPais: "Brasil",
                },
                IE: removePontuaction(company.inscr_est),
                CRT: "3",
            };
        }

        mountDestinataryTag() {
            const state = this.pos.company.state_id[1];
            const NFCeEnvironment = this.pos.config.nfce_environment;
            const client = this.order.get_client();

            if (client.is_anonymous_consumer) {
                return;
            }

            const customerTaxID = this.order.customer_tax_id;
            const isCPF = customerTaxID.length === 11;
            let name = "";

            if (NFCeEnvironment === "2") {
                name = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL";
            } else {
                name = client.name || "";
            }

            if (
                client.is_anonymous_consumer &&
                (customerTaxID.length === 11 || customerTaxID.length === 14)
            ) {
                return {
                    [isCPF ? "CPF" : "CNPJ"]: removePontuaction(customerTaxID),
                    xNome: name,
                    indIEDest: "9",
                };
            }
            const clientCnpjCpf = client.cnpj_cpf;

            return {
                CPF: removePontuaction(clientCnpjCpf),
                xNome: name,
                enderDest: {
                    xLgr: client.street_name,
                    nro: client.street_number,
                    xBairro: client.district,
                    cMun: this.pos.config.nfce_city_ibge_code,
                    xMun: client.city_id[1],
                    UF: ESTADOS_IBGE[BRAZILIAN_STATES_IBGE_CODE_MAP[state]][0],
                    CEP: removePontuaction(client.zip),
                    cPais: "1058",
                    xPais: "Brasil",
                },
                indIEDest: "9",
            };
        }

        mountDeliveryTag() {
            const state = this.pos.company.state_id[1];
            const client = this.order.get_client();

            if (client.is_anonymous_consumer) {
                return;
            }

            const customerTaxID = this.order.customer_tax_id;
            const isCPF = customerTaxID.length === 11;

            return {
                [isCPF ? "CPF" : "CNPJ"]: removePontuaction(customerTaxID),
                xNome: client.name,
                xLgr: client.street_name,
                nro: client.street_number,
                xBairro: client.district,
                cMun: this.pos.config.nfce_city_ibge_code,
                xMun: client.city_id[1],
                UF: ESTADOS_IBGE[BRAZILIAN_STATES_IBGE_CODE_MAP[state]][0],
                CEP: removePontuaction(client.zip),
                cPais: "1058",
                xPais: "Brasil",
            };
        }

        mountOrderLinesTag() {
            const {order} = this;
            const orderLines = order.get_orderlines();
            const detTags = [];

            for (let i = 0; i < orderLines.length; i++) {
                const line = orderLines[i];
                const detTag = {
                    "@nItem": i + 1,
                    prod: this.mountProductTag(line),
                    imposto: {
                        ICMS: this.mountICMSTag(line),
                        PIS: this.mountPISTag(line),
                        COFINS: this.mountCofinsTag(line),
                    },
                };
                detTags.push(detTag);
            }

            return detTags;
        }

        mountProductTag(line) {
            const product = line.product;
            const taxes = this.pos.fiscal_map_by_template_id[product.product_tmpl_id];
            return {
                cProd: line.product.default_code,
                cEAN: "SEM GTIN",
                xProd: line.product.display_name,
                NCM: taxes.ncm_code,
                CFOP: taxes.cfop_code,
                uCom: this.getUOMCode(product).code,
                qCom: line.quantity.toFixed(4),
                vUnCom: line.product.lst_price.toFixed(10),
                vProd: (line.quantity * line.product.lst_price).toFixed(2),
                cEANTrib: "SEM GTIN",
                uTrib: this.getUOMCode(product).code,
                qTrib: line.quantity.toFixed(4),
                vUnTrib: line.product.lst_price.toFixed(10),
                indTot: "1",
            };
        }

        getUOMCode(product) {
            return this.pos.uoms.find((uom) => {
                if (uom.id === product.uom_id[0]) {
                    return uom.code;
                }
            });
        }

        mountICMSTag(line) {
            const product = line.product;
            const taxes = this.pos.fiscal_map_by_template_id[product.product_tmpl_id];
            const {icms_cst_code, icms_origin} = taxes;

            switch (icms_cst_code) {
                case "00":
                    return {
                        ICMS00: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBC: "0",
                            vBC: taxes.icms_base.toFixed(2),
                            pICMS: taxes.icms_percent.toFixed(4),
                            vICMS: taxes.icms_value.toFixed(2),
                        },
                    };
                case "10":
                    return {
                        ICMS10: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBC: "0",
                            vBC: taxes.icms_base.toFixed(2),
                            pICMS: taxes.icms_percent.toFixed(4),
                            vICMS: taxes.icms_value.toFixed(2),
                        },
                    };
                case "20":
                    return {
                        ICMS20: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBC: "0",
                            pRedBC: taxes.icms_reduction.toFixed(4),
                            vBC: taxes.icms_base.toFixed(2),
                            pICMS: taxes.icms_percent.toFixed(4),
                            vICMS: taxes.icms_value.toFixed(2),
                        },
                    };
                case "30":
                    return {
                        ICMS30: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBCST: "0",
                            pMVAST: taxes.icmsst_mva_percent.toFixed(4),
                            pRedBCST: taxes.icmsst_reduction.toFixed(4),
                            vBCST: taxes.icmsst_base.toFixed(2),
                            pICMSST: taxes.icmsst_percent.toFixed(4),
                            vICMSST: taxes.icmsst_value.toFixed(2),
                        },
                    };
                case "51":
                    return {
                        ICMS51: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBC: "0",
                            pRedBC: taxes.icms_reduction.toFixed(4),
                            vBC: taxes.icms_base.toFixed(2),
                            pICMS: taxes.icms_percent.toFixed(4),
                            vICMSOp: "0.00", // FIXME
                            pDif: "0.0000", // FIXME
                            vICMSDif: "0.00", // FIXME
                            vICMS: taxes.icms_value.toFixed(2),
                        },
                    };
                case "60":
                    return {
                        ICMS60: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            vBCSTRet: taxes.icmsst_wh_base.toFixed(2),
                            pST: (taxes.icmsst_percent + taxes.icms_percent).toFixed(4),
                            vICMSSubstituto: taxes.icms_substitute.toFixed(2),
                            vICMSSTRet: taxes.icmsst_wh_value.toFixed(2),
                            vBCFCPSTRet: taxes.icmsfcp_base_wh.toFixed(2),
                            pFCPSTRet: taxes.icmsst_percent.toFixed(4),
                            vFCPSTRet: taxes.icmsst_value.toFixed(2),
                            pRedBCEfet: taxes.icms_effective_reduction.toFixed(4),
                            vBCEfet: taxes.icms_effective_base.toFixed(2),
                            pICMSEfet: taxes.icms_effective_percent.toFixed(4),
                            vICMSEfet: taxes.icms_effective_value.toFixed(2),
                        },
                    };
                case "70":
                    return {
                        ICMS70: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                            modBC: "0",
                            pRedBC: taxes.icms_reduction.toFixed(4),
                            vBC: taxes.icms_base.toFixed(2),
                            pICMS: taxes.icms_percent.toFixed(4),
                            vICMS: taxes.icms_value.toFixed(2),
                        },
                    };
                case "90":
                    return {
                        ICMS90: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                        },
                    };
                default:
                    return {
                        ICMS40: {
                            orig: icms_origin,
                            CST: icms_cst_code,
                        },
                    };
            }
        }

        mountPISTag(line) {
            const product = line.product;
            const taxes = this.pos.fiscal_map_by_template_id[product.product_tmpl_id];
            const {pis_cst_code, pis_base, pis_percent, pis_value} = taxes;

            if (["01", "02"].includes(pis_cst_code)) {
                return {
                    PISAliq: {
                        CST: pis_cst_code,
                        vBC: pis_base.toFixed(2),
                        pPIS: pis_percent.toFixed(4),
                        vPIS: pis_value.toFixed(2),
                    },
                };
            }

            if (["04", "06", "07", "08", "09"].includes(pis_cst_code)) {
                return {
                    PISNT: {
                        CST: pis_cst_code,
                    },
                };
            }
        }

        mountCofinsTag(line) {
            const product = line.product;
            const taxes = this.pos.fiscal_map_by_template_id[product.product_tmpl_id];
            const {cofins_cst_code, cofins_base, cofins_percent, cofins_value} = taxes;

            if (["01", "02"].includes(cofins_cst_code)) {
                return {
                    COFINSAliq: {
                        CST: cofins_cst_code,
                        vBC: cofins_base.toFixed(2),
                        pCOFINS: cofins_percent.toFixed(4),
                        vCOFINS: cofins_value.toFixed(2),
                    },
                };
            }

            if (["04", "05", "06", "07", "08", "09"].includes(cofins_cst_code)) {
                return {
                    COFINSNT: {
                        CST: cofins_cst_code,
                    },
                };
            }
        }

        mountTotalsTag() {
            return {
                ICMSTot: {
                    vBC: this.order.get_total_icms_base().toFixed(2),
                    vICMS: this.order.get_total_icms().toFixed(2),
                    vICMSDeson: "0.00",
                    vFCP: "0.00",
                    vBCST: "0.00",
                    vST: "0.00",
                    vFCPST: "0.00",
                    vFCPSTRet: "0.00",
                    vProd: this.order.get_total_with_tax().toFixed(2),
                    vFrete: "0.00",
                    vSeg: "0.00",
                    vDesc: this.order.get_total_discount().toFixed(2),
                    vII: "0.00",
                    vIPI: "0.00",
                    vIPIDevol: "0.00",
                    vPIS: this.order.get_total_pis().toFixed(2),
                    vCOFINS: this.order.get_total_cofins().toFixed(2),
                    vOutro: "0.00",
                    vNF: this.order.get_total_with_tax().toFixed(2),
                },
            };
        }

        mountTransportTag() {
            return {
                modFrete: "9",
            };
        }

        mountPaymentTag(paymentline) {
            const paymentModes = this.pos.paymentModes;
            const paymentMethod = paymentline.payment_method;
            const paymentLineMode = paymentModes.find(
                (mode) => mode.id === paymentMethod.payment_mode_id[0]
            );
            if (paymentLineMode.fiscal_payment_mode === "01") {
                return {
                    indPag: "0",
                    tPag: paymentLineMode.fiscal_payment_mode,
                    vPag: paymentline.amount.toFixed(2),
                };
            } else if (paymentLineMode.fiscal_payment_mode === "99") {
                return {
                    indPag: "0",
                    tPag: paymentLineMode.fiscal_payment_mode,
                    xPag: "Outros",
                    vPag: paymentline.amount.toFixed(2),
                };
            }
            return {
                indPag: "0",
                tPag: paymentLineMode.fiscal_payment_mode,
                vPag: paymentline.amount.toFixed(2),
                card: {
                    tpIntegra: "1",
                    CNPJ: paymentline.terminal_transaction_network_cnpj.replace(
                        /([^\w ]|_)/g,
                        ""
                    ),
                    tBand: paymentline.terminal_transaction_administrator,
                    cAut: paymentline.transaction_id,
                },
            };
        }

        async generateQRCodeText() {
            const date = new Date(this.date);

            const diaEmissao = date.getDate().toString().padStart(2, "0");
            const ambiente = this.pos.config.nfce_environment;
            const cscToken = this.pos.company.nfce_csc_token;
            const cscCode = this.pos.company.nfce_csc_code;
            const chaveNFCe = this.chaveEdoc.generatedChave;
            const totalNFCe = this.order.get_total_with_tax().toFixed(2);
            const digestValue = this.generateBase64HashFromXML();

            // eslint-disable-next-line no-undef
            const sha1Hash = Sha1.hash;
            const hexStr = this.toHexString(digestValue);

            const preQRCodeWithoutCSC = `${chaveNFCe}|2|${ambiente}|${diaEmissao}|${totalNFCe}|${hexStr}|${cscToken}`;
            const preQRCode = `${preQRCodeWithoutCSC}${cscCode}`;
            const qrCodeValue = `${preQRCodeWithoutCSC}|${sha1Hash(
                preQRCode,
                "hex"
            ).toUpperCase()}`;

            return `${
                ESTADO_QRCODE[
                    ESTADOS_IBGE[
                        BRAZILIAN_STATES_IBGE_CODE_MAP[this.pos.company.state_id[1]]
                    ][0]
                ][ambiente]
            }${qrCodeValue}`;
        }

        toHexString(str) {
            const base64Str = btoa(str);
            const bytes = new Uint8Array(
                [...atob(base64Str)].map((char) => char.charCodeAt(0))
            );
            return bytes.reduce(
                (acc, byte) => acc + ("0" + byte.toString(16)).slice(-2),
                ""
            );
        }

        generateBase64HashFromXML() {
            let xmlString = this.getXMLMountedString();
            xmlString = xmlString.replace('<?xml version="1.0"?>', "");
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlString, "text/xml");
            const canonicalized = new XMLSerializer()
                .serializeToString(xmlDoc.documentElement)
                .replace(/\s{2,}/g, " ");

            // eslint-disable-next-line no-undef
            const hash = Sha1.hash(canonicalized, "hex");

            const hexToBytes = (hex) =>
                new Uint8Array(hex.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)));
            const bytesToString = (bytes) => String.fromCharCode.apply(null, bytes);
            const base64Encode = (str) => btoa(str);

            const arrayBuffer = hexToBytes(hash).buffer;
            const string = bytesToString(new Uint8Array(arrayBuffer));
            const base64Value = base64Encode(string);

            return base64Value;
        }

        getXMLMountedString() {
            return this.createNFeXML().end({prettyPrint: false});
        }
    }

    return {
        NFeXML: NFeXML,
        BRAZILIAN_STATES_IBGE_CODE_MAP: BRAZILIAN_STATES_IBGE_CODE_MAP,
    };
});
