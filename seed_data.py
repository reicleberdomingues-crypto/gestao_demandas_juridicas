"""
seed_data.py - Carga Inicial de Dados Realistas para Demonstração e Testes
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

from datetime import date, time, timedelta
import random
from database import (
    init_db,
    get_db_session,
    Analista,
    ProdutividadeOperacional,
    DemandaOperacional,
    AcaoMandamental,
)


def seed_analistas_padrao():
    """
    Cadastra a equipe padrão de analistas caso a tabela esteja vazia.
    Retorna a lista de instâncias ou DTOs de analistas criados/existentes.
    """
    init_db()
    with get_db_session() as session:
        if session.query(Analista).count() > 0:
            return session.query(Analista).all()

        analistas_data = [
            ("Dra. Carolina Mendes", "Obrigações/Subsídios", True),
            ("Dr. Rodrigo Silveira", "Obrigações/Subsídios", True),
            ("Dra. Juliana Vasconcelos", "Obrigações/Subsídios", True),
            ("Dr. Felipe Cavalcanti", "Ações Mandamentais", True),
            ("Dra. Mariana Azevedo", "Ações Mandamentais", True),
            ("Dr. Thiago Peixoto", "Obrigações/Subsídios", False),  # Inativo
        ]

        analistas_obj = []
        for nome, esp, ativo in analistas_data:
            a = Analista(nome=nome, especialidade=esp, ativo=ativo)
            session.add(a)
            analistas_obj.append(a)
        session.flush()
        return analistas_obj


def seed_database(force: bool = False):
    """
    Popula o banco com analistas, produtividade operacional consolidada
    e ações mandamentais para permitir uso e testes imediatos com gráficos ricos.
    """
    init_db()

    with get_db_session() as session:
        # Se já existirem registros e force for False, não duplica
        if not force and session.query(Analista).count() > 0 and session.query(ProdutividadeOperacional).count() > 0:
            return

        # Limpar registros se force for True
        if force:
            session.query(ProdutividadeOperacional).delete()
            session.query(DemandaOperacional).delete()
            session.query(AcaoMandamental).delete()
            session.query(Analista).delete()

        # 1. Cadastrar Analistas
        analistas_data = [
            ("Dra. Carolina Mendes", "Obrigações/Subsídios", True),
            ("Dr. Rodrigo Silveira", "Obrigações/Subsídios", True),
            ("Dra. Juliana Vasconcelos", "Obrigações/Subsídios", True),
            ("Dr. Felipe Cavalcanti", "Ações Mandamentais", True),
            ("Dra. Mariana Azevedo", "Ações Mandamentais", True),
            ("Dr. Thiago Peixoto", "Obrigações/Subsídios", False),  # Inativo
        ]

        analistas_obj = []
        for nome, esp, ativo in analistas_data:
            a = Analista(nome=nome, especialidade=esp, ativo=ativo)
            session.add(a)
            analistas_obj.append(a)

        session.flush()

        analistas_op = [a.id for a in analistas_obj if a.especialidade == "Obrigações/Subsídios" and a.ativo]
        analistas_mand = [a.id for a in analistas_obj if a.especialidade == "Ações Mandamentais" and a.ativo]

        hoje = date.today()

        # 2. Produtividade Operacional (Obrigações de Fazer e Subsídios)
        # Registros diários consolidados por analista (sem número de processo)
        random.seed(42)
        observacoes_op = [
            "Atendimento prioritário de tutelas de urgência e cumprimento tempestivo",
            "Cumprimento tempestivo de ordens com cominação de multa",
            "Fornecimento de informações e subsídios técnicos aos órgãos de defesa",
            "Demandas regulares concluídas no expediente com alta vazão",
            "Priorização de implantação de tratamentos de saúde e benefícios",
            "Expediente focado em saneamento de pendências anteriores",
            "Atendimento de notificações judiciais com prazos exíguos",
            "Elaboração de notas técnicas e prestação de esclarecimentos periciais",
        ]

        # Inicializar backlog inicial para cada analista operacional
        backlog_analistas = {a_id: random.randint(4, 9) for a_id in analistas_op}

        # Gerar registros de produtividade diária para os últimos 20 dias úteis
        dias_uteis_gerados = []
        cur_date = hoje
        while len(dias_uteis_gerados) < 20:
            if cur_date.weekday() < 5:  # Segunda a sexta
                dias_uteis_gerados.append(cur_date)
            cur_date -= timedelta(days=1)
        dias_uteis_gerados.reverse()  # Ordem cronológica crescente

        for dt_ref in dias_uteis_gerados:
            for analista_id in analistas_op:
                pend_ant = backlog_analistas[analista_id]

                qtd_sub = random.randint(3, 8)
                # Subsídios urgentes (subconjunto dos subsídios)
                qtd_sub_urg = random.randint(0, min(2, qtd_sub))

                qtd_obrig = random.randint(2, 6)
                # Obrigação urgente (subconjunto das obrigações)
                qtd_obrig_urg = random.randint(0, min(2, qtd_obrig))

                total_entradas = qtd_sub + qtd_obrig
                total_disponivel = pend_ant + total_entradas

                # Desempenho realista (taxa entre 75% e 95%)
                if dt_ref == hoje:
                    # No dia de hoje, uma parte ainda está em andamento
                    taxa_conc = random.uniform(0.65, 0.85)
                else:
                    taxa_conc = random.uniform(0.78, 0.96)

                concluidas_dia = min(total_disponivel, max(1, int(total_entradas * taxa_conc)))
                novo_backlog = max(1, total_disponivel - concluidas_dia)
                backlog_analistas[analista_id] = novo_backlog

                obs = random.choice(observacoes_op)
                if (qtd_sub_urg + qtd_obrig_urg) > 0 and random.random() < 0.4:
                    obs = f"Urgência tempestiva cumprida. {obs}"

                prod = ProdutividadeOperacional(
                    data_referencia=dt_ref,
                    id_analista=analista_id,
                    quantidade_subsidios=qtd_sub,
                    quantidade_subsidios_urgente=qtd_sub_urg,
                    quantidade_obrigacao_fazer=qtd_obrig,
                    quantidade_obrigacao_fazer_urgente=qtd_obrig_urg,
                    quantidade_pendencias_anteriores=pend_ant,
                    quantidade_concluidas_dia=concluidas_dia,
                    observacoes=obs,
                )
                session.add(prod)

        # 3. Ações Mandamentais (MS, HC, HD)
        tipos_mand = ["MS", "HC", "HD"]
        resultados_merito = [
            "Favorável (Denegado)",
            "Favorável (Denegado)",
            "Favorável (Denegado)",
            "Sem Resolução de Mérito",
            "Desfavorável (Concedido)",
        ]

        count_mand = 5000
        for dias_atras in range(25, -1, -2):
            dt_ent = hoje - timedelta(days=dias_atras)
            qtd = random.randint(1, 3)

            for _ in range(qtd):
                count_mand += 1
                cnj = f"10{count_mand:05d}-88.2024.8.19.0000"
                tipo = random.choice(tipos_mand)
                is_lim = (tipo == "HC") or (random.random() < 0.35)
                analista_id = random.choice(analistas_mand)

                # Manifestação
                dt_man = None
                if dias_atras >= 2:
                    # HC e liminares prestadas em até 24h (92% das vezes)
                    if is_lim:
                        dt_man = dt_ent if random.random() < 0.92 else dt_ent + timedelta(days=2)
                    else:
                        dt_man = dt_ent + timedelta(days=random.randint(1, 5))

                # Status de tramitação e Sentença
                if dias_atras >= 12:
                    status_tram = random.choices(["Aguardando Julgamento", "Transitado em Julgado"], weights=[0.4, 0.6])[0]
                    dt_sent = dt_ent + timedelta(days=random.randint(8, 11))
                    res = random.choice(resultados_merito)
                elif dias_atras >= 5:
                    status_tram = "Aguardando Julgamento"
                    dt_sent = None
                    res = None
                else:
                    status_tram = "Em Elaboração"
                    dt_sent = None
                    res = None

                acao = AcaoMandamental(
                    numero_processo=cnj,
                    tipo_acao=tipo,
                    data_entrada=dt_ent,
                    id_analista=analista_id,
                    is_urgente_liminar=is_lim,
                    data_manifestacao=dt_man,
                    status_tramitacao=status_tram,
                    data_sentenca=dt_sent,
                    resultado_merito=res,
                )
                session.add(acao)


if __name__ == "__main__":
    seed_database(force=True)
    print("Banco de dados juridico.db populado com sucesso com dados simulados realistas!")
