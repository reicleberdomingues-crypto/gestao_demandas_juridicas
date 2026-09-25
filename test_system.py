"""
test_system.py - Verificação e Testes Unitários Automatizados
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

from datetime import date, time, timedelta
import pandas as pd
import numpy as np

import database as db
import metrics as met
from seed_data import seed_database


def test_database_and_seed():
    """Testa inicialização do banco, seed de dados e consistência relacional."""
    print("[1/5] Testando inicialização do banco e seed de dados...")
    db.init_db()
    seed_database(force=True)

    analistas = db.get_analistas()
    assert len(analistas) >= 5, f"Esperado pelo menos 5 analistas, obtido {len(analistas)}"
    assert hasattr(analistas[0], "nome"), "AnalistaDTO deve possuir atributo 'nome'"

    # Validar Produtividade Operacional (Obrigações e Subsídios por Analista)
    df_prod = db.get_df_produtividade_operacional()
    assert not df_prod.empty, "DataFrame de produtividade operacional não deveria estar vazio."
    assert "quantidade_subsidios" in df_prod.columns
    assert "quantidade_obrigacao_fazer" in df_prod.columns
    assert "quantidade_concluidas_dia" in df_prod.columns
    assert "quantidade_pendencias_anteriores" in df_prod.columns
    assert "analista_nome" in df_prod.columns
    assert "total_entradas_dia" in df_prod.columns

    # Validar Ações Mandamentais (MS, HC, HD)
    df_mand = db.get_df_acoes_mandamentais()
    assert not df_mand.empty, "DataFrame de ações mandamentais não deveria estar vazio."
    assert "numero_processo" in df_mand.columns
    assert "tipo_acao" in df_mand.columns
    print(f"  -> Banco e Seed validados: {len(df_prod)} registros de produtividade diária e {len(df_mand)} ações mandamentais!")


def test_crud_produtividade_operacional():
    """Testa inserção, atualização em lote e exclusão de registros de produtividade diária."""
    print("[2/5] Testando operações CRUD de Produtividade Operacional...")
    hoje = date.today()
    analistas = db.get_analistas(active_only=True)
    analista_op = [a for a in analistas if a.especialidade == "Obrigações/Subsídios"][0]

    # Inserção
    novo_id = db.add_produtividade_operacional(
        data_referencia=hoje,
        id_analista=analista_op.id,
        quantidade_subsidios=10,
        quantidade_subsidios_urgente=2,
        quantidade_obrigacao_fazer=8,
        quantidade_obrigacao_fazer_urgente=1,
        quantidade_pendencias_anteriores=5,
        quantidade_concluidas_dia=15,
        observacoes="Registro de teste automatizado",
    )
    assert novo_id > 0, "ID gerado deve ser maior que 0"

    # Atualização em lote
    qtd_atualizada = db.bulk_update_produtividade_operacional([
        {
            "id": novo_id,
            "quantidade_concluidas_dia": 17,
            "observacoes": "Registro atualizado pelo teste",
        }
    ])
    assert qtd_atualizada == 1, f"Esperado 1 registro atualizado, obtido {qtd_atualizada}"

    # Exclusão
    sucesso_del = db.delete_produtividade_operacional(novo_id)
    assert sucesso_del is True, "Exclusão do registro de teste deve retornar True"
    print("  -> CRUD de Produtividade Operacional testado e aprovado!")


def test_metricas_operacionais():
    """Testa cálculos de KPIs e KGIs da produtividade operacional."""
    print("[3/5] Testando KPIs e KGIs de produtividade operacional e contabilidade distribuída...")
    d1 = date(2024, 9, 2)  # Segunda-feira
    d2 = date(2024, 9, 6)  # Sexta-feira
    dias = met.calcular_dias_uteis(d1, d2)
    assert dias == 4, f"Esperado 4 dias úteis entre segunda e sexta, obtido {dias}"
    assert met.calcular_dias_uteis(d1, d1) == 0

    df_prod = db.get_df_produtividade_operacional()
    kpis = met.calcular_kpis_operacionais(df_prod)

    assert "volume_recebido" in kpis
    assert "volume_distribuido" in kpis
    assert "volume_concluido" in kpis
    assert "taxa_produtividade" in kpis
    assert "backlog_pendencias" in kpis
    assert "total_subsidios" in kpis
    assert "total_subsidios_urgentes" in kpis
    assert "total_obrigacao_fazer" in kpis
    assert "total_obrigacao_fazer_urgentes" in kpis
    assert "kgi1_urgencia_multa_pct" in kpis
    assert "kgi2_conclusao_semanal_pct" in kpis

    assert kpis["volume_recebido"] > 0
    assert kpis["volume_concluido"] > 0
    assert 0 <= kpis["taxa_produtividade"] <= 100
    assert 0 <= kpis["kgi1_urgencia_multa_pct"] <= 100
    print(f"  -> KPIs Operacionais: Recebido={kpis['volume_recebido']}, Distribuído={kpis['volume_distribuido']}, Concluído={kpis['volume_concluido']}, Subsídios={kpis['total_subsidios']} (Urg: {kpis['total_subsidios_urgentes']}), Obrigação={kpis['total_obrigacao_fazer']} (Urg: {kpis['total_obrigacao_fazer_urgentes']})")


def test_metricas_mandamentais():
    """Testa cálculos de KPIs e KGIs de ações mandamentais."""
    print("[4/5] Testando KPIs e KGIs mandamentais...")
    df_mand = db.get_df_acoes_mandamentais()
    kpis_m = met.calcular_kpis_mandamentais(df_mand)

    assert "kgi_taxa_exito_ms_pct" in kpis_m
    assert "kgi_tempestividade_hc_liminares_pct" in kpis_m
    assert "total_liminares_urgentes" in kpis_m
    assert "total_sentenciadas" in kpis_m
    assert "ms_favoraveis_total" in kpis_m
    assert 0 <= kpis_m["kgi_taxa_exito_ms_pct"] <= 100
    assert 0 <= kpis_m["kgi_tempestividade_hc_liminares_pct"] <= 100
    print(f"  -> Mandamentais: Total={kpis_m['total_impetracoes']}, MS={kpis_m['total_ms']}, HC={kpis_m['total_hc']}, HD={kpis_m['total_hd']}, Taxa Êxito MS={kpis_m['kgi_taxa_exito_ms_pct']}%, KGI HC={kpis_m['kgi_tempestividade_hc_liminares_pct']}%")


def test_series_e_tabelas():
    """Testa séries temporais de fluxo e produtividade por analista."""
    print("[5/5] Testando séries temporais e produtividade consolidada por analista...")
    df_prod = db.get_df_produtividade_operacional()
    df_fluxo = met.gerar_serie_entradas_vs_saidas(df_prod)
    assert not df_fluxo.empty
    assert "saldo_diario" in df_fluxo.columns
    assert "passivo_acumulado" in df_fluxo.columns
    assert "data_str" in df_fluxo.columns

    df_analistas_prod = met.gerar_produtividade_por_analista(df_prod)
    assert not df_analistas_prod.empty
    assert "produtividade_pct" in df_analistas_prod.columns
    assert "total_distribuido" in df_analistas_prod.columns
    assert "total_concluido" in df_analistas_prod.columns
    assert "total_subsidios" in df_analistas_prod.columns
    assert "total_subsidios_urgente" in df_analistas_prod.columns
    assert "total_obrigacao_fazer" in df_analistas_prod.columns
    assert "total_obrigacao_fazer_urgente" in df_analistas_prod.columns
    assert "total_urgentes" in df_analistas_prod.columns

    df_mand = db.get_df_acoes_mandamentais()
    df_mand_analistas = met.gerar_produtividade_mandamentais_por_analista(df_mand)
    assert not df_mand_analistas.empty
    assert "total_acoes" in df_mand_analistas.columns
    assert "total_ms" in df_mand_analistas.columns
    assert "taxa_exito_pct" in df_mand_analistas.columns
    assert "taxa_tempestividade_pct" in df_mand_analistas.columns

    print(f"  -> Série temporal ({len(df_fluxo)} dias), Produtividade Operacional ({len(df_analistas_prod)} analistas) e Mandamentais ({len(df_mand_analistas)} analistas) testadas e validadas com sucesso!")


if __name__ == "__main__":
    print("==================================================")
    print("INICIANDO SUÍTE DE TESTES DO SISTEMA JURÍDICO")
    print("==================================================")
    test_database_and_seed()
    test_crud_produtividade_operacional()
    test_metricas_operacionais()
    test_metricas_mandamentais()
    test_series_e_tabelas()
    print("==================================================")
    print("TODOS OS TESTES FORAM CONCLUIDOS COM SUCESSO!")
    print("==================================================")
