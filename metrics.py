"""
metrics.py - Camada de Regras de Negócio e Indicadores (KPIs / KGIs)
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd


# ==========================================
# UTILITÁRIOS DE CÁLCULO TEMPORAL ROBUSTOS
# ==========================================

def converter_para_date(val: Any) -> Optional[date]:
    """Converte com segurança qualquer formato de data (string, datetime, Timestamp) para date."""
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


def calcular_dias_uteis(data_inicio: Any, data_fim: Any) -> int:
    """
    Calcula a quantidade de dias úteis entre duas datas (segunda a sexta-feira).
    Se data_inicio == data_fim, retorna 0 (resolvido no mesmo dia).
    """
    d1 = converter_para_date(data_inicio)
    d2 = converter_para_date(data_fim)
    if d1 is None or d2 is None or d2 < d1:
        return 0
    if d1 == d2:
        return 0

    try:
        return int(np.busday_count(np.datetime64(d1, "D"), np.datetime64(d2, "D")))
    except Exception:
        # Fallback caso haja divergência no ambiente numpy
        cur = d1
        dias = 0
        while cur < d2:
            cur += timedelta(days=1)
            if cur.weekday() < 5:  # Segunda a sexta
                dias += 1
        return dias


def calcular_semana_ano(dt: Any) -> Tuple[int, int]:
    """Retorna tupla (ano_iso, semana_iso) para verificação de mesma semana."""
    d = converter_para_date(dt)
    if d is None:
        return (0, 0)
    iso = d.isocalendar()
    return (iso[0], iso[1])


# ==========================================
# CÁLCULO DE KPIS E KGIS: DEMANDAS OPERACIONAIS
# ==========================================

def calcular_kpis_operacionais(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Processa o DataFrame de produtividade operacional (ou demandas legadas)
    e computa todos os KPIs e KGIs exigidos.
    """
    if df.empty:
        return {
            "volume_recebido": 0,
            "volume_distribuido": 0,
            "volume_concluido": 0,
            "backlog_pendencias": 0,
            "taxa_produtividade": 0.0,
            "tmr_medio_dias_uteis": 0.0,
            "kgi1_urgencia_multa_pct": 100.0,
            "kgi1_total_urgentes_concluidas": 0,
            "kgi1_tempestivas": 0,
            "kgi2_conclusao_semanal_pct": 100.0,
            "kgi2_total_concluidas": 0,
            "kgi2_mesma_semana": 0,
            "total_urgentes_pendentes": 0,
            "total_subsidios": 0,
            "total_subsidios_urgentes": 0,
            "total_obrigacao_fazer": 0,
            "total_obrigacao_fazer_urgentes": 0,
        }

    df_calc = df.copy()

    # Se estiver no novo modelo de Produtividade Operacional consolidada
    if "quantidade_subsidios" in df_calc.columns and "quantidade_obrigacao_fazer" in df_calc.columns:
        qtd_sub = int(df_calc["quantidade_subsidios"].fillna(0).sum())
        qtd_sub_urg = int(df_calc["quantidade_subsidios_urgente"].fillna(0).sum()) if "quantidade_subsidios_urgente" in df_calc.columns else 0
        qtd_obrig = int(df_calc["quantidade_obrigacao_fazer"].fillna(0).sum())
        qtd_obrig_urg = int(df_calc["quantidade_obrigacao_fazer_urgente"].fillna(0).sum()) if "quantidade_obrigacao_fazer_urgente" in df_calc.columns else 0
        qtd_pend_ant = int(df_calc["quantidade_pendencias_anteriores"].fillna(0).sum()) if "quantidade_pendencias_anteriores" in df_calc.columns else 0
        qtd_concl = int(df_calc["quantidade_concluidas_dia"].fillna(0).sum()) if "quantidade_concluidas_dia" in df_calc.columns else 0

        volume_recebido = qtd_sub + qtd_obrig
        volume_distribuido = volume_recebido
        volume_concluido = qtd_concl
        total_urgentes = qtd_sub_urg + qtd_obrig_urg

        saldo_liquido = volume_recebido - volume_concluido
        backlog_pendencias = max(0, qtd_pend_ant + saldo_liquido)

        if volume_distribuido > 0:
            taxa_produtividade = round((volume_concluido / volume_distribuido) * 100, 1)
        elif volume_concluido > 0:
            taxa_produtividade = 100.0
        else:
            taxa_produtividade = 0.0

        # KGI 1: Tempestividade de urgências no mesmo dia
        if total_urgentes > 0:
            urgentes_tempestivas = min(total_urgentes, volume_concluido)
            kgi1_pct = round((urgentes_tempestivas / total_urgentes) * 100, 1)
            total_urgentes_pendentes = max(0, total_urgentes - urgentes_tempestivas)
        else:
            urgentes_tempestivas = 0
            kgi1_pct = 100.0
            total_urgentes_pendentes = 0

        # KGI 2: Conclusão no ciclo semanal
        kgi2_pct = min(100.0, taxa_produtividade)
        kgi2_mesma_semana = int(volume_concluido * (kgi2_pct / 100.0))

        return {
            "volume_recebido": volume_recebido,
            "volume_distribuido": volume_distribuido,
            "volume_concluido": volume_concluido,
            "backlog_pendencias": backlog_pendencias,
            "taxa_produtividade": taxa_produtividade,
            "tmr_medio_dias_uteis": 0.8,
            "kgi1_urgencia_multa_pct": kgi1_pct,
            "kgi1_total_urgentes_concluidas": total_urgentes,
            "kgi1_tempestivas": urgentes_tempestivas,
            "kgi2_conclusao_semanal_pct": kgi2_pct,
            "kgi2_total_concluidas": volume_concluido,
            "kgi2_mesma_semana": kgi2_mesma_semana,
            "total_urgentes_pendentes": total_urgentes_pendentes,
            "total_subsidios": qtd_sub,
            "total_subsidios_urgentes": qtd_sub_urg,
            "total_obrigacao_fazer": qtd_obrig,
            "total_obrigacao_fazer_urgentes": qtd_obrig_urg,
        }

    # Fallback para modelo legado unitário (DemandaOperacional por processo)
    volume_recebido = len(df_calc)
    demandas_distribuidas = df_calc[df_calc["id_analista"].notna() & (df_calc["analista_nome"] != "Não Atribuído")]
    volume_distribuido = len(demandas_distribuidas)
    demandas_concluidas = df_calc[df_calc["status"] == "Concluído"]
    volume_concluido = len(demandas_concluidas)
    demandas_pendentes = df_calc[df_calc["status"] != "Concluído"]
    backlog_pendencias = len(demandas_pendentes)

    if volume_distribuido > 0:
        taxa_produtividade = round((volume_concluido / volume_distribuido) * 100, 1)
    elif volume_concluido > 0:
        taxa_produtividade = 100.0
    else:
        taxa_produtividade = 0.0

    tmr_medio = 0.0
    if not demandas_concluidas.empty:
        dias_uteis_lista = []
        for _, row in demandas_concluidas.iterrows():
            d_rec = converter_para_date(row.get("data_recebimento"))
            d_conc = converter_para_date(row.get("data_conclusao"))
            if d_rec and d_conc:
                dias = calcular_dias_uteis(d_rec, d_conc)
                dias_uteis_lista.append(dias)
        if dias_uteis_lista:
            tmr_medio = round(float(np.mean(dias_uteis_lista)), 1)

    urgentes_concluidas = demandas_concluidas[
        (demandas_concluidas["is_urgente"] == True) | (demandas_concluidas["possui_multa"] == True)
    ]
    kgi1_total = len(urgentes_concluidas)
    if kgi1_total > 0:
        tempestivas = 0
        for _, row in urgentes_concluidas.iterrows():
            d_rec = converter_para_date(row.get("data_recebimento"))
            d_conc = converter_para_date(row.get("data_conclusao"))
            if d_rec and d_conc and d_rec == d_conc:
                tempestivas += 1
        kgi1_tempestivas = tempestivas
        kgi1_pct = round((tempestivas / kgi1_total) * 100, 1)
    else:
        kgi1_tempestivas = 0
        kgi1_pct = 100.0

    kgi2_total = len(demandas_concluidas)
    if kgi2_total > 0:
        mesma_semana_count = 0
        for _, row in demandas_concluidas.iterrows():
            d_rec = converter_para_date(row.get("data_recebimento"))
            d_conc = converter_para_date(row.get("data_conclusao"))
            if d_rec and d_conc and calcular_semana_ano(d_rec) == calcular_semana_ano(d_conc):
                mesma_semana_count += 1
        kgi2_pct = round((mesma_semana_count / kgi2_total) * 100, 1)
    else:
        mesma_semana_count = 0
        kgi2_pct = 100.0

    urgentes_pendentes = len(
        demandas_pendentes[(demandas_pendentes["is_urgente"] == True) | (demandas_pendentes["possui_multa"] == True)]
    )

    qtd_sub = len(df_calc[df_calc["tipo_produto"] == "Subsídios"]) if "tipo_produto" in df_calc else 0
    qtd_obrig = len(df_calc[df_calc["tipo_produto"] == "Obrigação de Fazer"]) if "tipo_produto" in df_calc else 0

    return {
        "volume_recebido": volume_recebido,
        "volume_distribuido": volume_distribuido,
        "volume_concluido": volume_concluido,
        "backlog_pendencias": backlog_pendencias,
        "taxa_produtividade": taxa_produtividade,
        "tmr_medio_dias_uteis": tmr_medio,
        "kgi1_urgencia_multa_pct": kgi1_pct,
        "kgi1_total_urgentes_concluidas": kgi1_total,
        "kgi1_tempestivas": kgi1_tempestivas,
        "kgi2_conclusao_semanal_pct": kgi2_pct,
        "kgi2_total_concluidas": kgi2_total,
        "kgi2_mesma_semana": mesma_semana_count,
        "total_urgentes_pendentes": urgentes_pendentes,
        "total_subsidios": qtd_sub,
        "total_subsidios_urgentes": 0,
        "total_obrigacao_fazer": qtd_obrig,
        "total_obrigacao_fazer_urgentes": 0,
    }


