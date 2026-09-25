"""
app.py - Interface Principal do Usuário (Streamlit)
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

import io
import re
from datetime import date, datetime, timedelta, time
from typing import Optional, Any

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Módulos Locais do Sistema (Modo Produção)
import database as db
import metrics as met

# Configuração da Página Streamlit
st.set_page_config(
    page_title="Gestão de Demandas Jurídicas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# ESCUDO NATIVO DE DOM / REACT (EXECUÇÃO IMEDIATA NA JANELA PRINCIPAL)
# Previne o erro 'NotFoundError: Falha ao executar removeChild em Node'
# decorrente de tradutores automáticos do navegador (Google Translate / Microsoft Edge).
# ==============================================================================
DOM_SHIELD_JS = """
<script>
    (function() {
        try {
            var w = window;
            if (w.__react_dom_shield_active__) return;
            w.__react_dom_shield_active__ = true;

            // 1. Forçar idioma Português e desativar auto-tradução no documento raiz
            var enforceNoTranslate = function() {
                var d = document;
                if (d.documentElement) {
                    d.documentElement.setAttribute('translate', 'no');
                    d.documentElement.setAttribute('lang', 'pt-BR');
                    d.documentElement.classList.add('notranslate');
                }
                if (d.body) {
                    d.body.setAttribute('translate', 'no');
                    d.body.classList.add('notranslate');
                }
            };
            enforceNoTranslate();
            if (w.MutationObserver) {
                var obs = new MutationObserver(function() {
                    if (document.documentElement && document.documentElement.getAttribute('translate') !== 'no') {
                        enforceNoTranslate();
                    }
                });
                obs.observe(document.documentElement, { attributes: true, attributeFilter: ['translate', 'lang', 'class'] });
            }

            var d = document;
            if (!d.querySelector('meta[name="google"][content="notranslate"]')) {
                var m1 = d.createElement('meta');
                m1.name = 'google';
                m1.content = 'notranslate';
                d.head.appendChild(m1);
                var m2 = d.createElement('meta');
                m2.name = 'googlebot';
                m2.content = 'notranslate';
                d.head.appendChild(m2);
            }

            // 2. Patch essencial em Node.prototype.removeChild
            if (w.Node && w.Node.prototype) {
                var origRC = w.Node.prototype.removeChild;
                w.Node.prototype.removeChild = function(child) {
                    try {
                        return origRC.call(this, child);
                    } catch (err) {
                        if (err.name === 'NotFoundError' || 
                            (err.message && (
                                err.message.indexOf('removeChild') !== -1 || 
                                err.message.indexOf('not a child') !== -1 || 
                                err.message.indexOf('não é filho') !== -1 ||
                                err.message.indexOf('removido') !== -1
                            ))) {
                            if (child && child.parentNode && child.parentNode !== this) {
                                try { return child.parentNode.removeChild(child); } catch(ex) { return child; }
                            }
                            return child;
                        }
                        throw err;
                    }
                };

                // 3. Patch essencial em Node.prototype.insertBefore
                var origIB = w.Node.prototype.insertBefore;
                w.Node.prototype.insertBefore = function(newNode, referenceNode) {
                    try {
                        return origIB.call(this, newNode, referenceNode);
                    } catch (err) {
                        if (err.name === 'NotFoundError' || 
                            (err.message && (
                                err.message.indexOf('insertBefore') !== -1 || 
                                err.message.indexOf('not a child') !== -1 || 
                                err.message.indexOf('não é filho') !== -1 ||
                                err.message.indexOf('inserido') !== -1
                            ))) {
                            try { return this.appendChild(newNode); } catch(ex) { return newNode; }
                        }
                        throw err;
                    }
                };

                // 4. Patch essencial em Node.prototype.replaceChild
                var origRepC = w.Node.prototype.replaceChild;
                w.Node.prototype.replaceChild = function(newChild, oldChild) {
                    try {
                        return origRepC.call(this, newChild, oldChild);
                    } catch (err) {
                        if (err.name === 'NotFoundError' || 
                            (err.message && (
                                err.message.indexOf('replaceChild') !== -1 || 
                                err.message.indexOf('not a child') !== -1 || 
                                err.message.indexOf('não é filho') !== -1 ||
                                err.message.indexOf('substituído') !== -1
                            ))) {
                            try { return this.appendChild(newChild); } catch(ex) { return newChild; }
                        }
                        throw err;
                    }
                };
            }

            // 5. Captura global de exceções na fase de disparo (Capture Phase)
            w.addEventListener('error', function(event) {
                var msg = (event && (event.message || (event.error && event.error.message))) || '';
                if (typeof msg === 'string' && (
                    msg.indexOf('removeChild') !== -1 ||
                    msg.indexOf('not a child') !== -1 ||
                    msg.indexOf('não é filho') !== -1 ||
                    msg.indexOf('insertBefore') !== -1 ||
                    msg.indexOf('replaceChild') !== -1
                )) {
                    if (event.preventDefault) event.preventDefault();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                    if (event.stopPropagation) event.stopPropagation();
                    return true;
                }
            }, true);

            w.addEventListener('unhandledrejection', function(event) {
                var reason = event && event.reason;
                var msg = (reason && (reason.message || String(reason))) || '';
                if (typeof msg === 'string' && (
                    msg.indexOf('removeChild') !== -1 ||
                    msg.indexOf('not a child') !== -1 ||
                    msg.indexOf('não é filho') !== -1
                )) {
                    if (event.preventDefault) event.preventDefault();
                    return true;
                }
            }, true);
        } catch(e) {}
    })();
</script>
"""

if hasattr(st, "html"):
    st.html(DOM_SHIELD_JS, unsafe_allow_javascript=True)

def safe_rerun():
    """Função utilitária para rerun compatível com todas as versões do Streamlit."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def safe_count_aportes() -> int:
    """Contagem segura de aportes diários com fallback defensivo."""
    if hasattr(db, "get_total_aportes_count"):
        try:
            return db.get_total_aportes_count()
        except Exception:
            pass
    try:
        if hasattr(db, "get_db_session") and hasattr(db, "AporteDiario"):
            with db.get_db_session() as session:
                return session.query(db.AporteDiario).count()
    except Exception:
        pass
    return 0

def safe_get_df_aportes_diarios(data_inicio=None, data_fim=None) -> pd.DataFrame:
    """Busca segura do DataFrame de demandas que aportam por data."""
    if hasattr(db, "get_df_aportes_diarios"):
        try:
            return db.get_df_aportes_diarios(data_inicio=data_inicio, data_fim=data_fim)
        except Exception as ex:
            print(f"[ERRO safe_get_df_aportes_diarios]: {ex}")
    return pd.DataFrame()

def safe_add_aporte_diario(data_aporte, quantidade_subsidios, quantidade_subsidios_urgente,
                           quantidade_obrigacao_fazer, quantidade_obrigacao_fazer_urgente,
                           observacoes="") -> int:
    """Adiciona aporte diário com fallback defensivo caso database.py não esteja sincronizado."""
    if hasattr(db, "add_aporte_diario"):
        return db.add_aporte_diario(
            data_aporte=data_aporte,
            quantidade_subsidios=quantidade_subsidios,
            quantidade_subsidios_urgente=quantidade_subsidios_urgente,
            quantidade_obrigacao_fazer=quantidade_obrigacao_fazer,
            quantidade_obrigacao_fazer_urgente=quantidade_obrigacao_fazer_urgente,
            observacoes=observacoes,
        )
    if hasattr(db, "get_db_session") and hasattr(db, "AporteDiario"):
        with db.get_db_session() as session:
            obj = db.AporteDiario(
                data_aporte=data_aporte,
                quantidade_subsidios=quantidade_subsidios,
                quantidade_subsidios_urgente=quantidade_subsidios_urgente,
                quantidade_obrigacao_fazer=quantidade_obrigacao_fazer,
                quantidade_obrigacao_fazer_urgente=quantidade_obrigacao_fazer_urgente,
                observacoes=observacoes,
            )
            session.add(obj)
            session.commit()
            return obj.id
    raise RuntimeError("O módulo 'database.py' no servidor precisa ser atualizado para incluir suporte a aportes diários.")

def safe_calcular_kpis_aportes(df: pd.DataFrame) -> dict:
    """Cálculo seguro de KPIs dos quantitativos diários que aportam, com fallback robusto."""
    if hasattr(met, "calcular_kpis_aportes"):
        try:
            return met.calcular_kpis_aportes(df)
        except Exception as ex:
            print(f"[ERRO met.calcular_kpis_aportes]: {ex}")

    empty_result = {
        "total_subsidios": 0,
        "total_subsidios_urgentes": 0,
        "subsidios_comuns": 0,
        "total_obrigacao_fazer": 0,
        "total_obrigacao_fazer_urgentes": 0,
        "obrigacao_fazer_comuns": 0,
        "total_geral_aportado": 0,
        "total_urgentes": 0,
        "total_regulares": 0,
        "taxa_urgencia_pct": 0.0,
        "dias_com_aporte": 0,
        "media_diaria_aporte": 0.0,
        "maior_aporte_dia_volume": 0,
        "maior_aporte_dia_data": None,
    }
    if df is None or df.empty:
        return empty_result

    try:
        df_calc = df.copy()
        col_s = pd.to_numeric(df_calc.get("quantidade_subsidios", 0), errors="coerce").fillna(0)
        col_su = pd.to_numeric(df_calc.get("quantidade_subsidios_urgente", 0), errors="coerce").fillna(0)
        col_o = pd.to_numeric(df_calc.get("quantidade_obrigacao_fazer", 0), errors="coerce").fillna(0)
        col_ou = pd.to_numeric(df_calc.get("quantidade_obrigacao_fazer_urgente", 0), errors="coerce").fillna(0)

        tot_sub = int(col_s.sum())
        tot_sub_urg = int(col_su.sum())
        sub_comum = max(0, tot_sub - tot_sub_urg)

        tot_obrig = int(col_o.sum())
        tot_obrig_urg = int(col_ou.sum())
        obrig_comum = max(0, tot_obrig - tot_obrig_urg)

        total_geral = tot_sub + tot_obrig
        total_urgentes = tot_sub_urg + tot_obrig_urg
        total_regulares = sub_comum + obrig_comum

        taxa_urg = round((total_urgentes / total_geral) * 100, 1) if total_geral > 0 else 0.0

        if "data_aporte" in df_calc.columns:
            dias_unicos = df_calc["data_aporte"].nunique()
        else:
            dias_unicos = len(df_calc)

        media_diaria = round(total_geral / max(1, dias_unicos), 1)

        maior_vol = 0
        maior_data = None
        if "data_aporte" in df_calc.columns and total_geral > 0:
            df_calc["tot_dia_calc"] = col_s + col_o
            agrup_dia = df_calc.groupby("data_aporte")["tot_dia_calc"].sum()
            if not agrup_dia.empty:
                maior_vol = int(agrup_dia.max())
                maior_data = agrup_dia.idxmax()

        return {
            "total_subsidios": tot_sub,
            "total_subsidios_urgentes": tot_sub_urg,
            "subsidios_comuns": sub_comum,
            "total_obrigacao_fazer": tot_obrig,
            "total_obrigacao_fazer_urgentes": tot_obrig_urg,
            "obrigacao_fazer_comuns": obrig_comum,
            "total_geral_aportado": total_geral,
            "total_urgentes": total_urgentes,
            "total_regulares": total_regulares,
            "taxa_urgencia_pct": taxa_urg,
            "dias_com_aporte": dias_unicos,
            "media_diaria_aporte": media_diaria,
            "maior_aporte_dia_volume": maior_vol,
            "maior_aporte_dia_data": maior_data,
        }
    except Exception as ex:
        print(f"[ERRO safe_calcular_kpis_aportes]: {ex}")
        return empty_result

def safe_gerar_serie_diaria_aportes(df_aportes: pd.DataFrame) -> pd.DataFrame:
    """Gera série diária de demandas que aportam com fallback seguro."""
    if hasattr(met, "gerar_serie_diaria_aportes"):
        try:
            return met.gerar_serie_diaria_aportes(df_aportes)
        except Exception as ex:
            print(f"[ERRO met.gerar_serie_diaria_aportes]: {ex}")

    colunas_vazias = [
        "data", "data_str", "subsidios_comum", "subsidios_urgente", "total_subsidios",
        "obrigacao_comum", "obrigacao_urgente", "total_obrigacao", "total_dia",
        "total_urgente_dia", "taxa_urgencia_dia"
    ]
    if df_aportes is None or df_aportes.empty:
        return pd.DataFrame(columns=colunas_vazias)

    try:
        df_temp = df_aportes.copy()
        if "data_aporte" not in df_temp.columns:
            return pd.DataFrame(columns=colunas_vazias)

        def _to_date(val):
            if hasattr(met, "converter_para_date"):
                return met.converter_para_date(val)
            if pd.isna(val) or val is None or str(val).strip() in ("", "NaT", "None"):
                return None
            if isinstance(val, date) and not isinstance(val, datetime):
                return val
            if isinstance(val, (pd.Timestamp, datetime)):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val.split()[0], "%Y-%m-%d").date()
                except Exception:
                    try:
                        return datetime.strptime(val.split()[0], "%d/%m/%Y").date()
                    except Exception:
                        return None
            return None

        df_temp["dt"] = df_temp["data_aporte"].apply(_to_date)
        df_temp = df_temp[df_temp["dt"].notna()]
        if df_temp.empty:
            return pd.DataFrame(columns=colunas_vazias)

        for col in ["quantidade_subsidios", "quantidade_subsidios_urgente", "quantidade_obrigacao_fazer", "quantidade_obrigacao_fazer_urgente"]:
            if col not in df_temp.columns:
                df_temp[col] = 0
            else:
                df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce").fillna(0).astype(int)

        agrupado = df_temp.groupby("dt").agg(
            quantidade_subsidios=("quantidade_subsidios", "sum"),
            quantidade_subsidios_urgente=("quantidade_subsidios_urgente", "sum"),
            quantidade_obrigacao_fazer=("quantidade_obrigacao_fazer", "sum"),
            quantidade_obrigacao_fazer_urgente=("quantidade_obrigacao_fazer_urgente", "sum"),
        ).reset_index().rename(columns={"dt": "data"})

        agrupado["subsidios_comum"] = (agrupado["quantidade_subsidios"] - agrupado["quantidade_subsidios_urgente"]).clip(lower=0)
        agrupado["subsidios_urgente"] = agrupado["quantidade_subsidios_urgente"]
        agrupado["total_subsidios"] = agrupado["quantidade_subsidios"]

        agrupado["obrigacao_comum"] = (agrupado["quantidade_obrigacao_fazer"] - agrupado["quantidade_obrigacao_fazer_urgente"]).clip(lower=0)
        agrupado["obrigacao_urgente"] = agrupado["quantidade_obrigacao_fazer_urgente"]
        agrupado["total_obrigacao"] = agrupado["quantidade_obrigacao_fazer"]

        agrupado["total_dia"] = agrupado["total_subsidios"] + agrupado["total_obrigacao"]
        agrupado["total_urgente_dia"] = agrupado["subsidios_urgente"] + agrupado["obrigacao_urgente"]
        agrupado["taxa_urgencia_dia"] = np.where(
            agrupado["total_dia"] > 0,
            np.round((agrupado["total_urgente_dia"] / agrupado["total_dia"]) * 100, 1),
            0.0
        )
        agrupado = agrupado.sort_values("data").reset_index(drop=True)
        agrupado["data_str"] = agrupado["data"].apply(lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d))
        return agrupado
    except Exception as ex:
        print(f"[ERRO safe_gerar_serie_diaria_aportes]: {ex}")
        return pd.DataFrame(columns=colunas_vazias)