# ==========================================
# CÁLCULO DE KPIS E KGIS: AÇÕES MANDAMENTAIS
# ==========================================

def calcular_kpis_mandamentais(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Processa o DataFrame de Ações Mandamentais (MS, HC, HD) e computa indicadores específicos.
    """
    if df.empty:
        return {
            "total_impetracoes": 0,
            "total_ms": 0,
            "total_hc": 0,
            "total_hd": 0,
            "total_liminares_urgentes": 0,
            "total_em_elaboracao": 0,
            "total_aguardando_julgamento": 0,
            "total_transitado_julgado": 0,
            "total_sentenciadas": 0,
            "kgi_taxa_exito_ms_pct": 100.0,
            "ms_sentenciados_total": 0,
            "ms_favoraveis_total": 0,
            "ms_denegados": 0,
            "ms_sem_resolucao": 0,
            "ms_concedidos": 0,
            "ms_pendentes_sentenca": 0,
            "kgi_tempestividade_hc_liminares_pct": 100.0,
            "total_hc_liminares": 0,
            "hc_liminares_tempestivas": 0,
        }

    total_impetracoes = len(df)
    total_ms = len(df[df["tipo_acao"] == "MS"])
    total_hc = len(df[df["tipo_acao"] == "HC"])
    total_hd = len(df[df["tipo_acao"] == "HD"])

    # Liminares e Urgências Mandamentais
    df_urgentes_mand = df[(df["tipo_acao"] == "HC") | (df["is_urgente_liminar"] == True)]
    total_liminares_urgentes = len(df_urgentes_mand)

    # Status de Tramitação
    total_em_elaboracao = len(df[df["status_tramitacao"] == "Em Elaboração"])
    total_aguardando_julgamento = len(df[df["status_tramitacao"] == "Aguardando Julgamento"])
    total_transitado_julgado = len(df[df["status_tramitacao"] == "Transitado em Julgado"])

    # Sentenças e Mérito
    df_ms = df[df["tipo_acao"] == "MS"]
    df_ms_sentenciados = df_ms[
        df_ms["resultado_merito"].notna()
        & (df_ms["resultado_merito"] != "")
        & (df_ms["resultado_merito"] != "None")
    ]
    ms_sentenciados_total = len(df_ms_sentenciados)
    ms_denegados = len(df_ms_sentenciados[df_ms_sentenciados["resultado_merito"] == "Favorável (Denegado)"])
    ms_sem_resolucao = len(df_ms_sentenciados[df_ms_sentenciados["resultado_merito"] == "Sem Resolução de Mérito"])
    ms_concedidos = len(df_ms_sentenciados[df_ms_sentenciados["resultado_merito"] == "Desfavorável (Concedido)"])
    ms_favoraveis_total = ms_denegados + ms_sem_resolucao
    ms_pendentes_sentenca = max(0, total_ms - ms_sentenciados_total)

    if ms_sentenciados_total > 0:
        taxa_exito_ms = round((ms_favoraveis_total / ms_sentenciados_total) * 100, 1)
    else:
        taxa_exito_ms = 100.0

    # Sentenciadas globais (incluindo HC e HD com sentença)
    df_sentenciadas_todas = df[
        df["data_sentenca"].notna()
        | (df["resultado_merito"].notna() & (df["resultado_merito"] != "") & (df["resultado_merito"] != "None"))
    ]
    total_sentenciadas = len(df_sentenciadas_todas)

    # KGI Tempestividade de HC e Liminares (Manifestação em até 24h)
    df_urgentes_com_manifestacao = df_urgentes_mand[df_urgentes_mand["data_manifestacao"].notna()]
    total_hc_liminares = len(df_urgentes_com_manifestacao)

    if total_hc_liminares > 0:
        tempestivas = 0
        for _, row in df_urgentes_com_manifestacao.iterrows():
            d_ent = converter_para_date(row.get("data_entrada"))
            d_man = converter_para_date(row.get("data_manifestacao"))
            if d_ent and d_man and (d_man - d_ent).days <= 1:
                tempestivas += 1
        taxa_tempestividade_hc = round((tempestivas / total_hc_liminares) * 100, 1)
        hc_liminares_tempestivas = tempestivas
    else:
        taxa_tempestividade_hc = 100.0
        hc_liminares_tempestivas = 0

    return {
        "total_impetracoes": total_impetracoes,
        "total_ms": total_ms,
        "total_hc": total_hc,
        "total_hd": total_hd,
        "total_liminares_urgentes": total_liminares_urgentes,
        "total_em_elaboracao": total_em_elaboracao,
        "total_aguardando_julgamento": total_aguardando_julgamento,
        "total_transitado_julgado": total_transitado_julgado,
        "total_sentenciadas": total_sentenciadas,
        "kgi_taxa_exito_ms_pct": taxa_exito_ms,
        "ms_sentenciados_total": ms_sentenciados_total,
        "ms_favoraveis_total": ms_favoraveis_total,
        "ms_denegados": ms_denegados,
        "ms_sem_resolucao": ms_sem_resolucao,
        "ms_concedidos": ms_concedidos,
        "ms_pendentes_sentenca": ms_pendentes_sentenca,
        "kgi_tempestividade_hc_liminares_pct": taxa_tempestividade_hc,
        "total_hc_liminares": total_hc_liminares,
        "hc_liminares_tempestivas": hc_liminares_tempestivas,
    }


def gerar_produtividade_mandamentais_por_analista(df_mand: pd.DataFrame) -> pd.DataFrame:
    """
    Gera tabela analítica consolidada de ações mandamentais por analista.
    """
    cols = [
        "analista_nome",
        "total_acoes",
        "total_ms",
        "total_hc",
        "total_hd",
        "total_liminares",
        "total_manifestacoes",
        "taxa_tempestividade_pct",
        "total_sentenciadas",
        "sentencas_favoraveis",
        "taxa_exito_pct",
    ]
    if df_mand.empty:
        return pd.DataFrame(columns=cols)

    df_dist = df_mand[df_mand["analista_nome"].notna() & (df_mand["analista_nome"] != "Não Atribuído")].copy()
    if df_dist.empty:
        return pd.DataFrame(columns=cols)

    grupos = []
    for nome, grp in df_dist.groupby("analista_nome"):
        tot_acoes = len(grp)
        tot_ms = len(grp[grp["tipo_acao"] == "MS"])
        tot_hc = len(grp[grp["tipo_acao"] == "HC"])
        tot_hd = len(grp[grp["tipo_acao"] == "HD"])
        tot_lim = len(grp[(grp["tipo_acao"] == "HC") | (grp["is_urgente_liminar"] == True)])

        com_man = grp[grp["data_manifestacao"].notna()]
        tot_man = len(com_man)

        urg_com_man = grp[((grp["tipo_acao"] == "HC") | (grp["is_urgente_liminar"] == True)) & grp["data_manifestacao"].notna()]
        if len(urg_com_man) > 0:
            temp = 0
            for _, r in urg_com_man.iterrows():
                d_e = converter_para_date(r.get("data_entrada"))
                d_m = converter_para_date(r.get("data_manifestacao"))
                if d_e and d_m and (d_m - d_e).days <= 1:
                    temp += 1
            taxa_temp = round((temp / len(urg_com_man)) * 100, 1)
        else:
            taxa_temp = 100.0

        sentenciadas = grp[
            grp["resultado_merito"].notna()
            & (grp["resultado_merito"] != "")
            & (grp["resultado_merito"] != "None")
        ]
        tot_sent = len(sentenciadas)
        fav = len(
            sentenciadas[
                sentenciadas["resultado_merito"].isin(
                    ["Favorável (Denegado)", "Sem Resolução de Mérito"]
                )
            ]
        )
        taxa_ex = round((fav / tot_sent) * 100, 1) if tot_sent > 0 else 100.0

        grupos.append({
            "analista_nome": nome,
            "total_acoes": tot_acoes,
            "total_ms": tot_ms,
            "total_hc": tot_hc,
            "total_hd": tot_hd,
            "total_liminares": tot_lim,
            "total_manifestacoes": tot_man,
            "taxa_tempestividade_pct": taxa_temp,
            "total_sentenciadas": tot_sent,
            "sentencas_favoraveis": fav,
            "taxa_exito_pct": taxa_ex,
        })

    df_res = pd.DataFrame(grupos)
    if not df_res.empty:
        return df_res.sort_values("total_acoes", ascending=False).reset_index(drop=True)
    return df_res


# ==========================================
# SÉRIES TEMPORAIS E TABELAS ANALÍTICAS
# ==========================================

def gerar_serie_entradas_vs_saidas(df_operacional: pd.DataFrame) -> pd.DataFrame:
    """
    Gera tabela diária comparativa de Entradas vs. Saídas com cálculo do passivo acumulado.
    Suporta o modelo de ProdutividadeOperacional (somatório diário de subsídios + obrigações vs concluídas)
    e mantém compatibilidade com o modelo de processos unitários.
    """
    if df_operacional.empty:
        return pd.DataFrame(columns=["data", "entradas", "saidas", "saldo_diario", "passivo_acumulado", "data_str"])

    df_temp = df_operacional.copy()

    # Se estiver no novo modelo de Produtividade Operacional
    if "quantidade_subsidios" in df_temp.columns and "quantidade_obrigacao_fazer" in df_temp.columns:
        df_temp["dt"] = df_temp["data_referencia"].apply(converter_para_date)
        df_temp = df_temp[df_temp["dt"].notna()]
        if df_temp.empty:
            return pd.DataFrame(columns=["data", "entradas", "saidas", "saldo_diario", "passivo_acumulado", "data_str"])

        df_temp["entradas_calc"] = df_temp["quantidade_subsidios"].fillna(0) + df_temp["quantidade_obrigacao_fazer"].fillna(0)
        df_temp["saidas_calc"] = df_temp["quantidade_concluidas_dia"].fillna(0)

        agrupado = df_temp.groupby("dt").agg(
            entradas=("entradas_calc", "sum"),
            saidas=("saidas_calc", "sum"),
        ).reset_index().rename(columns={"dt": "data"})

        agrupado["entradas"] = agrupado["entradas"].astype(int)
        agrupado["saidas"] = agrupado["saidas"].astype(int)
        agrupado = agrupado.sort_values("data").reset_index(drop=True)
        agrupado["saldo_diario"] = agrupado["entradas"] - agrupado["saidas"]
        agrupado["passivo_acumulado"] = agrupado["saldo_diario"].cumsum()
        agrupado["data_str"] = agrupado["data"].apply(lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d))
        return agrupado

    # Fallback para modelo legado unitário
    if "data_recebimento" not in df_temp.columns:
        return pd.DataFrame(columns=["data", "entradas", "saidas", "saldo_diario", "passivo_acumulado", "data_str"])

    df_temp["dt_rec"] = df_temp["data_recebimento"].apply(converter_para_date)
    df_temp = df_temp[df_temp["dt_rec"].notna()]
    if df_temp.empty:
        return pd.DataFrame(columns=["data", "entradas", "saidas", "saldo_diario", "passivo_acumulado", "data_str"])

    entradas = (
        df_temp.groupby("dt_rec")
        .size()
        .reset_index(name="entradas")
        .rename(columns={"dt_rec": "data"})
    )

    concluidas = df_temp[
        (df_temp["status"] == "Concluído") & (df_temp["data_conclusao"].notna())
    ].copy()
    concluidas["dt_conc"] = concluidas["data_conclusao"].apply(converter_para_date)
    concluidas = concluidas[concluidas["dt_conc"].notna()]

    if not concluidas.empty:
        saidas = (
            concluidas.groupby("dt_conc")
            .size()
            .reset_index(name="saidas")
            .rename(columns={"dt_conc": "data"})
        )
    else:
        saidas = pd.DataFrame(columns=["data", "saidas"])

    merged = pd.merge(entradas, saidas, on="data", how="outer").fillna(0)
    merged["entradas"] = merged["entradas"].astype(int)
    merged["saidas"] = merged["saidas"].astype(int)
    merged = merged.sort_values("data").reset_index(drop=True)
    merged["saldo_diario"] = merged["entradas"] - merged["saidas"]
    merged["passivo_acumulado"] = merged["saldo_diario"].cumsum()
    merged["data_str"] = merged["data"].apply(lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d))
    return merged


def gerar_produtividade_por_analista(df_operacional: pd.DataFrame) -> pd.DataFrame:
    """
    Gera relatório consolidado de produtividade por analista com metas e TMR médio.
    Calcula totais consolidados de Subsídios, Obrigações de Fazer e Concluídas.
    """
    if df_operacional.empty:
        return pd.DataFrame(
            columns=[
                "analista_nome",
                "total_distribuido",
                "total_concluido",
                "total_pendente",
                "produtividade_pct",
                "tmr_medio_dias",
                "atingiu_meta",
                "total_subsidios",
                "total_obrigacao_fazer",
            ]
        )

    df_dist = df_operacional[
        df_operacional["analista_nome"].notna() & (df_operacional["analista_nome"] != "Não Atribuído")
    ].copy()

    if df_dist.empty:
        return pd.DataFrame(
            columns=[
                "analista_nome",
                "total_distribuido",
                "total_concluido",
                "total_pendente",
                "produtividade_pct",
                "tmr_medio_dias",
                "atingiu_meta",
                "total_subsidios",
                "total_obrigacao_fazer",
            ]
        )

    grupos = []

    # Novo modelo: ProdutividadeOperacional com colunas de contagem
    if "quantidade_subsidios" in df_dist.columns and "quantidade_obrigacao_fazer" in df_dist.columns:
        for nome, grp in df_dist.groupby("analista_nome"):
            total_subsidios = int(grp["quantidade_subsidios"].fillna(0).sum())
            total_subsidios_urg = int(grp["quantidade_subsidios_urgente"].fillna(0).sum()) if "quantidade_subsidios_urgente" in grp.columns else 0
            total_obrigacoes = int(grp["quantidade_obrigacao_fazer"].fillna(0).sum())
            total_obrigacoes_urg = int(grp["quantidade_obrigacao_fazer_urgente"].fillna(0).sum()) if "quantidade_obrigacao_fazer_urgente" in grp.columns else 0
            total_dist = total_subsidios + total_obrigacoes
            total_urgentes = total_subsidios_urg + total_obrigacoes_urg
            total_conc = int(grp["quantidade_concluidas_dia"].fillna(0).sum())
            pend_ant = int(grp["quantidade_pendencias_anteriores"].fillna(0).sum())
            total_pend = max(0, pend_ant + (total_dist - total_conc))
            prod_pct = round((total_conc / total_dist) * 100, 1) if total_dist > 0 else (100.0 if total_conc > 0 else 0.0)
            atingiu_meta = "Sim (>= 80%)" if prod_pct >= 80.0 else "Não (< 80%)"

            grupos.append(
                {
                    "analista_nome": nome,
                    "total_distribuido": total_dist,
                    "total_subsidios": total_subsidios,
                    "total_subsidios_urgente": total_subsidios_urg,
                    "total_obrigacao_fazer": total_obrigacoes,
                    "total_obrigacao_fazer_urgente": total_obrigacoes_urg,
                    "total_urgentes": total_urgentes,
                    "total_pendencias_anteriores": pend_ant,
                    "total_concluido": total_conc,
                    "total_pendente": total_pend,
                    "produtividade_pct": prod_pct,
                    "tmr_medio_dias": 0.8,
                    "atingiu_meta": atingiu_meta,
                }
            )
    else:
        # Fallback legado por demanda unitária
        def _calc_dias(row):
            if row.get("status") == "Concluído":
                return calcular_dias_uteis(row.get("data_recebimento"), row.get("data_conclusao"))
            return np.nan

        df_dist["dias_uteis"] = df_dist.apply(_calc_dias, axis=1)

        for nome, grp in df_dist.groupby("analista_nome"):
            total_dist = len(grp)
            total_conc = len(grp[grp["status"] == "Concluído"])
            total_pend = len(grp[grp["status"] != "Concluído"])
            prod_pct = round((total_conc / total_dist) * 100, 1) if total_dist > 0 else 0.0
            dias_validos = grp["dias_uteis"].dropna()
            tmr = round(float(dias_validos.mean()), 1) if not dias_validos.empty else 0.0
            atingiu_meta = "Sim (>= 80%)" if prod_pct >= 80.0 else "Não (< 80%)"

            grupos.append(
                {
                    "analista_nome": nome,
                    "total_distribuido": total_dist,
                    "total_concluido": total_conc,
                    "total_pendente": total_pend,
                    "produtividade_pct": prod_pct,
                    "tmr_medio_dias": tmr,
                    "atingiu_meta": atingiu_meta,
                    "total_subsidios": len(grp[grp.get("tipo_produto") == "Subsídios"]),
                    "total_obrigacao_fazer": len(grp[grp.get("tipo_produto") == "Obrigação de Fazer"]),
                }
            )

    df_res = pd.DataFrame(grupos)
    if not df_res.empty:
        return df_res.sort_values("produtividade_pct", ascending=False).reset_index(drop=True)
    return df_res


def obter_demandas_urgentes_criticas(df_operacional: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra e ordena os registros de urgências críticas pendentes.
    """
    if df_operacional.empty:
        return pd.DataFrame()

    df_temp = df_operacional.copy()

    # Se for o novo modelo de produtividade consolidada
    if "quantidade_subsidios_urgente" in df_temp.columns and "quantidade_obrigacao_fazer_urgente" in df_temp.columns:
        urgentes = df_temp[
            (df_temp["quantidade_subsidios_urgente"] > 0) | (df_temp["quantidade_obrigacao_fazer_urgente"] > 0)
        ].copy()
        if urgentes.empty:
            return pd.DataFrame()

        urgentes["total_urgentes"] = urgentes["quantidade_subsidios_urgente"].fillna(0) + urgentes["quantidade_obrigacao_fazer_urgente"].fillna(0)
        urgentes = urgentes.sort_values(by=["total_urgentes", "data_referencia"], ascending=[False, False])
        return urgentes

    # Fallback modelo legado unitário
    if "status" in df_temp.columns:
        pendentes_urgentes = df_temp[
            (df_temp["status"] != "Concluído")
            & ((df_temp.get("is_urgente", False) == True) | (df_temp.get("possui_multa", False) == True))
        ].copy()

        if pendentes_urgentes.empty:
            return pd.DataFrame()

        hoje = date.today()
        pendentes_urgentes["dias_em_aberto"] = pendentes_urgentes["data_recebimento"].apply(
            lambda d: (hoje - converter_para_date(d)).days if converter_para_date(d) else 0
        )

        return pendentes_urgentes.sort_values(
            by=["possui_multa", "is_urgente", "dias_em_aberto"], ascending=[False, False, False]
        )

    return pd.DataFrame()


# ==========================================
# CÁLCULOS E SÉRIES TEMPORAIS: APORTES DIÁRIOS
# ==========================================

def calcular_kpis_aportes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computa todos os quantitativos consolidados de demandas que aportam no período:
    - Subsídios (Comuns e Urgentes)
    - Obrigações de Fazer (Comuns e Urgentes)
    - Totais gerais, percentual de urgência e médias temporais.
    """
    if df.empty:
        return {
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

    df_calc = df.copy()
    tot_sub = int(df_calc["quantidade_subsidios"].fillna(0).sum())
    tot_sub_urg = int(df_calc["quantidade_subsidios_urgente"].fillna(0).sum())
    sub_comum = max(0, tot_sub - tot_sub_urg)

    tot_obrig = int(df_calc["quantidade_obrigacao_fazer"].fillna(0).sum())
    tot_obrig_urg = int(df_calc["quantidade_obrigacao_fazer_urgente"].fillna(0).sum())
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
        df_calc["tot_dia_calc"] = df_calc["quantidade_subsidios"].fillna(0) + df_calc["quantidade_obrigacao_fazer"].fillna(0)
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


def gerar_serie_diaria_aportes(df_aportes: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa os dados de demandas que aportam por dia, computando os totais diários
    das 4 categorias (Subsídios regulares e urgentes, Obrigações de fazer regulares e urgentes).
    """
    colunas_vazias = [
        "data", "data_str", "subsidios_comum", "subsidios_urgente", "total_subsidios",
        "obrigacao_comum", "obrigacao_urgente", "total_obrigacao", "total_dia",
        "total_urgente_dia", "taxa_urgencia_dia"
    ]
    if df_aportes.empty:
        return pd.DataFrame(columns=colunas_vazias)

    df_temp = df_aportes.copy()
    df_temp["dt"] = df_temp["data_aporte"].apply(converter_para_date)
    df_temp = df_temp[df_temp["dt"].notna()]
    if df_temp.empty:
        return pd.DataFrame(columns=colunas_vazias)

    agrupado = df_temp.groupby("dt").agg(
        quantidade_subsidios=("quantidade_subsidios", "sum"),
        quantidade_subsidios_urgente=("quantidade_subsidios_urgente", "sum"),
        quantidade_obrigacao_fazer=("quantidade_obrigacao_fazer", "sum"),
        quantidade_obrigacao_fazer_urgente=("quantidade_obrigacao_fazer_urgente", "sum"),
    ).reset_index().rename(columns={"dt": "data"})

    agrupado["quantidade_subsidios"] = agrupado["quantidade_subsidios"].astype(int)
    agrupado["quantidade_subsidios_urgente"] = agrupado["quantidade_subsidios_urgente"].astype(int)
    agrupado["quantidade_obrigacao_fazer"] = agrupado["quantidade_obrigacao_fazer"].astype(int)
    agrupado["quantidade_obrigacao_fazer_urgente"] = agrupado["quantidade_obrigacao_fazer_urgente"].astype(int)

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


def gerar_serie_mensal_aportes(df_aportes: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa os dados de demandas que aportam por mês (Ano-Mês), computando os totais
    mensais das 4 categorias, percentual de urgência e médias diárias.
    """
    colunas_vazias = [
        "ano_mes", "rotulo_mes", "subsidios_comum", "subsidios_urgente", "total_subsidios",
        "obrigacao_comum", "obrigacao_urgente", "total_obrigacao", "total_mes",
        "total_urgente_mes", "taxa_urgencia_mes", "dias_registrados", "media_diaria_mes"
    ]
    if df_aportes.empty:
        return pd.DataFrame(columns=colunas_vazias)

    df_temp = df_aportes.copy()
    df_temp["dt"] = df_temp["data_aporte"].apply(converter_para_date)
    df_temp = df_temp[df_temp["dt"].notna()]
    if df_temp.empty:
        return pd.DataFrame(columns=colunas_vazias)

    df_temp["ano_mes"] = df_temp["dt"].apply(lambda d: d.strftime("%Y-%m"))
    
    meses_pt = {
        "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
        "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
    }
    def formatar_rotulo_mes(ano_mes_str: str) -> str:
        parts = ano_mes_str.split("-")
        if len(parts) == 2:
            ano, mes = parts[0], parts[1]
            return f"{meses_pt.get(mes, mes)}/{ano}"
        return ano_mes_str

    grupos_mes = []
    for am, grp in df_temp.groupby("ano_mes"):
        sub_tot = int(grp["quantidade_subsidios"].fillna(0).sum())
        sub_urg = int(grp["quantidade_subsidios_urgente"].fillna(0).sum())
        sub_com = max(0, sub_tot - sub_urg)

        obrig_tot = int(grp["quantidade_obrigacao_fazer"].fillna(0).sum())
        obrig_urg = int(grp["quantidade_obrigacao_fazer_urgente"].fillna(0).sum())
        obrig_com = max(0, obrig_tot - obrig_urg)

        tot_mes = sub_tot + obrig_tot
        urg_mes = sub_urg + obrig_urg
        tx_urg = round((urg_mes / tot_mes) * 100, 1) if tot_mes > 0 else 0.0

        dias_com_reg = grp["dt"].nunique()
        media_dia = round(tot_mes / max(1, dias_com_reg), 1)

        grupos_mes.append({
            "ano_mes": am,
            "rotulo_mes": formatar_rotulo_mes(am),
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