def safe_gerar_serie_mensal_aportes(df_aportes: pd.DataFrame) -> pd.DataFrame:
    """Gera série mensal de demandas que aportam com fallback seguro."""
    if hasattr(met, "gerar_serie_mensal_aportes"):
        try:
            return met.gerar_serie_mensal_aportes(df_aportes)
        except Exception as ex:
            print(f"[ERRO met.gerar_serie_mensal_aportes]: {ex}")

    colunas_vazias = [
        "ano_mes", "rotulo_mes", "subsidios_comum", "subsidios_urgente", "total_subsidios",
        "obrigacao_comum", "obrigacao_urgente", "total_obrigacao", "total_mes",
        "total_urgente_mes", "taxa_urgencia_mes", "dias_registrados", "media_diaria_mes"
    ]
    if df_aportes is None or df_aportes.empty:
        return pd.DataFrame(columns=colunas_vazias)

    try:
        df_temp = df_aportes.copy()
        if "data_aporte" not in df_temp.columns:
            return pd.DataFrame(columns=colunas_vazias)

        def _to_date(val):
            if hasattr(met, "converter_para_date"):
                return met.converter_para_date(val)
            if pd.isna(val) or val is None or str(val).strip() in ("", "NaT", "None"):
                return None
            if isinstance(val, date) and not isinstance(val, datetime):
                return val
            if isinstance(val, (pd.Timestamp, datetime)):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val.split()[0], "%Y-%m-%d").date()
                except Exception:
                    try:
                        return datetime.strptime(val.split()[0], "%d/%m/%Y").date()
                    except Exception:
                        return None
            return None

        df_temp["dt"] = df_temp["data_aporte"].apply(_to_date)
        df_temp = df_temp[df_temp["dt"].notna()]
        if df_temp.empty:
            return pd.DataFrame(columns=colunas_vazias)

        for col in ["quantidade_subsidios", "quantidade_subsidios_urgente", "quantidade_obrigacao_fazer", "quantidade_obrigacao_fazer_urgente"]:
            if col not in df_temp.columns:
                df_temp[col] = 0
            else:
                df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce").fillna(0).astype(int)

        df_temp["ano_mes"] = df_temp["dt"].apply(lambda d: d.strftime("%Y-%m"))
        meses_pt = {
            "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
            "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
        }
        grupos_mes = []
        for am, grp in df_temp.groupby("ano_mes"):
            sub_tot = int(grp["quantidade_subsidios"].sum())
            sub_urg = int(grp["quantidade_subsidios_urgente"].sum())
            sub_com = max(0, sub_tot - sub_urg)

            obrig_tot = int(grp["quantidade_obrigacao_fazer"].sum())
            obrig_urg = int(grp["quantidade_obrigacao_fazer_urgente"].sum())
            obrig_com = max(0, obrig_tot - obrig_urg)

            tot_mes = sub_tot + obrig_tot
            urg_mes = sub_urg + obrig_urg
            tx_urg = round((urg_mes / tot_mes) * 100, 1) if tot_mes > 0 else 0.0

            dias_com_reg = grp["dt"].nunique()
            media_dia = round(tot_mes / max(1, dias_com_reg), 1)

            parts = str(am).split("-")
            rotulo = f"{meses_pt.get(parts[1], parts[1])}/{parts[0]}" if len(parts) == 2 else str(am)

            grupos_mes.append({
                "ano_mes": am,
                "rotulo_mes": rotulo,
                "subsidios_comum": sub_com,
                "subsidios_urgente": sub_urg,
                "total_subsidios": sub_tot,
                "obrigacao_comum": obrig_com,
                "obrigacao_urgente": obrig_urg,
                "total_obrigacao": obrig_tot,
                "total_mes": tot_mes,
                "total_urgente_mes": urg_mes,
                "taxa_urgencia_mes": tx_urg,
                "dias_registrados": dias_com_reg,
                "media_diaria_mes": media_dia,
            })

        df_mensal = pd.DataFrame(grupos_mes)
        if not df_mensal.empty:
            df_mensal = df_mensal.sort_values("ano_mes").reset_index(drop=True)
        return df_mensal
    except Exception as ex:
        print(f"[ERRO safe_gerar_serie_mensal_aportes]: {ex}")
        return pd.DataFrame(columns=colunas_vazias)

def safe_count_produtividade() -> int:
    """Contagem segura de produtividade operacional com fallback defensivo."""
    if hasattr(db, "get_total_produtividade_count"):
        try:
            return db.get_total_produtividade_count()
        except Exception:
            pass
    try:
        if hasattr(db, "get_db_session") and hasattr(db, "ProdutividadeOperacional"):
            with db.get_db_session() as session:
                return session.query(db.ProdutividadeOperacional).count()
    except Exception:
        pass
    return 0

def safe_count_mandamentais() -> int:
    """Contagem segura de ações mandamentais com fallback defensivo."""
    if hasattr(db, "get_total_mandamentais_count"):
        try:
            return db.get_total_mandamentais_count()
        except Exception:
            pass
    try:
        if hasattr(db, "get_db_session") and hasattr(db, "AcaoMandamental"):
            with db.get_db_session() as session:
                return session.query(db.AcaoMandamental).count()
    except Exception:
        pass
    return 0

def safe_count_analistas() -> int:
    """Contagem segura de analistas com fallback defensivo."""
    if hasattr(db, "get_total_analistas_count"):
        try:
            return db.get_total_analistas_count()
        except Exception:
            pass
    try:
        if hasattr(db, "get_db_session") and hasattr(db, "Analista"):
            with db.get_db_session() as session:
                return session.query(db.Analista).count()
    except Exception:
        pass
    return 0

# Inicialização e Manutenção Automática da Base de Produção
@st.cache_resource(show_spinner=False)
def bootstrap_producao():
    """
    Garante inicialização do banco SQLite em modo de produção.
    Elimina dados fictícios de demonstração de versões anteriores e prepara as tabelas
    para inclusão de novos registros reais pelos usuários.
    """
    try:
        if hasattr(db, "init_db"):
            db.init_db()
        if hasattr(db, "garantir_limpeza_producao"):
            db.garantir_limpeza_producao()
        elif hasattr(db, "get_db_session"):
            with db.get_db_session() as session:
                if hasattr(db, "ConfiguracaoSistema"):
                    flag = session.query(db.ConfiguracaoSistema).filter(db.ConfiguracaoSistema.chave == "modo_producao_ativo").first()
                    if not (flag and flag.valor == "sim"):
                        if hasattr(db, "AporteDiario"):
                            session.query(db.AporteDiario).delete()
                        if hasattr(db, "ProdutividadeOperacional"):
                            session.query(db.ProdutividadeOperacional).delete()
                        if hasattr(db, "DemandaOperacional"):
                            session.query(db.DemandaOperacional).delete()
                        if hasattr(db, "AcaoMandamental"):
                            session.query(db.AcaoMandamental).delete()
                        if hasattr(db, "Analista"):
                            session.query(db.Analista).delete()
                        if not flag:
                            session.add(db.ConfiguracaoSistema(chave="modo_producao_ativo", valor="sim"))
                        else:
                            flag.valor = "sim"
        return True
    except Exception as init_err:
        print(f"[BOOTSTRAP] Informação de inicialização do banco: {init_err}")
        return False

bootstrap_producao()

# Estilização CSS de Alto Contraste e Proteção contra Tradução
st.markdown(
    """
    <meta name="google" content="notranslate" />
    <style>
        /* Oculta iframe de suporte técnico do DOM Shield */
        iframe[title*="st.iframe"] {
            display: none !important;
            height: 0px !important;
            width: 0px !important;
            border: none !important;
        }
        /* Bloqueio de tradução automática que quebra nós do React DOM */
        html, body, div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"], section.main, .notranslate, [translate="no"] {
            translate: no !important;
        }
        /* Variáveis de cores dinâmicas adaptativas ao tema */
        :root {
            --app-header-color: #38BDF8;
            --app-sub-color: #94A3B8;
            --app-metric-color: #F8FAFC;
        }

        /* Estilização de Cabeçalho com contraste impecável */
        .main-header {
            font-size: 2.25rem !important;
            font-weight: 800 !important;
            color: #38BDF8 !important;
            margin-bottom: 0.25rem;
            letter-spacing: -0.02em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        .sub-header {
            font-size: 1.05rem !important;
            color: var(--text-color, #94A3B8) !important;
            opacity: 0.9;
            margin-bottom: 1.6rem;
            line-height: 1.5;
        }

        /* Cartões de Métricas nativos: design executivo e desbloqueio total de truncamento */
        div[data-testid="stMetric"] {
            background-color: #111827 !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-radius: 10px !important;
            padding: 1rem 1.25rem !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
            overflow: visible !important;
            min-height: 125px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            border-color: rgba(56, 189, 248, 0.6) !important;
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.15) !important;
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] *,
        div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] span {
            font-size: 0.96rem !important;
            font-weight: 700 !important;
            color: #94A3B8 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            line-height: 1.35 !important;
            margin-bottom: 0.25rem !important;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] *,
        div[data-testid="stMetricValue"] div {
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            color: #F8FAFC !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.2 !important;
            margin: 0.2rem 0 !important;
        }
        div[data-testid="stMetricDelta"],
        div[data-testid="stMetricDelta"] *,
        div[data-testid="stMetricDelta"] div,
        div[data-testid="stMetricDelta"] span {
            font-size: 0.90rem !important;
            font-weight: 600 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            line-height: 1.35 !important;
        }
        div[data-testid="stMetricDelta"] svg {
            flex-shrink: 0 !important;
            margin-right: 0.25rem !important;
        }

        /* Caixa de Alerta Crítico em Alto Contraste */
        .alerta-critico-box {
            background-color: rgba(220, 38, 38, 0.20) !important;
            border: 1px solid rgba(239, 68, 68, 0.5) !important;
            border-left: 6px solid #EF4444 !important;
            padding: 1.1rem 1.4rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.15);
        }
        .alerta-critico-titulo {
            font-weight: 800 !important;
            color: #FCA5A5 !important;
            font-size: 1.15rem !important;
            margin-bottom: 0.35rem;
            letter-spacing: 0.01em;
        }
        .alerta-critico-texto {
            color: #FEE2E2 !important;
            font-size: 0.95rem !important;
            line-height: 1.45;
        }

        /* Estilo dos formulários e abas */
        div[data-testid="stForm"] {
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 8px;
            padding: 1.5rem;
            background-color: rgba(30, 41, 59, 0.3) !important;
        }

        /* Painéis e Caixas de Gráficos Delimitados */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827 !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-radius: 10px !important;
            padding: 1.2rem 1.25rem !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 1.3rem !important;
            overflow: visible !important;
        }
        div[data-testid="stPlotlyChart"] {
            width: 100% !important;
            overflow: visible !important;
        }
        .panel-header-title {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            color: #38BDF8 !important;
            margin-bottom: 0.25rem !important;
            display: flex;
            align-items: center;
            gap: 0.45rem;
            line-height: 1.35 !important;
        }
        .panel-header-desc {
            font-size: 0.90rem !important;
            color: #94A3B8 !important;
            margin-bottom: 0.75rem !important;
            line-height: 1.45 !important;
        }
        .info-pill {
            background-color: rgba(56, 189, 248, 0.12) !important;
            border: 1px solid rgba(56, 189, 248, 0.35) !important;
            color: #F0F9FF !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: 8px !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            text-align: center !important;
            margin-top: 0.4rem !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
        }
        .info-pill b {
            color: #38BDF8 !important;
        }
        .info-pill-success {
            background-color: rgba(16, 185, 129, 0.14) !important;
            border: 1px solid rgba(16, 185, 129, 0.4) !important;
            color: #ECFDF5 !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: 8px !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            text-align: center !important;
            margin-top: 0.4rem !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
        }
        .info-pill-success b {
            color: #34D399 !important;
        }
        .info-pill-warning {
            background-color: rgba(245, 158, 11, 0.14) !important;
            border: 1px solid rgba(245, 158, 11, 0.4) !important;
            color: #FFFBEB !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: 8px !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            text-align: center !important;
            margin-top: 0.4rem !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
        }
        .info-pill-warning b {
            color: #FBBF24 !important;
        }
        .info-pill-danger {
            background-color: rgba(239, 68, 68, 0.14) !important;
            border: 1px solid rgba(239, 68, 68, 0.4) !important;
            color: #FEF2F2 !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: 8px !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            text-align: center !important;
            margin-top: 0.4rem !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
        }
        .info-pill-danger b {
            color: #F87171 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# BARRA LATERAL (SIDEBAR): FILTROS GLOBAIS
# ==========================================

st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 1.25rem;">
        <img src="https://img.icons8.com/fluency/96/scales.png" width="70" style="display: block; margin: 0 auto 0.6rem auto;" alt="Balança da Justiça" />
        <h3 style="margin: 0; padding: 0; color: #38BDF8; font-size: 1.4rem; font-weight: 700; letter-spacing: -0.01em;">Painel de Pesquisa</h3>
        <p style="margin: 0.35rem 0 0 0; color: #94A3B8; font-size: 0.88rem; font-weight: 500;">Filtros analíticos aplicados em tempo real.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 1. Filtro de Período de Datas
hoje = date.today()
data_padrao_inicio = hoje - timedelta(days=30)
data_padrao_fim = hoje

col_sidebar_d1, col_sidebar_d2 = st.sidebar.columns(2)
with col_sidebar_d1:
    filtro_data_inicio = st.date_input("Data Início", value=data_padrao_inicio, format="DD/MM/YYYY")
with col_sidebar_d2:
    filtro_data_fim = st.date_input("Data Fim", value=data_padrao_fim, format="DD/MM/YYYY")

if filtro_data_inicio > filtro_data_fim:
    st.sidebar.error("A Data Início não pode ser maior que a Data Fim.")
    filtro_data_inicio = data_padrao_inicio

# 2. Carregar Analistas para Filtro
df_analistas = db.get_df_analistas()
opcoes_analistas = {"Todos os Analistas": None}
if not df_analistas.empty:
    for _, row in df_analistas.iterrows():
        opcoes_analistas[f"{row['nome']} ({row['especialidade']})"] = int(row["id"])

analista_selecionado_nome = st.sidebar.selectbox(
    "Filtrar por Analista",
    options=list(opcoes_analistas.keys()),
    index=0,
)
filtro_id_analista = opcoes_analistas[analista_selecionado_nome]

# 3. Filtro de Tipo de Produto / Ação
tipo_produto_filtro = st.sidebar.selectbox(
    "Tipo de Demanda / Produto",
    options=["Todos", "Obrigação de Fazer", "Subsídios", "MS", "HC", "HD"],
    index=0,
)

# 4. Filtro de Urgência
urgencia_filtro = st.sidebar.radio(
    "Prioridade",
    options=["Todas as Demandas", "Apenas Urgentes / Com Multa", "Demandas Normais"],
    index=0,
)
if urgencia_filtro == "Apenas Urgentes / Com Multa":
    apenas_urgentes = True
elif urgencia_filtro == "Demandas Normais":
    apenas_urgentes = False
else:
    apenas_urgentes = None

st.sidebar.divider()
st.sidebar.markdown("#### **Status do Sistema**")
st.sidebar.caption("Ambiente: Produção 🟢 | Base: SQLite WAL")
total_ap_cont = safe_count_aportes()
total_op_cont = safe_count_produtividade()
total_mand_cont = safe_count_mandamentais()
st.sidebar.caption(f"Lançamentos Ativos: **{total_ap_cont}** aportes • **{total_op_cont}** op. • **{total_mand_cont}** mand.")


# ==========================================
# CABEÇALHO PRINCIPAL
# ==========================================

st.markdown('<div class="main-header">⚖️ Gestão Estratégica e Operacional de Demandas Jurídicas</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Controle de distribuição diária, mensuração de produtividade, acompanhamento de prazos e cálculo de KPIs/KGIs corporativos.</div>', unsafe_allow_html=True)

# 4 Abas Principais
tab_distribuicao, tab_gestao, tab_dashboard, tab_automacao = st.tabs([
    "📥 Entrada e Distribuição Diária",
    "⚖️ Gestão e Baixa de Demandas",
    "📊 Painel Gerencial de Produtividade",
    "⚙️ Automação e Integrações",
])


# ==============================================================================
# ABA 1: ENTRADA E DISTRIBUIÇÃO DIÁRIA
# ==============================================================================
with tab_distribuicao:
    st.markdown("### 📥 Registro de Aportes Diários, Produtividade e Ações Jurídicas")
    st.caption("Insira os quantitativos diários de demandas que aportam no setor, registre a produtividade por analista ou cadastre Ações Mandamentais unitárias.")

    tipo_registro = st.radio(
        "Selecione a Modalidade de Cadastro:",
        options=[
            "📥 Aporte Diário de Demandas (Entradas que Aportam no Setor)",
            "📝 Produtividade Diária por Analista (Obrigações e Subsídios)",
            "📜 Ações Mandamentais (MS, HC, HD)",
        ],
        horizontal=True,
    )

    if tipo_registro == "📥 Aporte Diário de Demandas (Entradas que Aportam no Setor)":
        with st.form("form_aporte_diario", clear_on_submit=False):
            st.markdown("#### 📥 Lançamento de Quantitativos Diários que Aportam no Setor")
            st.caption("Registre por data a quantidade de demandas recebidas no setor: Subsídios e Obrigações de Fazer (comuns e urgentes). Esses valores alimentam automaticamente os gráficos diários e mensais.")

            col_ap_dt, col_ap_info = st.columns([1, 2])
            with col_ap_dt:
                dt_aporte_in = st.date_input("Data do Aporte / Entrada", value=hoje, format="DD/MM/YYYY", key="input_dt_aporte")
            with col_ap_info:
                st.info("💡 **Dica de Preenchimento:** Informe a quantidade recebida com prazo comum/regular e a quantidade de caráter urgente. O sistema totaliza e calcula percentuais em tempo real.")

            st.markdown("##### 📊 Quantitativos das Demandas Recebidas:")
            col_ap1, col_ap2 = st.columns(2)
            with col_ap1:
                st.markdown("**📁 Fornecimento de Subsídios**")
                qtd_subs_comum_in = st.number_input(
                    "Quantidade de Subsídios (Regulares / Comuns)",
                    min_value=0, value=0, step=1,
                    help="Subsídios comuns recebidos no expediente com prazo regular",
                    key="input_ap_subs_comum",
                )
                qtd_subs_urg_in = st.number_input(
                    "Quantidade de Subsídios Urgentes",
                    min_value=0, value=0, step=1,
                    help="Subsídios recebidos com prioridade urgente ou tutela de urgência",
                    key="input_ap_subs_urg",
                )

            with col_ap2:
                st.markdown("**⚡ Obrigações de Fazer**")
                qtd_obrig_comum_in = st.number_input(
                    "Quantidade de Obrigação de Fazer (Regulares / Comuns)",
                    min_value=0, value=0, step=1,
                    help="Obrigações de fazer comuns com prazos ordinários",
                    key="input_ap_obrig_comum",
                )
                qtd_obrig_urg_in = st.number_input(
                    "Quantidade de Obrigação de Fazer Urgente",
                    min_value=0, value=0, step=1,
                    help="Obrigações de fazer urgentes ou sob cominação de multa diária (astreintes)",
                    key="input_ap_obrig_urg",
                )

            obs_aporte_in = st.text_area(
                "Observações do Aporte",
                placeholder="Detalhes sobre a remessa do dia, lotes do tribunal, plantão judiciário ou particularidades...",
                key="input_ap_obs",
            )

            # Cálculos automáticos prévios
            tot_subs_aporte = qtd_subs_comum_in + qtd_subs_urg_in
            tot_obrig_aporte = qtd_obrig_comum_in + qtd_obrig_urg_in
            tot_urg_aporte = qtd_subs_urg_in + qtd_obrig_urg_in
            tot_geral_aporte = tot_subs_aporte + tot_obrig_aporte
            tx_urg_aporte = round((tot_urg_aporte / tot_geral_aporte * 100), 1) if tot_geral_aporte > 0 else 0.0

            col_res_ap1, col_res_ap2, col_res_ap3, col_res_ap4 = st.columns(4)
            with col_res_ap1:
                st.markdown(f"<div class='info-pill'>🟡 <b>Subsídios:</b> {tot_subs_aporte} ({qtd_subs_comum_in} reg. • {qtd_subs_urg_in} urg.)</div>", unsafe_allow_html=True)
            with col_res_ap2:
                st.markdown(f"<div class='info-pill'>🔵 <b>Obrigações:</b> {tot_obrig_aporte} ({qtd_obrig_comum_in} reg. • {qtd_obrig_urg_in} urg.)</div>", unsafe_allow_html=True)
            with col_res_ap3:
                st.markdown(f"<div class='info-pill-warning'>🚨 <b>Total Urgentes:</b> {tot_urg_aporte} ({tx_urg_aporte}%)</div>", unsafe_allow_html=True)
            with col_res_ap4:
                st.markdown(f"<div class='info-pill-success'>📥 <b>Total Geral:</b> {tot_geral_aporte} demandas</div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
            btn_salvar_aporte = st.form_submit_button("💾 Salvar Aporte Diário", type="primary", use_container_width=True)

            if btn_salvar_aporte:
                if tot_geral_aporte == 0:
                    st.warning("⚠️ Insira ao menos um quantitativo maior que zero para registrar o aporte do dia.")
                else:
                    try:
                        novo_id_ap = safe_add_aporte_diario(
                            data_aporte=dt_aporte_in,
                            quantidade_subsidios=tot_subs_aporte,
                            quantidade_subsidios_urgente=qtd_subs_urg_in,
                            quantidade_obrigacao_fazer=tot_obrig_aporte,
                            quantidade_obrigacao_fazer_urgente=qtd_obrig_urg_in,
                            observacoes=obs_aporte_in,
                        )
                        st.success(f"✅ Aporte diário de **{dt_aporte_in.strftime('%d/%m/%Y')}** registrado com sucesso! (ID #{novo_id_ap} • Total: {tot_geral_aporte} demandas)")
                        safe_rerun()
                    except Exception as err_ap:
                        st.error(f"Erro ao salvar aporte diário: {err_ap}")

        # Tabela com histórico recente de aportes cadastrados
        df_ultimos_aportes = safe_get_df_aportes_diarios()
        if not df_ultimos_aportes.empty:
            with st.expander("📋 Visualizar Últimos Aportes Cadastrados no Sistema", expanded=False):
                cols_show_ap = [
                    "id", "data_aporte", "subsidios_comum", "quantidade_subsidios_urgente",
                    "quantidade_subsidios", "obrigacao_fazer_comum", "quantidade_obrigacao_fazer_urgente",
                    "quantidade_obrigacao_fazer", "total_urgentes_aportados", "total_geral_aportado", "observacoes"
                ]
                cols_existentes = [c for c in cols_show_ap if c in df_ultimos_aportes.columns]
                st.dataframe(
                    df_ultimos_aportes[cols_existentes].head(15),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.NumberColumn("ID", width="small"),
                        "data_aporte": st.column_config.DateColumn("Data Aporte", format="DD/MM/YYYY"),
                        "subsidios_comum": st.column_config.NumberColumn("Subs. Comum"),
                        "quantidade_subsidios_urgente": st.column_config.NumberColumn("🚨 Subs. Urg."),
                        "quantidade_subsidios": st.column_config.NumberColumn("Total Subs."),
                        "obrigacao_fazer_comum": st.column_config.NumberColumn("Obrig. Comum"),
                        "quantidade_obrigacao_fazer_urgente": st.column_config.NumberColumn("⚡ Obrig. Urg."),
                        "quantidade_obrigacao_fazer": st.column_config.NumberColumn("Total Obrig."),
                        "total_urgentes_aportados": st.column_config.NumberColumn("🚨 Total Urgentes"),
                        "total_geral_aportado": st.column_config.NumberColumn("📥 Total Geral"),
                        "observacoes": st.column_config.TextColumn("Observações", width="large"),
                    }
                )

    elif tipo_registro == "📝 Produtividade Diária por Analista (Obrigações e Subsídios)":
        with st.form("form_produtividade_operacional", clear_on_submit=False):
            st.markdown("#### 📝 Lançamento de Produtividade Diária por Analista")
            st.caption("Insira os quantitativos de produtividade de cada analista sem necessidade de número de processo individual.")

            col_p_d1, col_p_d2 = st.columns([1, 1.5])
            with col_p_d1:
                dt_ref_input = st.date_input("Data de Referência", value=hoje, format="DD/MM/YYYY")
            with col_p_d2:
                analistas_op = [
                    a for a in db.get_analistas(active_only=True)
                    if a.especialidade == "Obrigações/Subsídios"
                ]
                opcoes_analistas_op = {a.nome: a.id for a in analistas_op}
                if not opcoes_analistas_op:
                    st.warning("Nenhum analista ativo de Obrigações/Subsídios disponível.")
                    analista_escolhido = None
                else:
                    analista_escolhido = st.selectbox("Analista Responsável", options=list(opcoes_analistas_op.keys()))

            st.markdown("##### 📊 Quantitativos do Expediente:")
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                qtd_subs = st.number_input("Quantidade de Subsídios", min_value=0, value=0, step=1, help="Total de subsídios recebidos/distribuídos no dia")
                qtd_subs_urg = st.number_input("Quantidade de Subsídios Urgente", min_value=0, value=0, step=1, help="Subconjunto de subsídios de caráter urgente/liminar")
                qtd_pend_ant = st.number_input("Quantidade de Pendências Anteriores", min_value=0, value=0, step=1, help="Saldo de pendências remanescentes do dia anterior")

            with col_q2:
                qtd_obrig = st.number_input("Quantidade de Obrigação de Fazer", min_value=0, value=0, step=1, help="Total de obrigações de fazer recebidas/distribuídas no dia")
                qtd_obrig_urg = st.number_input("Quantidade de Obrigação de Fazer Urgente", min_value=0, value=0, step=1, help="Subconjunto de obrigações urgentes / com cominação de multa")
                qtd_concl_dia = st.number_input("Quantidade de Demandas Concluídas no Dia", min_value=0, value=0, step=1, help="Total de demandas efetivamente concluídas e baixadas no dia")

            obs_prod = st.text_area("Observações Operacionais", placeholder="Notas sobre o expediente, priorizações de tutelas ou justificativas de pendências...")

            # Balanço prévio dos totais calculados
            total_entradas_calc = qtd_subs + qtd_obrig
            total_urgentes_calc = qtd_subs_urg + qtd_obrig_urg
            saldo_dia_calc = total_entradas_calc - qtd_concl_dia
            pend_finais_calc = max(0, qtd_pend_ant + saldo_dia_calc)
            taxa_prev = round((qtd_concl_dia / total_entradas_calc * 100), 1) if total_entradas_calc > 0 else (100.0 if qtd_concl_dia > 0 else 0.0)

            col_prev1, col_prev2, col_prev3, col_prev4 = st.columns(4)
            with col_prev1:
                st.info(f"📥 **Novas Entradas:** {total_entradas_calc}")
            with col_prev2:
                st.info(f"🚨 **Total Urgentes:** {total_urgentes_calc}")
            with col_prev3:
                st.info(f"📤 **Concluídas:** {qtd_concl_dia} ({taxa_prev}%)")
            with col_prev4:
                st.info(f"⏳ **Pendência Final:** {pend_finais_calc}")

            btn_salvar_prod = st.form_submit_button("💾 Salvar Registro de Produtividade", use_container_width=True)

            if btn_salvar_prod:
                if not analista_escolhido:
                    st.error("Selecione um analista responsável para continuar.")
                elif qtd_subs_urg > qtd_subs:
                    st.error("❌ A Quantidade de Subsídios Urgente não pode ser maior que o total de Subsídios.")
                elif qtd_obrig_urg > qtd_obrig:
                    st.error("❌ A Quantidade de Obrigação de Fazer Urgente não pode ser maior que o total de Obrigações de Fazer.")
                else:
                    try:
                        id_an = opcoes_analistas_op[analista_escolhido]
                        novo_id_prod = db.add_produtividade_operacional(
                            data_referencia=dt_ref_input,
                            id_analista=id_an,
                            quantidade_subsidios=qtd_subs,
                            quantidade_subsidios_urgente=qtd_subs_urg,
                            quantidade_obrigacao_fazer=qtd_obrig,
                            quantidade_obrigacao_fazer_urgente=qtd_obrig_urg,
                            quantidade_pendencias_anteriores=qtd_pend_ant,
                            quantidade_concluidas_dia=qtd_concl_dia,
                            observacoes=obs_prod,
                        )
                        st.success(f"✅ Produtividade de **{analista_escolhido}** em **{dt_ref_input.strftime('%d/%m/%Y')}** registrada com sucesso! (ID #{novo_id_prod})")
                        safe_rerun()
                    except Exception as err:
                        st.error(f"Erro ao salvar produtividade operacional: {err}")

    else:
        # Formulário de Ação Mandamental (Estrutura 100% Mantida)
        with st.form("form_acao_mandamental", clear_on_submit=True):
            st.markdown("#### 📜 Cadastro Unitário: Ação Mandamental (MS, HC, HD)")
            col_m1, col_m2, col_m3 = st.columns([2, 1.5, 1.5])

            with col_m1:
                cnj_m_input = st.text_input("Número do Processo (CNJ)", placeholder="1000000-00.0000.8.00.0000")
            with col_m2:
                tipo_mand = st.selectbox("Tipo de Ação Mandamental", options=["MS", "HC", "HD"])
            with col_m3:
                analistas_m = [
                    a for a in db.get_analistas(active_only=True)
                    if a.especialidade == "Ações Mandamentais"
                ]
                opcoes_m = {"Não Atribuído": None}
                for a in analistas_m:
                    opcoes_m[a.nome] = a.id
                analista_m_escolhido = st.selectbox("Analista Designado", options=list(opcoes_m.keys()))

            col_m4, col_m5, col_m6 = st.columns(3)
            with col_m4:
                dt_entrada_m = st.date_input("Data de Entrada", value=hoje, format="DD/MM/YYYY")
            with col_m5:
                status_tram_m = st.selectbox("Status de Tramitação", options=["Em Elaboração", "Aguardando Julgamento", "Transitado em Julgado"])
            with col_m6:
                st.markdown("<div style='margin-top: 1.6rem;'></div>", unsafe_allow_html=True)
                is_liminar = st.checkbox("⚡ Liminar / Urgência Mandamental?", value=(tipo_mand == "HC"))

            btn_salvar_m = st.form_submit_button("💾 Salvar Ação Mandamental", use_container_width=True)

            if btn_salvar_m:
                padrao_cnj = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"
                cnj_limpo = cnj_m_input.strip()
                if not re.match(padrao_cnj, cnj_limpo):
                    st.error("❌ Formato de processo CNJ inválido! Exemplo: 1012345-67.2024.8.19.0000")
                else:
                    try:
                        id_an_m = opcoes_m[analista_m_escolhido]
                        novo_id_m = db.add_acao_mandamental(
                            numero_processo=cnj_limpo,
                            tipo_acao=tipo_mand,
                            data_entrada=dt_entrada_m,
                            id_analista=id_an_m,
                            is_urgente_liminar=is_liminar,
                            status_tramitacao=status_tram_m,
                        )
                        st.success(f"✅ Ação Mandamental {cnj_limpo} cadastrada com sucesso! (ID #{novo_id_m})")
                    except Exception as err:
                        st.error(f"Erro ao salvar ação mandamental: {err}")

    st.divider()

    # Informações de Distribuição
    with st.expander("ℹ️ Informação sobre a Distribuição Operacional"):
        st.info("💡 **Modelo Operacional Direto:** Para Obrigações de Fazer e Subsídios, os quantitativos são registrados diretamente por analista diário, eliminando a exigência de sorteio unitário de processos. Para Ações Mandamentais (MS/HC/HD), o controle por número de processo permanece integral.")

    # Expander de Gestão Rápida da Equipe de Analistas
    with st.expander("👤 Gerenciar Equipe de Analistas Jurídicos", expanded=df_analistas.empty):
        col_an1, col_an2 = st.columns([1.5, 1])
        with col_an1:
            st.markdown("##### Analistas Cadastrados")
            if not df_analistas.empty:
                st.dataframe(df_analistas, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum analista cadastrado no banco. Utilize o formulário ao lado para cadastrar sua equipe.")
        with col_an2:
            st.markdown("##### Adicionar Novo Analista")
            novo_nome = st.text_input("Nome do Analista", placeholder="Ex: Dr. Carlos Silva")
            nova_esp = st.selectbox("Especialidade", options=["Obrigações/Subsídios", "Ações Mandamentais"])
            novo_ativo = st.checkbox("Analista Ativo?", value=True)
            if st.button("Adicionar Analista", type="primary", use_container_width=True):
                if novo_nome.strip():
                    db.add_analista(novo_nome.strip(), nova_esp, novo_ativo)
                    st.success(f"Analista {novo_nome} adicionado com sucesso!")
                    safe_rerun()
                else:
                    st.error("Informe o nome do analista.")

            if df_analistas.empty:
                st.info("ℹ️ Nenhum analista cadastrado no momento. Utilize o formulário acima para cadastrar os analistas da equipe.")


# ==============================================================================
# ABA 2: GESTÃO E BAIXA DE DEMANDAS
# ==============================================================================
with tab_gestao:
    st.markdown("### ⚖️ Gestão, Atualização de Status e Baixa de Demandas")
    st.caption("Edite os dados diretamente na tabela interativa e clique em Salvar para atualizar o banco de dados.")

    visao_gestao = st.radio(
        "Selecione a Base para Gestão:",
        options=[
            "📥 Aportes Diários de Demandas",
            "Produtividade Operacional (Obrigações e Subsídios)",
            "Ações Mandamentais (MS/HC/HD)",
        ],
        horizontal=True,
    )

    if visao_gestao == "📥 Aportes Diários de Demandas":
        df_ap_gestao = safe_get_df_aportes_diarios(
            data_inicio=filtro_data_inicio,
            data_fim=filtro_data_fim,
        )

        if df_ap_gestao.empty:
            st.info("Nenhum registro de aporte diário encontrado com os filtros selecionados.")
        else:
            st.markdown(f"**Total de Registros de Aportes:** `{len(df_ap_gestao)}` lançamentos diários")

            colunas_ap_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "data_aporte": st.column_config.DateColumn("Data do Aporte", format="DD/MM/YYYY", required=True),
                "subsidios_comum": st.column_config.NumberColumn("Subsídios Regulares", min_value=0),
                "quantidade_subsidios_urgente": st.column_config.NumberColumn("🚨 Subsídios Urgentes", min_value=0),
                "quantidade_subsidios": st.column_config.NumberColumn("Total Subsídios", disabled=True),
                "obrigacao_fazer_comum": st.column_config.NumberColumn("Obrigação Regular", min_value=0),
                "quantidade_obrigacao_fazer_urgente": st.column_config.NumberColumn("⚡ Obrigação Urgente", min_value=0),
                "quantidade_obrigacao_fazer": st.column_config.NumberColumn("Total Obrigação", disabled=True),
                "total_urgentes_aportados": st.column_config.NumberColumn("Total Urgentes", disabled=True),
                "total_geral_aportado": st.column_config.NumberColumn("Total Geral", disabled=True),
                "observacoes": st.column_config.TextColumn("Observações", width="large"),
            }

            colunas_ap_ordem = [
                "id",
                "data_aporte",
                "subsidios_comum",
                "quantidade_subsidios_urgente",
                "quantidade_subsidios",
                "obrigacao_fazer_comum",
                "quantidade_obrigacao_fazer_urgente",
                "quantidade_obrigacao_fazer",
                "total_urgentes_aportados",
                "total_geral_aportado",
                "observacoes",
            ]
            cols_reais = [c for c in colunas_ap_ordem if c in df_ap_gestao.columns]

            df_editado_ap = st.data_editor(
                df_ap_gestao[cols_reais],
                column_config=colunas_ap_config,
                hide_index=True,
                use_container_width=True,
                key="editor_demandas_aportes",
            )

            col_btn_ap1, col_btn_ap2 = st.columns([1, 1.2])
            with col_btn_ap1:
                if st.button("💾 Salvar Alterações de Aportes", type="primary", key="btn_salvar_ap_gestao"):
                    try:
                        regs_ap_atualizar = []
                        for rec in df_editado_ap.to_dict(orient="records"):
                            sub_c = int(rec.get("subsidios_comum") or 0)
                            sub_u = int(rec.get("quantidade_subsidios_urgente") or 0)
                            ob_c = int(rec.get("obrigacao_fazer_comum") or 0)
                            ob_u = int(rec.get("quantidade_obrigacao_fazer_urgente") or 0)
                            rec["quantidade_subsidios"] = sub_c + sub_u
                            rec["quantidade_obrigacao_fazer"] = ob_c + ob_u
                            regs_ap_atualizar.append(rec)

                        qtd_at_ap = db.bulk_update_aportes_diarios(regs_ap_atualizar) if hasattr(db, "bulk_update_aportes_diarios") else 0
                        st.success(f"✅ {qtd_at_ap} registros de aportes diários atualizados com sucesso!")
                        safe_rerun()
                    except Exception as err_ap_at:
                        st.error(f"Erro ao atualizar aportes diários: {err_ap_at}")

            with col_btn_ap2:
                with st.expander("🗑️ Excluir Registro de Aporte Diário"):
                    id_ap_del = st.number_input("ID do Aporte", min_value=1, step=1, key="num_del_aporte")
                    if st.button("Confirmar Exclusão do Aporte", type="secondary", key="btn_confirm_del_ap"):
                        if hasattr(db, "delete_aporte_diario") and db.delete_aporte_diario(int(id_ap_del)):
                            st.success(f"Aporte ID #{id_ap_del} excluído com sucesso!")
                            safe_rerun()
                        else:
                            st.error(f"Aporte ID #{id_ap_del} não encontrado.")

    elif visao_gestao == "Produtividade Operacional (Obrigações e Subsídios)":
        df_prod_gestao = db.get_df_produtividade_operacional(
            data_inicio=filtro_data_inicio,
            data_fim=filtro_data_fim,
            id_analista=filtro_id_analista,
        )

        if df_prod_gestao.empty:
            st.info("Nenhum registro de produtividade operacional encontrado com os filtros selecionados.")
        else:
            st.markdown(f"**Total de Registros de Produtividade:** `{len(df_prod_gestao)}` lançamentos diários")

            colunas_prod_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "data_referencia": st.column_config.DateColumn("Data de Referência", format="DD/MM/YYYY"),
                "analista_nome": st.column_config.TextColumn("Analista", disabled=True),
                "quantidade_subsidios": st.column_config.NumberColumn("Subsídios", min_value=0),
                "quantidade_subsidios_urgente": st.column_config.NumberColumn("Subsídios Urg.", min_value=0),
                "quantidade_obrigacao_fazer": st.column_config.NumberColumn("Obrigação Fazer", min_value=0),
                "quantidade_obrigacao_fazer_urgente": st.column_config.NumberColumn("Obrigação Urg.", min_value=0),
                "quantidade_pendencias_anteriores": st.column_config.NumberColumn("Pend. Anteriores", min_value=0),
                "quantidade_concluidas_dia": st.column_config.NumberColumn("Concluídas Dia", min_value=0),
                "total_entradas_dia": st.column_config.NumberColumn("Total Entradas", disabled=True),
                "saldo_diario": st.column_config.NumberColumn("Saldo Diário", disabled=True),
                "pendencias_finais_dia": st.column_config.NumberColumn("Pendência Final", disabled=True),
                "observacoes": st.column_config.TextColumn("Observações", width="large"),
            }

            colunas_prod_ordem = [
                "id",
                "data_referencia",
                "analista_nome",
                "quantidade_subsidios",
                "quantidade_subsidios_urgente",
                "quantidade_obrigacao_fazer",
                "quantidade_obrigacao_fazer_urgente",
                "quantidade_pendencias_anteriores",
                "quantidade_concluidas_dia",
                "total_entradas_dia",
                "saldo_diario",
                "pendencias_finais_dia",
                "observacoes",
            ]

            df_editado_prod = st.data_editor(
                df_prod_gestao[colunas_prod_ordem],
                column_config=colunas_prod_config,
                hide_index=True,
                use_container_width=True,
                key="editor_produtividade_op",
            )

            col_btn_p1, col_btn_p2 = st.columns([1.5, 1])
            with col_btn_p1:
                if st.button("💾 Salvar Alterações de Produtividade", type="primary"):
                    try:
                        registros_para_atualizar = df_editado_prod.to_dict(orient="records")
                        qtd_atualizada = db.bulk_update_produtividade_operacional(registros_para_atualizar)
                        st.success(f"✅ {qtd_atualizada} registros de produtividade atualizados com sucesso no banco de dados!")
                        safe_rerun()
                    except Exception as err:
                        st.error(f"Erro ao atualizar produtividade: {err}")

            with col_btn_p2:
                with st.expander("🗑️ Excluir Registro de Produtividade"):
                    id_para_excluir = st.number_input("ID do Registro", min_value=1, step=1, key="num_del_prod")
                    if st.button("Confirmar Exclusão Definitiva", type="secondary", key="btn_confirm_del_prod"):
                        if db.delete_produtividade_operacional(int(id_para_excluir)):
                            st.success(f"Registro ID #{id_para_excluir} excluído com sucesso!")
                            safe_rerun()
                        else:
                            st.error(f"Registro ID #{id_para_excluir} não encontrado.")

    else:
        # Gestão de Ações Mandamentais
        df_mand_gestao = db.get_df_acoes_mandamentais(
            data_inicio=filtro_data_inicio,
            data_fim=filtro_data_fim,
            id_analista=filtro_id_analista,
            tipo_acao=tipo_produto_filtro if tipo_produto_filtro in ["MS", "HC", "HD"] else None,
            apenas_liminares=apenas_urgentes,
        )

        if df_mand_gestao.empty:
            st.info("Nenhuma ação mandamental encontrada com os filtros selecionados.")
        else:
            st.markdown(f"**Total de Ações Mandamentais:** `{len(df_mand_gestao)}` registros")

            colunas_mand_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "numero_processo": st.column_config.TextColumn("Processo", disabled=True),
                "tipo_acao": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
                "data_entrada": st.column_config.DateColumn("Entrada", disabled=True, format="DD/MM/YYYY"),
                "analista_nome": st.column_config.TextColumn("Analista", disabled=True),
                "is_urgente_liminar": st.column_config.CheckboxColumn("Liminar Urgente?"),
                "data_manifestacao": st.column_config.DateColumn("Data Manifestação", format="DD/MM/YYYY"),
                "status_tramitacao": st.column_config.SelectboxColumn(
                    "Tramitação",
                    options=["Em Elaboração", "Aguardando Julgamento", "Transitado em Julgado"],
                    required=True,
                ),
                "data_sentenca": st.column_config.DateColumn("Data Sentença", format="DD/MM/YYYY"),
                "resultado_merito": st.column_config.SelectboxColumn(
                    "Resultado do Mérito",
                    options=["Favorável (Denegado)", "Desfavorável (Concedido)", "Sem Resolução de Mérito", None],
                ),
            }

            df_editado_mand = st.data_editor(
                df_mand_gestao,
                column_config=colunas_mand_config,
                hide_index=True,
                use_container_width=True,
                key="editor_demandas_mand",
            )

            if st.button("💾 Salvar Ações Mandamentais", type="primary"):
                try:
                    registros_mand = df_editado_mand.to_dict(orient="records")
                    qtd = db.bulk_update_acoes_mandamentais(registros_mand)
                    st.success(f"✅ {qtd} ações mandamentais atualizadas com sucesso!")
                    safe_rerun()
                except Exception as err:
                    st.error(f"Erro ao atualizar ações mandamentais: {err}")


# ==============================================================================
# ABA 3: PAINEL GERENCIAL DE PRODUTIVIDADE (DASHBOARD)
# ==============================================================================
with tab_dashboard:
    st.markdown("### 📊 Painel Gerencial de Produtividade e Desempenho Jurídico")
    st.caption("Visão executiva consolidada: contabilidade das demandas distribuídas e análises especializadas das ações mandamentais.")

    subtab_aportes, subtab_operacional, subtab_mandamentais = st.tabs([
        "📥 Aportes Diários e Mensais (Demandas que Aportam)",
        "📋 Produtividade e Distribuição por Analista",
        "📜 Ações Mandamentais (MS, HC, HD)",
    ])

    # ==========================================================================
    # SUB-ABA 1: APORTES DIÁRIOS E MENSAIS (DEMANDAS QUE APORTAM)
    # ==========================================================================
    with subtab_aportes:
        st.markdown("#### 📥 Contabilidade e Análise de Demandas que Aportam no Setor")
        st.caption("Acompanhamento quantitativo das entradas que aportam por data: Subsídios (comuns e urgentes) e Obrigações de Fazer (comuns e urgentes), com gráficos diários e mensais.")

        df_ap_dash = safe_get_df_aportes_diarios(data_inicio=filtro_data_inicio, data_fim=filtro_data_fim)
        kpis_ap = safe_calcular_kpis_aportes(df_ap_dash)

        if df_ap_dash.empty:
            st.info("ℹ️ Nenhum quantitativo de aporte diário cadastrado para o período selecionado. Cadastre novas entradas na **Aba 1 (📥 Entrada e Distribuição Diária)**.")
        else:
            # 1. Cards de Quantitativos das 4 Categorias
            st.markdown("##### 📊 Quantitativos Computados por Categoria no Período:")
            col_ap_c1, col_ap_c2, col_ap_c3, col_ap_c4 = st.columns(4)
            with col_ap_c1:
                st.metric(
                    label="🟡 Subsídios Comuns (Regulares)",
                    value=f"{kpis_ap['subsidios_comuns']}",
                    delta=f"Total: {kpis_ap['total_subsidios']} ({round(kpis_ap['subsidios_comuns']/kpis_ap['total_subsidios']*100, 1) if kpis_ap['total_subsidios']>0 else 100}%)",
                    delta_color="off",
                    help="Volume de demandas de subsídios comuns com prazo regular que aportaram",
                )
            with col_ap_c2:
                st.metric(
                    label="🚨 Subsídios Urgentes",
                    value=f"{kpis_ap['total_subsidios_urgentes']}",
                    delta=f"{round(kpis_ap['total_subsidios_urgentes']/kpis_ap['total_subsidios']*100, 1) if kpis_ap['total_subsidios']>0 else 0}% dos subsídios",
                    delta_color="inverse" if kpis_ap['total_subsidios_urgentes'] > 0 else "off",
                    help="Volume de demandas de subsídios urgentes / liminares que aportaram",
                )
            with col_ap_c3:
                st.metric(
                    label="🔵 Obrigação de Fazer Comum",
                    value=f"{kpis_ap['obrigacao_fazer_comuns']}",
                    delta=f"Total: {kpis_ap['total_obrigacao_fazer']} ({round(kpis_ap['obrigacao_fazer_comuns']/kpis_ap['total_obrigacao_fazer']*100, 1) if kpis_ap['total_obrigacao_fazer']>0 else 100}%)",
                    delta_color="off",
                    help="Volume de obrigações de fazer regulares com prazos ordinários que aportaram",
                )
            with col_ap_c4:
                st.metric(
                    label="⚡ Obrigação de Fazer Urgente",
                    value=f"{kpis_ap['total_obrigacao_fazer_urgentes']}",
                    delta=f"{round(kpis_ap['total_obrigacao_fazer_urgentes']/kpis_ap['total_obrigacao_fazer']*100, 1) if kpis_ap['total_obrigacao_fazer']>0 else 0}% das obrigações",
                    delta_color="inverse" if kpis_ap['total_obrigacao_fazer_urgentes'] > 0 else "off",
                    help="Volume de obrigações de fazer urgentes sob pena de multa (astreintes) que aportaram",
                )

            st.markdown("<div style='margin-top: 0.4rem;'></div>", unsafe_allow_html=True)

            # 2. Cards Consolidados de Totais e Médias
            col_ap_fl1, col_ap_fl2, col_ap_fl3, col_ap_fl4 = st.columns(4)
            with col_ap_fl1:
                st.metric(
                    label="📥 Total Geral Aportado",
                    value=f"{kpis_ap['total_geral_aportado']}",
                    delta=f"Regulares: {kpis_ap['total_regulares']} • Urgentes: {kpis_ap['total_urgentes']}",
                    delta_color="off",
                    help="Somatório total de todas as demandas que aportaram no setor no período filtrado",
                )
            with col_ap_fl2:
                st.metric(
                    label="🚨 Índice Geral de Urgência",
                    value=f"{kpis_ap['taxa_urgencia_pct']}%",
                    delta=f"{kpis_ap['total_urgentes']} urgentes no período",
                    delta_color="inverse" if kpis_ap['total_urgentes'] > 0 else "off",
                    help="Percentual de demandas urgentes em relação ao total aportado",
                )
            with col_ap_fl3:
                st.metric(
                    label="📅 Dias com Aportes",
                    value=f"{kpis_ap['dias_com_aporte']} dias",
                    delta=f"Período: {filtro_data_inicio.strftime('%d/%m')} a {filtro_data_fim.strftime('%d/%m')}",
                    delta_color="off",
                    help="Quantidade de datas distintas em que houve registro de entrada",
                )
            with col_ap_fl4:
                pico_txt = f"Pico: {kpis_ap['maior_aporte_dia_volume']} dem. em {kpis_ap['maior_aporte_dia_data'].strftime('%d/%m/%Y')}" if kpis_ap['maior_aporte_dia_data'] else "Sem pico"
                st.metric(
                    label="📈 Média Diária de Aporte",
                    value=f"{kpis_ap['media_diaria_aporte']} dem./dia",
                    delta=pico_txt,
                    delta_color="off",
                    help="Média diária de demandas recebidas nos dias com movimentação",
                )

            st.divider()

            # 3. Gráficos Diários
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">📅 1. Evolução Diária das Demandas que Aportam</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Acompanhamento diário da quantidade de demandas que aportaram, desdobradas por Subsídios e Obrigações de Fazer (regulares e urgentes).</div>', unsafe_allow_html=True)

                df_serie_dia = safe_gerar_serie_diaria_aportes(df_ap_dash)
                if not df_serie_dia.empty:
                    col_fmt_dia, _ = st.columns([2, 3])
                    with col_fmt_dia:
                        tipo_graf_dia = st.radio(
                            "Estilo do Gráfico Diário:",
                            options=["Barras Empilhadas", "Barras Agrupadas", "Linhas de Tendência"],
                            horizontal=True,
                            key="tipo_graf_dia_ap",
                        )

                    fig_dia = go.Figure()
                    categorias_dia = [
                        ("Subsídios Comuns", "subsidios_comum", "#38BDF8"),
                        ("🚨 Subsídios Urgentes", "subsidios_urgente", "#F59E0B"),
                        ("Obrigações Comuns", "obrigacao_comum", "#818CF8"),
                        ("⚡ Obrigações Urgentes", "obrigacao_urgente", "#EF4444"),
                    ]

                    if tipo_graf_dia in ["Barras Empilhadas", "Barras Agrupadas"]:
                        b_mode = "stack" if tipo_graf_dia == "Barras Empilhadas" else "group"
                        for nome_cat, col_cat, cor_cat in categorias_dia:
                            fig_dia.add_trace(
                                go.Bar(
                                    name=nome_cat,
                                    x=df_serie_dia["data_str"],
                                    y=df_serie_dia[col_cat],
                                    marker_color=cor_cat,
                                    text=df_serie_dia[col_cat],
                                    textposition="inside" if b_mode == "stack" else "outside",
                                    textfont=dict(size=10, family="sans-serif"),
                                )
                            )
                        fig_dia.update_layout(barmode=b_mode)
                    else:
                        for nome_cat, col_cat, cor_cat in categorias_dia:
                            fig_dia.add_trace(
                                go.Scatter(
                                    name=nome_cat,
                                    x=df_serie_dia["data_str"],
                                    y=df_serie_dia[col_cat],
                                    mode="lines+markers",
                                    line=dict(color=cor_cat, width=2.5),
                                    marker=dict(size=7),
                                )
                            )
                        fig_dia.add_trace(
                            go.Scatter(
                                name="📥 Total Geral do Dia",
                                x=df_serie_dia["data_str"],
                                y=df_serie_dia["total_dia"],
                                mode="lines+markers+text",
                                text=df_serie_dia["total_dia"],
                                textposition="top center",
                                textfont=dict(color="#38BDF8", size=11),
                                line=dict(color="#38BDF8", width=3, dash="dot"),
                                marker=dict(size=9, symbol="diamond"),
                            )
                        )

                    max_y_dia = max(int(df_serie_dia["total_dia"].max()), 1)
                    fig_dia.update_layout(
                        height=420,
                        margin=dict(l=40, r=40, t=50, b=80, autoexpand=True),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.04,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=11, color="#E2E8F0"),
                        ),
                        xaxis=dict(
                            title=dict(text="Data do Aporte", standoff=15, font=dict(color="#E2E8F0")),
                            tickangle=-45,
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=11),
                        ),
                        yaxis=dict(
                            title=dict(text="Quantidade Aportada", standoff=10, font=dict(color="#E2E8F0")),
                            range=[0, max_y_dia * 1.25] if tipo_graf_dia != "Barras Agrupadas" else None,
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=11),
                        ),
                        hovermode="x unified",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="sans-serif", color="#E2E8F0"),
                    )
                    st.plotly_chart(fig_dia, use_container_width=True)

                    col_dia_c1, col_dia_c2 = st.columns([1, 1.4])
                    with col_dia_c1:
                        df_donut_ap = pd.DataFrame([
                            {"categoria": "Subsídios Comuns", "quantidade": kpis_ap["subsidios_comuns"]},
                            {"categoria": "Subsídios Urgentes", "quantidade": kpis_ap["total_subsidios_urgentes"]},
                            {"categoria": "Obrigação Comum", "quantidade": kpis_ap["obrigacao_fazer_comuns"]},
                            {"categoria": "Obrigação Urgente", "quantidade": kpis_ap["total_obrigacao_fazer_urgentes"]},
                        ])
                        df_donut_ap_filtrado = df_donut_ap[df_donut_ap["quantidade"] > 0]
                        if not df_donut_ap_filtrado.empty:
                            fig_donut_ap = px.pie(
                                df_donut_ap_filtrado,
                                names="categoria",
                                values="quantidade",
                                hole=0.52,
                                color="categoria",
                                color_discrete_map={
                                    "Subsídios Comuns": "#38BDF8",
                                    "Subsídios Urgentes": "#F59E0B",
                                    "Obrigação Comum": "#818CF8",
                                    "Obrigação Urgente": "#EF4444",
                                },
                            )
                            fig_donut_ap.update_traces(
                                textposition="inside",
                                textinfo="percent+value",
                                textfont=dict(size=11, color="#FFFFFF"),
                            )
                            fig_donut_ap.update_layout(
                                height=280,
                                title=dict(text="Proporção das 4 Demandas que Aportaram", font=dict(size=13, color="#E2E8F0")),
                                margin=dict(l=15, r=15, t=35, b=15),
                                paper_bgcolor="rgba(0,0,0,0)",
                                legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(size=10, color="#E2E8F0")),
                            )
                            st.plotly_chart(fig_donut_ap, use_container_width=True)
                    with col_dia_c2:
                        st.markdown("**📋 Tabela Analítica Diária:**")
                        cols_tabela_dia = [
                            "data_str", "subsidios_comum", "subsidios_urgente",
                            "obrigacao_comum", "obrigacao_urgente", "total_dia", "taxa_urgencia_dia"
                        ]
                        st.dataframe(
                            df_serie_dia[cols_tabela_dia],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "data_str": st.column_config.TextColumn("Data"),
                                "subsidios_comum": st.column_config.NumberColumn("Subs. Comum"),
                                "subsidios_urgente": st.column_config.NumberColumn("Subs. Urg."),
                                "obrigacao_comum": st.column_config.NumberColumn("Obrig. Comum"),
                                "obrigacao_urgente": st.column_config.NumberColumn("Obrig. Urg."),
                                "total_dia": st.column_config.NumberColumn("Total Dia"),
                                "taxa_urgencia_dia": st.column_config.NumberColumn("% Urgência", format="%.1f%%"),
                            }
                        )

            # 4. Gráficos Mensais
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">📆 2. Evolução Mensal e Comparativo Mês a Mês</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Totalização e comportamento dos quantitativos agrupados por mês (comuns e urgentes).</div>', unsafe_allow_html=True)

                df_serie_mes = safe_gerar_serie_mensal_aportes(df_ap_dash)
                if df_serie_mes.empty:
                    st.info("Sem dados mensais para exibir no período.")
                else:
                    fig_mes = go.Figure()
                    fig_mes.add_trace(
                        go.Bar(
                            name="Subsídios Comuns",
                            x=df_serie_mes["rotulo_mes"],
                            y=df_serie_mes["subsidios_comum"],
                            marker_color="#38BDF8",
                            text=df_serie_mes["subsidios_comum"],
                            textposition="inside",
                            textfont=dict(size=11),
                        )
                    )
                    fig_mes.add_trace(
                        go.Bar(
                            name="🚨 Subsídios Urgentes",
                            x=df_serie_mes["rotulo_mes"],
                            y=df_serie_mes["subsidios_urgente"],
                            marker_color="#F59E0B",
                            text=df_serie_mes["subsidios_urgente"],
                            textposition="inside",
                            textfont=dict(size=11),
                        )
                    )
                    fig_mes.add_trace(
                        go.Bar(
                            name="Obrigações Comuns",
                            x=df_serie_mes["rotulo_mes"],
                            y=df_serie_mes["obrigacao_comum"],
                            marker_color="#818CF8",
                            text=df_serie_mes["obrigacao_comum"],
                            textposition="inside",
                            textfont=dict(size=11),
                        )
                    )
                    fig_mes.add_trace(
                        go.Bar(
                            name="⚡ Obrigações Urgentes",
                            x=df_serie_mes["rotulo_mes"],
                            y=df_serie_mes["obrigacao_urgente"],
                            marker_color="#EF4444",
                            text=df_serie_mes["obrigacao_urgente"],
                            textposition="inside",
                            textfont=dict(size=11),
                        )
                    )
                    # Linha do Total Mensal
                    fig_mes.add_trace(
                        go.Scatter(
                            name="📥 Total do Mês",
                            x=df_serie_mes["rotulo_mes"],
                            y=df_serie_mes["total_mes"],
                            mode="lines+markers+text",
                            text=df_serie_mes["total_mes"],
                            textposition="top center",
                            textfont=dict(color="#38BDF8", size=12),
                            line=dict(color="#38BDF8", width=3, dash="dot"),
                            marker=dict(size=9, symbol="circle"),
                        )
                    )

                    fig_mes.update_layout(
                        barmode="stack",
                        height=420,
                        margin=dict(l=40, r=40, t=50, b=70, autoexpand=True),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.04,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=11, color="#E2E8F0"),
                        ),
                        xaxis=dict(
                            title=dict(text="Mês de Referência", standoff=15, font=dict(color="#E2E8F0")),
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=12),
                        ),
                        yaxis=dict(
                            title=dict(text="Total de Demandas Aportadas", standoff=10, font=dict(color="#E2E8F0")),
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=11),
                        ),
                        hovermode="x unified",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="sans-serif", color="#E2E8F0"),
                    )
                    st.plotly_chart(fig_mes, use_container_width=True)

                    st.markdown("**📋 Tabela Analítica Mensal Consolidada:**")
                    cols_tabela_mes = [
                        "rotulo_mes", "subsidios_comum", "subsidios_urgente", "total_subsidios",
                        "obrigacao_comum", "obrigacao_urgente", "total_obrigacao", "total_mes",
                        "total_urgente_mes", "taxa_urgencia_mes", "dias_registrados", "media_diaria_mes"
                    ]
                    st.dataframe(
                        df_serie_mes[cols_tabela_mes],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "rotulo_mes": st.column_config.TextColumn("Mês/Ano"),
                            "subsidios_comum": st.column_config.NumberColumn("Subs. Comum"),
                            "subsidios_urgente": st.column_config.NumberColumn("Subs. Urg."),
                            "total_subsidios": st.column_config.NumberColumn("Total Subsídios"),
                            "obrigacao_comum": st.column_config.NumberColumn("Obrig. Comum"),
                            "obrigacao_urgente": st.column_config.NumberColumn("Obrig. Urg."),
                            "total_obrigacao": st.column_config.NumberColumn("Total Obrigações"),
                            "total_mes": st.column_config.NumberColumn("Total Mês"),
                            "total_urgente_mes": st.column_config.NumberColumn("Urgentes Mês"),
                            "taxa_urgencia_mes": st.column_config.NumberColumn("% Urgência", format="%.1f%%"),
                            "dias_registrados": st.column_config.NumberColumn("Dias Reg."),
                            "media_diaria_mes": st.column_config.NumberColumn("Média/Dia", format="%.1f"),
                        }
                    )

    # ==========================================================================
    # SUB-ABA 2: PRODUTIVIDADE E DISTRIBUIÇÃO POR ANALISTA
    # ==========================================================================
    with subtab_operacional:
        df_op_dash = db.get_df_produtividade_operacional(
            data_inicio=filtro_data_inicio,
            data_fim=filtro_data_fim,
            id_analista=filtro_id_analista,
        )
        kpis_op = met.calcular_kpis_operacionais(df_op_dash)

        # Alerta de Demandas Urgentes Críticas
        df_urgentes_criticas = met.obter_demandas_urgentes_criticas(df_op_dash)
        if not df_urgentes_criticas.empty:
            st.markdown(
                f"""
                <div class="alerta-critico-box">
                    <div class="alerta-critico-titulo">🚨 ATENÇÃO: {len(df_urgentes_criticas)} REGISTROS COM DEMANDAS URGENTES NO PERÍODO!</div>
                    <div class="alerta-critico-texto">Existem demandas com prioridade urgente ou cominação de multa que exigem tempestividade plena para mitigação de risco financeiro e processual.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Visualizar Detalhamento dos Registros com Urgências", expanded=False):
                if "data_referencia" in df_urgentes_criticas.columns:
                    cols_alert = [c for c in ["data_referencia", "analista_nome", "total_urgentes", "quantidade_subsidios_urgente", "quantidade_obrigacao_fazer_urgente", "observacoes"] if c in df_urgentes_criticas.columns]
                    st.dataframe(
                        df_urgentes_criticas[cols_alert],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "data_referencia": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                            "analista_nome": st.column_config.TextColumn("Analista"),
                            "total_urgentes": st.column_config.NumberColumn("🚨 Total Urgentes"),
                            "quantidade_subsidios_urgente": st.column_config.NumberColumn("Subsídios Urg."),
                            "quantidade_obrigacao_fazer_urgente": st.column_config.NumberColumn("Obrigação Urg."),
                            "observacoes": st.column_config.TextColumn("Observações", width="large"),
                        },
                    )

        # ----------------------------------------------------------------------
        # CONTABILIDADE DE TODAS AS DEMANDAS DISTRIBUÍDAS
        # ----------------------------------------------------------------------
        st.markdown("#### 📥 Contabilidade Consolidada de Demandas Distribuídas")
        
        tot_sub = kpis_op.get("total_subsidios", 0)
        tot_sub_urg = kpis_op.get("total_subsidios_urgentes", 0)
        sub_comum = max(0, tot_sub - tot_sub_urg)
        
        tot_obrig = kpis_op.get("total_obrigacao_fazer", 0)
        tot_obrig_urg = kpis_op.get("total_obrigacao_fazer_urgentes", 0)
        obrig_comum = max(0, tot_obrig - tot_obrig_urg)
        
        tot_distribuido = kpis_op.get("volume_distribuido", 0)
        tot_urgentes_dist = tot_sub_urg + tot_obrig_urg
        tot_regulares_dist = sub_comum + obrig_comum

        # Linha 1: 4 Cards de Contabilidade de Demandas Distribuídas
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            st.metric(
                label="🟡 Subsídios Comuns (Regulares)",
                value=f"{sub_comum}",
                delta=f"Total: {tot_sub} ({round(sub_comum/tot_sub*100, 1) if tot_sub>0 else 100}%)",
                delta_color="off",
                help="Demandas de subsídios comuns com prazo ordinário distribuídas no período",
            )
        with col_c2:
            st.metric(
                label="🚨 Subsídios Urgentes",
                value=f"{tot_sub_urg}",
                delta=f"{round(tot_sub_urg/tot_sub*100, 1) if tot_sub>0 else 0}% dos subsídios",
                delta_color="inverse" if tot_sub_urg > 0 else "off",
                help="Subsídios de caráter urgente/liminar com prioridade de atendimento",
            )
        with col_c3:
            st.metric(
                label="🔵 Obrigação de Fazer Comum",
                value=f"{obrig_comum}",
                delta=f"Total: {tot_obrig} ({round(obrig_comum/tot_obrig*100, 1) if tot_obrig>0 else 100}%)",
                delta_color="off",
                help="Obrigações de fazer comuns com prazos ordinários distribuídas",
            )
        with col_c4:
            st.metric(
                label="⚡ Obrigação de Fazer Urgente",
                value=f"{tot_obrig_urg}",
                delta=f"{round(tot_obrig_urg/tot_obrig*100, 1) if tot_obrig>0 else 0}% das obrigações",
                delta_color="inverse" if tot_obrig_urg > 0 else "off",
                help="Obrigações de fazer sob pena de cominação de multa diária ou tutela liminar",
            )

        st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

        # Linha 2: Balanço Geral de Fluxo Operacional
        col_fl1, col_fl2, col_fl3, col_fl4 = st.columns(4)
        with col_fl1:
            st.metric(
                label="👥 Total Distribuído",
                value=f"{tot_distribuido}",
                delta=f"Regulares: {tot_regulares_dist} • Urgentes: {tot_urgentes_dist}",
                delta_color="off",
                help="Carga total distribuída no período somando todas as modalidades",
            )
        with col_fl2:
            saldo_vazao = kpis_op['volume_concluido'] - tot_distribuido
            st.metric(
                label="📤 Volume Concluído",
                value=f"{kpis_op['volume_concluido']}",
                delta=f"{saldo_vazao:+d} de saldo no período",
                delta_color="normal" if saldo_vazao >= 0 else "inverse",
                help="Demandas finalizadas no expediente pelos analistas no período",
            )
        with col_fl3:
            urg_pend = kpis_op['total_urgentes_pendentes']
            st.metric(
                label="⏳ Pendências Ativas (Backlog)",
                value=f"{kpis_op['backlog_pendencias']}",
                delta=f"{urg_pend} urgentes pendentes" if urg_pend > 0 else "0 urgentes pendentes",
                delta_color="inverse" if urg_pend > 0 else "off",
                help="Saldo total de demandas em andamento aguardando conclusão",
            )
        with col_fl4:
            prod_val = kpis_op['taxa_produtividade']
            diff_meta = round(prod_val - 80.0, 1)
            st.metric(
                label="🎯 Taxa de Produtividade",
                value=f"{prod_val}%",
                delta=f"{diff_meta:+.1f}% vs Meta (80%)",
                delta_color="normal" if prod_val >= 80.0 else "inverse",
                help="Relação percentual calculada: (Concluídas / Distribuídas) * 100",
            )

        st.divider()

        # ----------------------------------------------------------------------
        # COMPOSIÇÃO: BARRAS EMPILHADAS + DONUT
        # ----------------------------------------------------------------------
        col_comp1, col_comp2 = st.columns([1.2, 1])
        with col_comp1:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">📊 Composição das Demandas: Regulares vs. Urgentes</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Comparativo de volume entre demandas com prazo regular e demandas urgentes por tipo de produto.</div>', unsafe_allow_html=True)

                if tot_distribuido > 0:
                    df_bar_comp = pd.DataFrame([
                        {
                            "Tipo": "Subsídios",
                            "Regulares": sub_comum,
                            "Urgentes": tot_sub_urg,
                            "Total": tot_sub,
                        },
                        {
                            "Tipo": "Obrigação de Fazer",
                            "Regulares": obrig_comum,
                            "Urgentes": tot_obrig_urg,
                            "Total": tot_obrig,
                        },
                    ])
                    fig_stack = go.Figure()
                    fig_stack.add_trace(
                        go.Bar(
                            name="Regulares / Comuns",
                            x=df_bar_comp["Tipo"],
                            y=df_bar_comp["Regulares"],
                            marker_color="#38BDF8",
                            text=df_bar_comp["Regulares"],
                            textposition="inside",
                            textfont=dict(color="#0F172A", size=13, family="sans-serif"),
                        )
                    )
                    fig_stack.add_trace(
                        go.Bar(
                            name="🚨 Urgentes / Com Multa",
                            x=df_bar_comp["Tipo"],
                            y=df_bar_comp["Urgentes"],
                            marker_color="#EF4444",
                            text=df_bar_comp["Urgentes"],
                            textposition="inside",
                            textfont=dict(color="#FFFFFF", size=13, family="sans-serif"),
                        )
                    )
                    fig_stack.update_layout(
                        barmode="stack",
                        height=310,
                        margin=dict(l=40, r=40, t=45, b=40, autoexpand=True),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.03,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=12, color="#E2E8F0"),
                        ),
                        xaxis=dict(
                            tickfont=dict(size=12, color="#F1F5F9"),
                            showgrid=False,
                        ),
                        yaxis=dict(
                            title=dict(text="Quantidade de Demandas", standoff=10, font=dict(color="#E2E8F0")),
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=11),
                        ),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="sans-serif", color="#E2E8F0"),
                    )
                    st.plotly_chart(fig_stack, use_container_width=True)
                else:
                    st.info("Sem demandas operacionais distribuídas no período selecionado.")

        with col_comp2:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">🥧 Proporção das 4 Demandas Distribuídas</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Distribuição percentual consolidada entre as 4 categorias de demandas distribuídas.</div>', unsafe_allow_html=True)

                if tot_distribuido > 0:
                    df_pie_dist = pd.DataFrame([
                        {"categoria": "Subsídios Comuns", "quantidade": sub_comum},
                        {"categoria": "Subsídios Urgentes", "quantidade": tot_sub_urg},
                        {"categoria": "Obrigação Comum", "quantidade": obrig_comum},
                        {"categoria": "Obrigação Urgente", "quantidade": tot_obrig_urg},
                    ])
                    df_pie_filtrado = df_pie_dist[df_pie_dist["quantidade"] > 0]
                    if not df_pie_filtrado.empty:
                        fig_donut_dist = px.pie(
                            df_pie_filtrado,
                            names="categoria",
                            values="quantidade",
                            hole=0.52,
                            color="categoria",
                            color_discrete_map={
                                "Subsídios Comuns": "#38BDF8",
                                "Subsídios Urgentes": "#F59E0B",
                                "Obrigação Comum": "#818CF8",
                                "Obrigação Urgente": "#EF4444",
                            },
                        )
                        fig_donut_dist.update_traces(
                            textposition="inside",
                            textinfo="percent+value",
                            textfont=dict(size=11, color="#FFFFFF", family="sans-serif"),
                        )
                        fig_donut_dist.update_layout(
                            height=310,
                            margin=dict(l=20, r=20, t=35, b=20, autoexpand=True),
                            paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5,
                                font=dict(size=11, color="#E2E8F0"),
                            ),
                            font=dict(family="sans-serif", color="#E2E8F0"),
                        )
                        st.plotly_chart(fig_donut_dist, use_container_width=True)
                    else:
                        st.info("Quantitativos zerados.")
                else:
                    st.info("Sem dados para compor gráfico de rosca.")

        # ----------------------------------------------------------------------
        # BALANÇO DIÁRIO DE FLUXO (ENTRADAS VS SAÍDAS)
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.markdown('<div class="panel-header-title">📈 Balanço Diário de Fluxo: Entradas vs. Saídas (Evidenciação de Gargalo)</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-header-desc">Acompanhamento diário das novas demandas recebidas em relação às conclusões efetivas. A linha pontilhada indica o passivo acumulado no período.</div>', unsafe_allow_html=True)

            df_fluxo = met.gerar_serie_entradas_vs_saidas(df_op_dash)
            if df_fluxo.empty:
                st.info("Sem movimentações registradas no período para gerar o gráfico de fluxo.")
            else:
                fig_fluxo = go.Figure()
                fig_fluxo.add_trace(
                    go.Bar(
                        x=df_fluxo["data_str"],
                        y=df_fluxo["entradas"],
                        name="📥 Entradas Diárias",
                        marker_color="#38BDF8",
                        text=df_fluxo["entradas"],
                        textposition="outside",
                        textfont=dict(color="#38BDF8", size=11, family="sans-serif"),
                        cliponaxis=False,
                    )
                )
                fig_fluxo.add_trace(
                    go.Bar(
                        x=df_fluxo["data_str"],
                        y=df_fluxo["saidas"],
                        name="📤 Conclusões (Saídas)",
                        marker_color="#10B981",
                        text=df_fluxo["saidas"],
                        textposition="outside",
                        textfont=dict(color="#10B981", size=11, family="sans-serif"),
                        cliponaxis=False,
                    )
                )
                fig_fluxo.add_trace(
                    go.Scatter(
                        x=df_fluxo["data_str"],
                        y=df_fluxo["passivo_acumulado"],
                        name="📊 Passivo Acumulado Líquido",
                        mode="lines+markers+text",
                        text=df_fluxo["passivo_acumulado"].apply(lambda v: f"{v:+d}"),
                        textposition="top center",
                        textfont=dict(color="#FCA5A5", size=11, family="sans-serif"),
                        line=dict(color="#F87171", width=3, dash="dot"),
                        marker=dict(size=8, color="#EF4444"),
                        yaxis="y2",
                        cliponaxis=False,
                    )
                )
                max_vol = max(int(df_fluxo["entradas"].max()), int(df_fluxo["saidas"].max()), 1)
                fig_fluxo.update_layout(
                    barmode="group",
                    height=440,
                    margin=dict(l=60, r=60, t=70, b=90, autoexpand=True),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.06,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12, color="#E2E8F0"),
                    ),
                    xaxis=dict(
                        title=dict(text="Data do Movimento", standoff=15, font=dict(color="#E2E8F0")),
                        tickangle=-45,
                        automargin=True,
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.12)",
                        tickfont=dict(color="#CBD5E1", size=11),
                    ),
                    yaxis=dict(
                        title=dict(text="Volume Diário de Demandas", standoff=15, font=dict(color="#38BDF8")),
                        range=[0, max_vol * 1.25],
                        automargin=True,
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.12)",
                        tickfont=dict(color="#CBD5E1", size=11),
                    ),
                    yaxis2=dict(
                        title=dict(text="Passivo Acumulado Líquido", standoff=15, font=dict(color="#F87171")),
                        overlaying="y",
                        side="right",
                        automargin=True,
                        showgrid=False,
                        tickfont=dict(color="#F87171", size=11),
                    ),
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="sans-serif", color="#E2E8F0"),
                )
                st.plotly_chart(fig_fluxo, use_container_width=True)

                tot_ent = int(df_fluxo['entradas'].sum())
                tot_sai = int(df_fluxo['saidas'].sum())
                saldo_final = int(df_fluxo['passivo_acumulado'].iloc[-1])
                c_inf1, c_inf2, c_inf3 = st.columns(3)
                with c_inf1:
                    st.markdown(f"<div class='info-pill'>📥 <b>Total Entradas no Período:</b> {tot_ent} demandas</div>", unsafe_allow_html=True)
                with c_inf2:
                    st.markdown(f"<div class='info-pill'>📤 <b>Total Conclusões no Período:</b> {tot_sai} demandas</div>", unsafe_allow_html=True)
                with c_inf3:
                    if saldo_final <= 0:
                        st.markdown(f"<div class='info-pill-success'>✅ <b>Vazão Positiva:</b> Saldo {saldo_final:+d} demandas</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='info-pill-warning'>⚠️ <b>Passivo em Aberto:</b> Saldo {saldo_final:+d} demandas</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # PRODUTIVIDADE E CONTABILIDADE COMPLETA POR ANALISTA
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.markdown('<div class="panel-header-title">👥 Produtividade Individual e Contabilidade Completa por Analista</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-header-desc">Desempenho por analista considerando todas as demandas distribuídas (Subsídios regulares e urgentes, Obrigações de fazer regulares e urgentes) e taxa de conclusão vs. meta (80%).</div>', unsafe_allow_html=True)

            df_prod_analistas = met.gerar_produtividade_por_analista(df_op_dash)
            if df_prod_analistas.empty:
                st.info("Nenhuma demanda atribuída a analistas no período filtrado.")
            else:
                df_prod_analistas["rotulo_barra"] = df_prod_analistas.apply(
                    lambda r: f"{r['produtividade_pct']:.1f}% ({r['total_concluido']}/{r['total_distribuido']} concl. • Urg: {r.get('total_urgentes', 0)})",
                    axis=1
                )
                fig_analistas = px.bar(
                    df_prod_analistas,
                    x="produtividade_pct",
                    y="analista_nome",
                    orientation="h",
                    text="rotulo_barra",
                    color="atingiu_meta",
                    color_discrete_map={
                        "Sim (>= 80%)": "#10B981",
                        "Não (< 80%)": "#F59E0B",
                    },
                    labels={
                        "produtividade_pct": "Taxa de Produtividade (%)",
                        "analista_nome": "",
                        "atingiu_meta": "Status da Meta",
                    },
                )
                fig_analistas.add_vline(
                    x=80,
                    line_width=2.5,
                    line_dash="dash",
                    line_color="#EF4444",
                    annotation_text="Meta Corporativa (80%)",
                    annotation_position="top right",
                    annotation_font=dict(color="#EF4444", size=12),
                )
                fig_analistas.update_traces(
                    textposition="outside",
                    textfont=dict(color="#F1F5F9", size=12, family="sans-serif"),
                    cliponaxis=False,
                )
                altura_graf = max(340, len(df_prod_analistas) * 65 + 100)
                fig_analistas.update_layout(
                    height=altura_graf,
                    margin=dict(l=220, r=40, t=55, b=45, autoexpand=True),
                    xaxis=dict(
                        range=[0, 155],
                        title=dict(text="Taxa de Produtividade (%)", standoff=12, font=dict(color="#E2E8F0")),
                        automargin=True,
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.12)",
                        tickfont=dict(color="#CBD5E1", size=11),
                    ),
                    yaxis=dict(
                        autorange="reversed",
                        automargin=True,
                        tickfont=dict(size=12, color="#F1F5F9", family="sans-serif"),
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.05,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12, color="#E2E8F0"),
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="sans-serif", color="#E2E8F0"),
                )
                st.plotly_chart(fig_analistas, use_container_width=True)

                col_res1, col_res2, col_res3 = st.columns(3)
                with col_res1:
                    total_analistas_count = len(df_prod_analistas)
                    analistas_meta = len(df_prod_analistas[df_prod_analistas["atingiu_meta"] == "Sim (>= 80%)"])
                    st.markdown(f"<div class='info-pill-success'>🎯 <b>Cumprimento de Meta:</b> {analistas_meta} de {total_analistas_count} analistas (>=80%)</div>", unsafe_allow_html=True)
                with col_res2:
                    media_prod = round(float(df_prod_analistas["produtividade_pct"].mean()), 1)
                    st.markdown(f"<div class='info-pill'>📊 <b>Média da Equipe:</b> {media_prod}% de produtividade</div>", unsafe_allow_html=True)
                with col_res3:
                    tot_urg_an = int(df_prod_analistas["total_urgentes"].sum()) if "total_urgentes" in df_prod_analistas.columns else 0
                    st.markdown(f"<div class='info-pill'>🚨 <b>Total Urgências Atendidas:</b> {tot_urg_an} demandas</div>", unsafe_allow_html=True)

                st.markdown("##### 📋 Tabela de Contabilidade e Produtividade Detalhada por Analista")
                df_tabela_exibicao = df_prod_analistas.copy()
                if "total_subsidios_urgente" in df_tabela_exibicao.columns:
                    df_tabela_exibicao["subsidios_comuns"] = df_tabela_exibicao["total_subsidios"] - df_tabela_exibicao["total_subsidios_urgente"]
                else:
                    df_tabela_exibicao["subsidios_comuns"] = df_tabela_exibicao["total_subsidios"]

                if "total_obrigacao_fazer_urgente" in df_tabela_exibicao.columns:
                    df_tabela_exibicao["obrigacao_comum"] = df_tabela_exibicao["total_obrigacao_fazer"] - df_tabela_exibicao["total_obrigacao_fazer_urgente"]
                else:
                    df_tabela_exibicao["obrigacao_comum"] = df_tabela_exibicao["total_obrigacao_fazer"]

                cols_show = [
                    "analista_nome",
                    "total_distribuido",
                    "subsidios_comuns",
                    "total_subsidios_urgente",
                    "obrigacao_comum",
                    "total_obrigacao_fazer_urgente",
                    "total_urgentes",
                    "total_pendencias_anteriores",
                    "total_concluido",
                    "total_pendente",
                    "produtividade_pct",
                    "atingiu_meta",
                ]
                cols_existentes = [c for c in cols_show if c in df_tabela_exibicao.columns]
                st.dataframe(
                    df_tabela_exibicao[cols_existentes],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "analista_nome": st.column_config.TextColumn("Analista Responsável"),
                        "total_distribuido": st.column_config.NumberColumn("Total Distribuído"),
                        "subsidios_comuns": st.column_config.NumberColumn("Subsídios Comuns"),
                        "total_subsidios_urgente": st.column_config.NumberColumn("Subsídios Urgentes 🚨"),
                        "obrigacao_comum": st.column_config.NumberColumn("Obrigação Comum"),
                        "total_obrigacao_fazer_urgente": st.column_config.NumberColumn("Obrigação Urgente ⚡"),
                        "total_urgentes": st.column_config.NumberColumn("Total Urgentes"),
                        "total_pendencias_anteriores": st.column_config.NumberColumn("Pend. Anteriores"),
                        "total_concluido": st.column_config.NumberColumn("Concluídas no Dia"),
                        "total_pendente": st.column_config.NumberColumn("Saldo Pendente"),
                        "produtividade_pct": st.column_config.NumberColumn("Produtividade (%)", format="%.1f%%"),
                        "atingiu_meta": st.column_config.TextColumn("Meta (>=80%)"),
                    },
                )

        # ----------------------------------------------------------------------
        # KGIs OPERACIONAIS (URGÊNCIAS E CICLO SEMANAL)
        # ----------------------------------------------------------------------
        st.markdown("#### 🎯 Indicadores Estratégicos Operacionais (KGIs)")
        col_kgi_op1, col_kgi_op2 = st.columns(2)
        with col_kgi_op1:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">🎯 KGI 1: Tempestividade de Urgências e Risco de Multa</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Percentual de urgências resolvidas tempestivamente (Meta: 100%).</div>', unsafe_allow_html=True)
                val_kgi1 = float(kpis_op["kgi1_urgencia_multa_pct"])
                fig_g1 = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=val_kgi1,
                        domain={"x": [0.05, 0.95], "y": [0.05, 0.95]},
                        number={"font": {"size": 34, "color": "#F8FAFC"}, "suffix": "%"},
                        delta={"reference": 100, "increasing": {"color": "#10B981"}},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "tickfont": {"color": "#CBD5E1", "size": 10}},
                            "bar": {"color": "#38BDF8", "thickness": 0.28},
                            "bgcolor": "rgba(0,0,0,0)",
                            "borderwidth": 1,
                            "bordercolor": "rgba(148, 163, 184, 0.3)",
                            "steps": [
                                {"range": [0, 70], "color": "rgba(239, 68, 68, 0.35)"},
                                {"range": [70, 90], "color": "rgba(245, 158, 11, 0.35)"},
                                {"range": [90, 100], "color": "rgba(16, 185, 129, 0.35)"},
                            ],
                            "threshold": {
                                "line": {"color": "#EF4444", "width": 4},
                                "thickness": 0.75,
                                "value": 100,
                            },
                        },
                    )
                )
                fig_g1.update_layout(
                    height=220,
                    margin=dict(l=20, r=20, t=15, b=20, autoexpand=True),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_g1, use_container_width=True)
                k1_temp = kpis_op['kgi1_tempestivas']
                k1_tot = kpis_op['kgi1_total_urgentes_concluidas']
                st.markdown(f"<div class='info-pill'>📋 <b>Amostra:</b> {k1_temp} de {k1_tot} tempestivas</div>", unsafe_allow_html=True)
                if val_kgi1 >= 100.0:
                    st.markdown("<div class='info-pill-success'>✅ <b>100% no Prazo:</b> Risco de multa diária eliminado</div>", unsafe_allow_html=True)
                else:
                    atraso = k1_tot - k1_temp
                    st.markdown(f"<div class='info-pill-warning'>⚠️ <b>Atenção:</b> {atraso} demandas fora do prazo de segurança</div>", unsafe_allow_html=True)

        with col_kgi_op2:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">📅 KGI 2: Cumprimento de Ciclo Semanal</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Percentual de conclusões realizadas na mesma semana de recebimento (Meta: 85%).</div>', unsafe_allow_html=True)
                kgi2_pct = float(kpis_op["kgi2_conclusao_semanal_pct"])
                fig_kgi2 = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=kgi2_pct,
                        domain={"x": [0.05, 0.95], "y": [0.05, 0.95]},
                        number={"font": {"size": 34, "color": "#F8FAFC"}, "suffix": "%"},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "tickfont": {"color": "#CBD5E1", "size": 10}},
                            "bar": {"color": "#38BDF8", "thickness": 0.28},
                            "bgcolor": "rgba(0,0,0,0)",
                            "borderwidth": 1,
                            "bordercolor": "rgba(148, 163, 184, 0.3)",
                            "steps": [
                                {"range": [0, 70], "color": "rgba(239, 68, 68, 0.35)"},
                                {"range": [70, 85], "color": "rgba(245, 158, 11, 0.35)"},
                                {"range": [85, 100], "color": "rgba(16, 185, 129, 0.35)"},
                            ],
                            "threshold": {
                                "line": {"color": "#10B981", "width": 4},
                                "thickness": 0.75,
                                "value": 85,
                            },
                        },
                    )
                )
                fig_kgi2.update_layout(
                    height=220,
                    margin=dict(l=20, r=20, t=15, b=20, autoexpand=True),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_kgi2, use_container_width=True)
                c_sem1, c_sem2 = st.columns(2)
                with c_sem1:
                    st.markdown(f"<div class='info-pill-success'>✅ <b>Na Mesma Semana:</b> {kpis_op['kgi2_mesma_semana']} demandas</div>", unsafe_allow_html=True)
                with c_sem2:
                    diff_sem = kpis_op['kgi2_total_concluidas'] - kpis_op['kgi2_mesma_semana']
                    st.markdown(f"<div class='info-pill'>⏳ <b>Semanas Seguintes:</b> {diff_sem} demandas</div>", unsafe_allow_html=True)

    # ==========================================================================
    # SUB-ABA 2: AÇÕES MANDAMENTAIS (MS, HC, HD)
    # ==========================================================================
    with subtab_mandamentais:
        df_mand_dash = db.get_df_acoes_mandamentais(
            data_inicio=filtro_data_inicio,
            data_fim=filtro_data_fim,
            id_analista=filtro_id_analista,
            tipo_acao=tipo_produto_filtro if tipo_produto_filtro in ["MS", "HC", "HD"] else None,
            apenas_liminares=apenas_urgentes,
        )
        kpis_mand = met.calcular_kpis_mandamentais(df_mand_dash)

        st.markdown("#### 📜 Contabilidade Executiva e Análises Estratégicas: Ações Mandamentais (MS, HC, HD)")
        st.caption("Acompanhamento das ações mandamentais, gestão de pedidos liminares e taxa de êxito da advocacia pública.")

        # ----------------------------------------------------------------------
        # CARDS EXECUTIVOS MANDAMENTAIS (4 Cards)
        # ----------------------------------------------------------------------
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric(
                label="🏛️ Total Ações Mandamentais",
                value=f"{kpis_mand['total_impetracoes']}",
                delta=f"MS: {kpis_mand['total_ms']} • HC: {kpis_mand['total_hc']} • HD: {kpis_mand['total_hd']}",
                delta_color="off",
                help="Total de ações mandamentais impetradas/conduzidas no período",
            )
        with col_m2:
            st.metric(
                label="⚡ Liminares e Casos Urgentes",
                value=f"{kpis_mand['total_liminares_urgentes']}",
                delta=f"{kpis_mand['hc_liminares_tempestivas']}/{kpis_mand['total_hc_liminares']} manifestados em 24h",
                delta_color="normal" if kpis_mand['kgi_tempestividade_hc_liminares_pct'] >= 100.0 else "inverse",
                help="Pedidos liminares de MS/HD ou rito sumaríssimo de Habeas Corpus",
            )
        with col_m3:
            exito_val = kpis_mand['kgi_taxa_exito_ms_pct']
            st.metric(
                label="⚖️ Taxa de Êxito em MS",
                value=f"{exito_val}%",
                delta=f"{kpis_mand['ms_favoraveis_total']} favoráveis de {kpis_mand['ms_sentenciados_total']} sentenças",
                delta_color="normal" if exito_val >= 75.0 else "inverse",
                help="Percentual de sentenças favoráveis à Administração (Denegado ou Sem Resolução)",
            )
        with col_m4:
            st.metric(
                label="⏳ Fase de Julgamento",
                value=f"{kpis_mand['total_sentenciadas']} Julgadas",
                delta=f"{kpis_mand['total_em_elaboracao'] + kpis_mand['total_aguardando_julgamento']} em tramitação",
                delta_color="off",
                help="Ações sentenciadas versus ações em elaboração / aguardando julgamento",
            )

        st.divider()

        # ----------------------------------------------------------------------
        # COMPOSIÇÃO POR TIPO DE AÇÃO MANDAMENTAL E STATUS PROCESSUAL
        # ----------------------------------------------------------------------
        col_graf_m1, col_graf_m2 = st.columns([1, 1.2])

        with col_graf_m1:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">🥧 Composição por Tipo de Ação Mandamental</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Distribuição de impetrações entre MS, HC e HD.</div>', unsafe_allow_html=True)

                if kpis_mand['total_impetracoes'] > 0:
                    df_tipo_m = pd.DataFrame([
                        {"tipo": "Mandado de Segurança (MS)", "quantidade": kpis_mand['total_ms']},
                        {"tipo": "Habeas Corpus (HC)", "quantidade": kpis_mand['total_hc']},
                        {"tipo": "Habeas Data (HD)", "quantidade": kpis_mand['total_hd']},
                    ])
                    df_tipo_m_filt = df_tipo_m[df_tipo_m["quantidade"] > 0]
                    if not df_tipo_m_filt.empty:
                        fig_donut_m = px.pie(
                            df_tipo_m_filt,
                            names="tipo",
                            values="quantidade",
                            hole=0.52,
                            color="tipo",
                            color_discrete_map={
                                "Mandado de Segurança (MS)": "#38BDF8",
                                "Habeas Corpus (HC)": "#F43F5E",
                                "Habeas Data (HD)": "#A78BFA",
                            },
                        )
                        fig_donut_m.update_traces(
                            textposition="inside",
                            textinfo="percent+value",
                            textfont=dict(size=12, color="#FFFFFF", family="sans-serif"),
                        )
                        fig_donut_m.update_layout(
                            height=280,
                            margin=dict(l=20, r=20, t=30, b=20, autoexpand=True),
                            paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5,
                                font=dict(size=11, color="#E2E8F0"),
                            ),
                            font=dict(family="sans-serif", color="#E2E8F0"),
                        )
                        st.plotly_chart(fig_donut_m, use_container_width=True)
                    else:
                        st.info("Sem ações mandamentais no filtro.")
                else:
                    st.info("Sem ações mandamentais no período.")

        with col_graf_m2:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">📊 Status da Fase Processual / Tramitação</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Volume de ações por estágio no Poder Judiciário.</div>', unsafe_allow_html=True)

                if kpis_mand['total_impetracoes'] > 0:
                    df_status_m = pd.DataFrame([
                        {"status": "Em Elaboração", "quantidade": kpis_mand['total_em_elaboracao']},
                        {"status": "Aguardando Julgamento", "quantidade": kpis_mand['total_aguardando_julgamento']},
                        {"status": "Transitado em Julgado", "quantidade": kpis_mand['total_transitado_julgado']},
                    ])
                    fig_bar_status = px.bar(
                        df_status_m,
                        x="quantidade",
                        y="status",
                        orientation="h",
                        text="quantidade",
                        color="status",
                        color_discrete_map={
                            "Em Elaboração": "#F59E0B",
                            "Aguardando Julgamento": "#38BDF8",
                            "Transitado em Julgado": "#10B981",
                        },
                        labels={"quantidade": "Total de Processos", "status": ""},
                    )
                    fig_bar_status.update_traces(
                        textposition="outside",
                        textfont=dict(color="#F1F5F9", size=12, family="sans-serif"),
                        cliponaxis=False,
                    )
                    max_st = max(int(df_status_m["quantidade"].max()), 1)
                    fig_bar_status.update_layout(
                        height=280,
                        margin=dict(l=160, r=40, t=30, b=40, autoexpand=True),
                        showlegend=False,
                        xaxis=dict(
                            range=[0, max_st * 1.35],
                            title=dict(text="Quantidade de Processos", standoff=10, font=dict(color="#E2E8F0")),
                            showgrid=True,
                            gridcolor="rgba(148, 163, 184, 0.12)",
                            tickfont=dict(color="#CBD5E1", size=11),
                        ),
                        yaxis=dict(
                            tickfont=dict(color="#F1F5F9", size=12),
                            autorange="reversed",
                        ),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="sans-serif", color="#E2E8F0"),
                    )
                    st.plotly_chart(fig_bar_status, use_container_width=True)
                else:
                    st.info("Sem processos em tramitação no período.")

        # ----------------------------------------------------------------------
        # INDICADORES ESTRATÉGICOS MANDAMENTAIS (KGIs)
        # ----------------------------------------------------------------------
        st.markdown("#### 🎯 Indicadores Estratégicos Mandamentais (KGIs)")
        col_kgi_m1, col_kgi_m2 = st.columns(2)

        with col_kgi_m1:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">⚖️ KGI MS: Taxa de Êxito Anual</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Sentenças favoráveis (Denegado ou Sem Resolução) vs. total de sentenças em MS (Meta: >= 75%).</div>', unsafe_allow_html=True)
                val_exito_ms = float(kpis_mand["kgi_taxa_exito_ms_pct"])
                fig_g_ms = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=val_exito_ms,
                        domain={"x": [0.05, 0.95], "y": [0.05, 0.95]},
                        number={"font": {"size": 34, "color": "#F8FAFC"}, "suffix": "%"},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "tickfont": {"color": "#CBD5E1", "size": 10}},
                            "bar": {"color": "#60A5FA", "thickness": 0.28},
                            "bgcolor": "rgba(0,0,0,0)",
                            "borderwidth": 1,
                            "bordercolor": "rgba(148, 163, 184, 0.3)",
                            "steps": [
                                {"range": [0, 50], "color": "rgba(239, 68, 68, 0.35)"},
                                {"range": [50, 75], "color": "rgba(245, 158, 11, 0.35)"},
                                {"range": [75, 100], "color": "rgba(16, 185, 129, 0.35)"},
                            ],
                            "threshold": {
                                "line": {"color": "#10B981", "width": 4},
                                "thickness": 0.75,
                                "value": 75,
                            },
                        },
                    )
                )
                fig_g_ms.update_layout(
                    height=220,
                    margin=dict(l=20, r=20, t=15, b=20, autoexpand=True),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_g_ms, use_container_width=True)
                fav = kpis_mand['ms_favoraveis_total']
                tot_sent = kpis_mand['ms_sentenciados_total']
                st.markdown(f"<div class='info-pill'>⚖️ <b>Sentenças MS:</b> {fav} de {tot_sent} favoráveis</div>", unsafe_allow_html=True)
                if val_exito_ms >= 75.0:
                    st.markdown("<div class='info-pill-success'>✅ <b>Resultado Favorável:</b> Meta corporativa atingida (>= 75%)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='info-pill-warning'>⚠️ <b>Taxa Atual:</b> {val_exito_ms}% em sentenças</div>", unsafe_allow_html=True)

        with col_kgi_m2:
            with st.container(border=True):
                st.markdown('<div class="panel-header-title">⚡ KGI HC: Prontidão e Tempestividade em até 24h</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-header-desc">Manifestação prestada em até 24 horas do recebimento (Meta: 100%).</div>', unsafe_allow_html=True)
                val_temp_hc = float(kpis_mand["kgi_tempestividade_hc_liminares_pct"])
                fig_g_hc = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=val_temp_hc,
                        domain={"x": [0.05, 0.95], "y": [0.05, 0.95]},
                        number={"font": {"size": 34, "color": "#F8FAFC"}, "suffix": "%"},
                        delta={"reference": 100},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "tickfont": {"color": "#CBD5E1", "size": 10}},
                            "bar": {"color": "#A78BFA", "thickness": 0.28},
                            "bgcolor": "rgba(0,0,0,0)",
                            "borderwidth": 1,
                            "bordercolor": "rgba(148, 163, 184, 0.3)",
                            "steps": [
                                {"range": [0, 80], "color": "rgba(239, 68, 68, 0.35)"},
                                {"range": [80, 95], "color": "rgba(245, 158, 11, 0.35)"},
                                {"range": [95, 100], "color": "rgba(16, 185, 129, 0.35)"},
                            ],
                            "threshold": {
                                "line": {"color": "#EF4444", "width": 4},
                                "thickness": 0.75,
                                "value": 100,
                            },
                        },
                    )
                )
                fig_g_hc.update_layout(
                    height=220,
                    margin=dict(l=20, r=20, t=15, b=20, autoexpand=True),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_g_hc, use_container_width=True)
                hc_temp = kpis_mand['hc_liminares_tempestivas']
                hc_tot = kpis_mand['total_hc_liminares']
                st.markdown(f"<div class='info-pill'>⚡ <b>Prazos Sumaríssimos:</b> {hc_temp} de {hc_tot} em até 24h</div>", unsafe_allow_html=True)
                if val_temp_hc >= 100.0:
                    st.markdown("<div class='info-pill-success'>✅ <b>100% Tempestivo:</b> Prontidão plena na defesa</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='info-pill-warning'>⚠️ <b>Atenção:</b> {hc_tot - hc_temp} manifestações fora de 24h</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # ANÁLISE DE MÉRITO DAS SENTENÇAS (MS)
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.markdown('<div class="panel-header-title">⚖️ Análise de Mérito das Sentenças Judiciais em Mandados de Segurança</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-header-desc">Detalhamento dos provimentos jurisdicionais de mérito proferidos pelos magistrados.</div>', unsafe_allow_html=True)

            if kpis_mand['total_sentenciadas'] > 0:
                df_merito = pd.DataFrame([
                    {"resultado": "Favorável (Denegado)", "quantidade": kpis_mand['ms_denegados'], "categoria": "Favorável"},
                    {"resultado": "Sem Resolução de Mérito", "quantidade": kpis_mand['ms_sem_resolucao'], "categoria": "Favorável"},
                    {"resultado": "Desfavorável (Concedido)", "quantidade": kpis_mand['ms_concedidos'], "categoria": "Desfavorável"},
                    {"resultado": "Pendente de Sentença", "quantidade": kpis_mand['ms_pendentes_sentenca'], "categoria": "Pendente"},
                ])
                fig_merito = px.bar(
                    df_merito,
                    x="resultado",
                    y="quantidade",
                    text="quantidade",
                    color="categoria",
                    color_discrete_map={
                        "Favorável": "#10B981",
                        "Desfavorável": "#EF4444",
                        "Pendente": "#F59E0B",
                    },
                    labels={"resultado": "Resultado Judicial", "quantidade": "Total de Sentenças", "categoria": "Efeito"},
                )
                fig_merito.update_traces(
                    textposition="outside",
                    textfont=dict(color="#F1F5F9", size=12, family="sans-serif"),
                    cliponaxis=False,
                )
                max_m = max(int(df_merito["quantidade"].max()), 1)
                fig_merito.update_layout(
                    height=320,
                    margin=dict(l=40, r=40, t=35, b=50, autoexpand=True),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.04,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12, color="#E2E8F0"),
                    ),
                    xaxis=dict(
                        tickfont=dict(size=11, color="#CBD5E1"),
                        showgrid=False,
                    ),
                    yaxis=dict(
                        range=[0, max_m * 1.3],
                        title=dict(text="Total de Processos", standoff=10, font=dict(color="#E2E8F0")),
                        showgrid=True,
                        gridcolor="rgba(148, 163, 184, 0.12)",
                        tickfont=dict(color="#CBD5E1", size=11),
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="sans-serif", color="#E2E8F0"),
                )
                st.plotly_chart(fig_merito, use_container_width=True)
            else:
                st.info("Sem sentenças judiciais registradas em Mandados de Segurança no período.")

        # ----------------------------------------------------------------------
        # PRODUTIVIDADE DOS ANALISTAS EM AÇÕES MANDAMENTAIS
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.markdown('<div class="panel-header-title">👥 Produtividade e Desempenho dos Analistas em Ações Mandamentais</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-header-desc">Total de ações conduzidas, manifestações prestadas, tempestividade em 24h e taxa de sentenças favoráveis por analista.</div>', unsafe_allow_html=True)

            df_mand_analistas = met.gerar_produtividade_mandamentais_por_analista(df_mand_dash)
            if df_mand_analistas.empty:
                st.info("Nenhuma ação mandamental atribuída a analistas no período.")
            else:
                st.dataframe(
                    df_mand_analistas,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "analista_nome": st.column_config.TextColumn("Analista Responsável"),
                        "total_acoes": st.column_config.NumberColumn("Total Ações Conduzidas"),
                        "total_ms": st.column_config.NumberColumn("MS"),
                        "total_hc": st.column_config.NumberColumn("HC"),
                        "total_hd": st.column_config.NumberColumn("HD"),
                        "total_liminares": st.column_config.NumberColumn("Liminares / Urgências ⚡"),
                        "total_manifestacoes": st.column_config.NumberColumn("Manifestações Prestadas"),
                        "taxa_tempestividade_pct": st.column_config.NumberColumn("Tempestividade 24h (%)", format="%.1f%%"),
                        "total_sentenciadas": st.column_config.NumberColumn("Sentenciadas"),
                        "sentencas_favoraveis": st.column_config.NumberColumn("Sentenças Favoráveis"),
                        "taxa_exito_pct": st.column_config.NumberColumn("Taxa Êxito (%)", format="%.1f%%"),
                    },
                )

        # ----------------------------------------------------------------------
        # CONSULTA RÁPIDA AOS PROCESSOS MANDAMENTAIS DO PERÍODO
        # ----------------------------------------------------------------------
        with st.expander("🔍 Consulta Rápida aos Processos Mandamentais do Período", expanded=False):
            if not df_mand_dash.empty:
                cols_consulta = [
                    "numero_processo", "tipo_acao", "analista_nome", "data_entrada",
                    "data_prazo_liminar", "status_tramitacao", "data_sentenca", "resultado_merito"
                ]
                cols_exist = [c for c in cols_consulta if c in df_mand_dash.columns]
                st.dataframe(
                    df_mand_dash[cols_exist],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "numero_processo": st.column_config.TextColumn("Nº Processo CNJ"),
                        "tipo_acao": st.column_config.TextColumn("Tipo"),
                        "analista_nome": st.column_config.TextColumn("Analista"),
                        "data_entrada": st.column_config.DateColumn("Entrada", format="DD/MM/YYYY"),
                        "data_prazo_liminar": st.column_config.DateColumn("Prazo Liminar", format="DD/MM/YYYY"),
                        "status_tramitacao": st.column_config.TextColumn("Tramitação"),
                        "data_sentenca": st.column_config.DateColumn("Sentença", format="DD/MM/YYYY"),
                        "resultado_merito": st.column_config.TextColumn("Resultado do Mérito"),
                    },
                )
            else:
                st.info("Nenhuma ação mandamental encontrada com os filtros atuais.")



# ==============================================================================
# ABA 4: AUTOMAÇÃO E INTEGRAÇÕES (PLACEHOLDER FUNCIONAL)
# ==============================================================================
with tab_automacao:
    st.markdown("### ⚙️ Automação Inteligente e Central de Exportação")
    st.caption("Módulos preparados para acelerar rotinas jurídicas, processamento automatizado e relatórios.")

    sub_aut1, sub_aut2, sub_aut3 = st.tabs([
        "🤖 Leitor Inteligente de Despacho/Intimação (OCR/Regex)",
        "📊 Central de Exportação (Excel / CSV)",
        "🛠️ Ferramentas Administrativas",
    ])

    # 1. PARSER INTELIGENTE DE DESPACHO
    with sub_aut1:
        st.markdown("#### 📄 Extração Automática de Metadados de Intimações Judiciais")
        st.write("Faça o upload de uma intimação ou despacho judicial em **PDF** ou cole o teor do despacho para que o sistema identifique automaticamente o número do processo, urgência, imposição de multa e tipo de demanda.")

        col_up1, col_up2 = st.columns([1, 1])
        texto_para_analise = ""

        with col_up1:
            arquivo_pdf = st.file_uploader("Upload de Despacho/Intimação Judicial (PDF)", type=["pdf"])
            if arquivo_pdf is not None:
                try:
                    import pypdf
                    pdf_reader = pypdf.PdfReader(arquivo_pdf)
                    paginas_texto = []
                    for pag in pdf_reader.pages:
                        extracted = pag.extract_text()
                        if extracted:
                            paginas_texto.append(extracted)
                    texto_para_analise = "\n".join(paginas_texto)
                    st.success(f"PDF carregado com sucesso! ({len(pdf_reader.pages)} páginas extraídas)")
                except ImportError:
                    st.warning("Biblioteca 'pypdf' não instalada. Para habilitar upload de PDF, execute 'pip install pypdf'. Você pode colar o texto ao lado.")
                except Exception as ex_pdf:
                    st.error(f"Erro ao ler PDF: {ex_pdf}")

        with col_up2:
            texto_colado = st.text_area(
                "Ou cole o texto da intimação judicial:",
                placeholder="Ex: 'Vistos. Trata-se de tutela de urgência no processo 0812345-67.2024.8.19.0001 requerendo o fornecimento de medicamento sob pena de multa diária de R$ 1.000,00...'",
                height=130,
            )
            if texto_colado.strip():
                texto_para_analise = texto_colado.strip()

        if texto_para_analise:
            st.markdown("##### 🔍 Diagnóstico Automatizado do Despacho:")

            # Regex para CNJ
            padrao_cnj = r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"
            matches_cnj = re.findall(padrao_cnj, texto_para_analise)
            cnj_detectado = matches_cnj[0] if matches_cnj else "Não detectado"

            # Detecção de Urgência
            termos_urgencia = ["URGENTE", "TUTELA DE URGÊNCIA", "LIMINAR", "PLANTÃO", "ANTECIPAÇÃO DOS EFEITOS DA TUTELA", "IMINENTE RISCO"]
            detectou_urgencia = any(t in texto_para_analise.upper() for t in termos_urgencia)

            # Detecção de Multa
            termos_multa = ["MULTA DIÁRIA", "ASTREINTE", "SOB PENA DE MULTA", "FIXO A MULTA", "PENA DE COMINAÇÃO", "MULTA COMINATÓRIA"]
            detectou_multa = any(t in texto_para_analise.upper() for t in termos_multa)

            # Sugestão de Tipo de Produto
            texto_upper = texto_para_analise.upper()
            if "MANDADO DE SEGURANÇA" in texto_upper:
                tipo_sugerido = "MS"
                tipo_classe = "Mandamental"
            elif "HABEAS CORPUS" in texto_upper:
                tipo_sugerido = "HC"
                tipo_classe = "Mandamental"
            elif "HABEAS DATA" in texto_upper:
                tipo_sugerido = "HD"
                tipo_classe = "Mandamental"
            elif "SUBSÍDIO" in texto_upper or "SUBSIDIOS" in texto_upper or "INFORMAÇÕES TÉCNICAS" in texto_upper:
                tipo_sugerido = "Subsídios"
                tipo_classe = "Operacional"
            else:
                tipo_sugerido = "Obrigação de Fazer"
                tipo_classe = "Operacional"

            col_diag1, col_diag2, col_diag3, col_diag4 = st.columns(4)
            with col_diag1:
                st.write(f"**Processo CNJ:** `{cnj_detectado}`")
            with col_diag2:
                st.write(f"**Urgência:** {'🚨 SIM' if detectou_urgencia else 'Não'}")
            with col_diag3:
                st.write(f"**Multa/Astreinte:** {'⚠️ SIM' if detectou_multa else 'Não'}")
            with col_diag4:
                st.write(f"**Produto Sugerido:** `{tipo_sugerido}`")

            if cnj_detectado != "Não detectado":
                st.markdown("###### Deseja cadastrar esta demanda diretamente a partir da extração?")
                if st.button("⚡ Confirmar Cadastro Imediato no Banco de Dados", type="primary"):
                    try:
                        if tipo_classe == "Operacional":
                            db.add_demanda_operacional(
                                numero_processo=cnj_detectado,
                                tipo_produto=tipo_sugerido,
                                data_recebimento=hoje,
                                hora_recebimento=datetime.now().time().replace(microsecond=0),
                                is_urgente=detectou_urgencia,
                                possui_multa=detectou_multa,
                                status="Não Distribuído",
                                observacoes=f"Extraído via automação de documento: {texto_para_analise[:180]}...",
                            )
                        else:
                            db.add_acao_mandamental(
                                numero_processo=cnj_detectado,
                                tipo_acao=tipo_sugerido,
                                data_entrada=hoje,
                                is_urgente_liminar=detectou_urgencia,
                                status_tramitacao="Em Elaboração",
                            )
                        st.success(f"Demanda {cnj_detectado} importada com sucesso na fila!")
                        safe_rerun()
                    except Exception as err_import:
                        st.error(f"Erro na importação: {err_import}")
            else:
                st.warning("⚠️ Nenhum número no formato CNJ válido foi identificado no texto fornecido.")

    # 2. CENTRAL DE EXPORTAÇÃO
    with sub_aut2:
        st.markdown("#### 📥 Exportação de Dados Tratados")
        st.write("Baixe a base de dados completa nos formatos analíticos corporativos.")

        df_export_aportes = safe_get_df_aportes_diarios()
        df_export_prod = db.get_df_produtividade_operacional()
        df_export_mand = db.get_df_acoes_mandamentais()
        df_export_analistas = met.gerar_produtividade_por_analista(df_export_prod)
        df_cad_analistas = db.get_df_analistas()

        # Formatar datas para dd/mm/aaaa no Excel e CSV
        def _formatar_datas_ptbr(df_alvo, colunas):
            df_copia = df_alvo.copy()
            for col in colunas:
                if col in df_copia.columns:
                    df_copia[col] = df_copia[col].apply(
                        lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") and pd.notna(d) else ("" if pd.isna(d) or str(d).strip() in ("None", "NaT") else str(d))
                    )
            return df_copia

        df_export_aportes_fmt = _formatar_datas_ptbr(df_export_aportes, ["data_aporte"])
        df_export_prod_fmt = _formatar_datas_ptbr(df_export_prod, ["data_referencia"])
        df_export_mand_fmt = _formatar_datas_ptbr(df_export_mand, ["data_entrada", "data_manifestacao", "data_sentenca"])

        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            st.markdown("##### 📑 Exportação Excel (.xlsx)")
            st.write("Gera arquivo Excel multi-abas contendo Aportes Diários, Produtividade Operacional, Ações Mandamentais, Resumo por Analista e Cadastro da Equipe com datas no padrão dd/mm/aaaa.")

            try:
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
                    if not df_export_aportes_fmt.empty:
                        df_export_aportes_fmt.to_excel(writer, sheet_name="Aportes Diários", index=False)
                    df_export_prod_fmt.to_excel(writer, sheet_name="Produtividade Operacional", index=False)
                    df_export_mand_fmt.to_excel(writer, sheet_name="Ações Mandamentais", index=False)
                    df_export_analistas.to_excel(writer, sheet_name="Produtividade por Analista", index=False)
                    df_cad_analistas.to_excel(writer, sheet_name="Equipe de Analistas", index=False)
                buffer_excel.seek(0)

                st.download_button(
                    label="📊 Baixar Relatório Completo (.xlsx)",
                    data=buffer_excel,
                    file_name=f"gestao_juridica_produtividade_{hoje.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except ImportError:
                st.warning("Módulo 'openpyxl' não instalado para gerar arquivos .xlsx. Utilize a exportação .csv ao lado ou instale via 'pip install openpyxl'.")
            except Exception as ex_excel:
                st.error(f"Erro ao gerar Excel: {ex_excel}")

        with col_exp2:
            st.markdown("##### 📄 Exportação CSV (.csv)")
            st.write("Exporta os dados em formato CSV com codificação UTF-8 e compatibilidade com Excel.")

            if not df_export_aportes_fmt.empty:
                csv_ap_data = df_export_aportes_fmt.to_csv(index=False, sep=";", encoding="utf-8-sig")
                st.download_button(
                    label="📥 Baixar Aportes Diários (.csv)",
                    data=csv_ap_data,
                    file_name=f"aportes_diarios_{hoje.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            csv_prod_data = df_export_prod_fmt.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="📥 Baixar Produtividade Operacional (.csv)",
                data=csv_prod_data,
                file_name=f"produtividade_operacional_{hoje.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            csv_mand_data = df_export_mand_fmt.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="📜 Baixar Ações Mandamentais (.csv)",
                data=csv_mand_data,
                file_name=f"acoes_mandamentais_{hoje.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # 3. FERRAMENTAS ADMINISTRATIVAS
    with sub_aut3:
        st.markdown("#### 🛠️ Manutenção do Banco de Dados e Ambiente de Produção")
        st.write("Controles administrativos para manutenção do banco de dados relacional SQLite em ambiente de produção.")

        col_adm1, col_adm2 = st.columns(2)

        with col_adm1:
            st.markdown("##### 📊 Status do Ambiente de Produção")
            tot_ap = safe_count_aportes()
            tot_p = safe_count_produtividade()
            tot_m = safe_count_mandamentais()
            tot_a = safe_count_analistas()
            st.markdown(f"""
            - **Ambiente:** Produção (Ativo 🟢)
            - **Banco de Dados:** SQLite (juridico.db - Modo WAL)
            - **Total de Lançamentos de Aportes Diários:** `{tot_ap}`
            - **Total de Lançamentos de Produtividade:** `{tot_p}`
            - **Total de Ações Mandamentais:** `{tot_m}`
            - **Total de Analistas na Equipe:** `{tot_a}`
            """)

        with col_adm2:
            st.markdown("##### 🗑️ Reinicialização Administrativa da Base")
            st.caption("Caso necessite limpar todos os registros para reiniciar a operação, utilize a opção abaixo com cautela.")
            with st.expander("⚠️ Opções de Limpeza de Dados"):
                st.warning("Atenção: Esta ação remove os registros permanentemente.")
                if st.button("Confirmar Limpeza de Todos os Registros", type="secondary", use_container_width=True):
                    try:
                        if hasattr(db, "clear_all_records"):
                            res_del = db.clear_all_records(keep_analistas=False)
                        else:
                            with db.get_db_session() as session:
                                if hasattr(db, "AporteDiario"):
                                    session.query(db.AporteDiario).delete()
                                p_del = session.query(db.ProdutividadeOperacional).delete() if hasattr(db, "ProdutividadeOperacional") else 0
                                m_del = session.query(db.AcaoMandamental).delete() if hasattr(db, "AcaoMandamental") else 0
                                if hasattr(db, "DemandaOperacional"):
                                    session.query(db.DemandaOperacional).delete()
                                if hasattr(db, "Analista"):
                                    session.query(db.Analista).delete()
                                res_del = {'produtividade_operacional': p_del, 'acoes_mandamentais': m_del}
                        st.success(f"Base de produção reiniciada com sucesso! ({res_del.get('produtividade_operacional', 0)} produtividades e {res_del.get('acoes_mandamentais', 0)} mandamentais removidos)")
                        safe_rerun()
                    except Exception as ex_del:
                        st.error(f"Erro ao limpar banco: {ex_del}")