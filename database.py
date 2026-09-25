"""
database.py - Camada de Persistência e Modelagem Relacional
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

from datetime import date, time, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    Text,
    ForeignKey,
    event,
    text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Session,
)

# Caminho do banco de dados SQLite no mesmo diretório deste módulo
DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "juridico.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Engine com pool otimizado e conexão segura
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)

# Habilitar integridade referencial de Foreign Keys e modo WAL no SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

# IMPORTANTE: expire_on_commit=False evita DetachedInstanceError em requisições Streamlit
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
Base = declarative_base()


def parse_date_flexible(val: Any) -> Optional[date]:
    """Converte valores de data (date, Timestamp ou strings em múltiplos formatos como DD/MM/YYYY e YYYY-MM-DD)."""
    if pd.isna(val) or val is None or str(val).strip() in ("", "NaT", "None"):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.date()
    if isinstance(val, str):
        cleaned = val.strip().split()[0]
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
    return None


@contextmanager
def get_db_session():
    """Gerenciador de contexto para transações seguras de banco de dados."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ==========================================
# DTOs DESACOPLADOS (Evita DetachedInstanceError)
# ==========================================

class AnalistaDTO:
    """Objeto de transferência de dados do Analista 100% desacoplado da sessão ORM."""
    def __init__(self, id: int, nome: str, especialidade: str, ativo: bool):
        self.id = int(id)
        self.nome = str(nome)
        self.especialidade = str(especialidade)
        self.ativo = bool(ativo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "especialidade": self.especialidade,
            "ativo": self.ativo,
        }

    def __repr__(self):
        return f"<AnalistaDTO(id={self.id}, nome='{self.nome}', especialidade='{self.especialidade}', ativo={self.ativo})>"


# ==========================================
# MODELOS RELACIONAIS ORM
# ==========================================

class Analista(Base):
    """Modelo da equipe de analistas jurídicos."""
    __tablename__ = "analistas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    especialidade = Column(String(50), nullable=False)  # "Obrigações/Subsídios" ou "Ações Mandamentais"
    ativo = Column(Boolean, default=True, nullable=False)

    demandas_operacionais = relationship(
        "DemandaOperacional",
        back_populates="analista",
        cascade="all, delete-orphan",
    )
    registros_produtividade = relationship(
        "ProdutividadeOperacional",
        back_populates="analista",
        cascade="all, delete-orphan",
    )
    acoes_mandamentais = relationship(
        "AcaoMandamental",
        back_populates="analista",
        cascade="all, delete-orphan",
    )

    def to_dto(self) -> AnalistaDTO:
        return AnalistaDTO(
            id=self.id,
            nome=self.nome,
            especialidade=self.especialidade,
            ativo=self.ativo,
        )


class ProdutividadeOperacional(Base):
    """Registros consolidados de produtividade diária por analista para Obrigações de Fazer e Subsídios."""
    __tablename__ = "produtividade_operacional"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_referencia = Column(Date, nullable=False, index=True)
    id_analista = Column(Integer, ForeignKey("analistas.id", ondelete="CASCADE"), nullable=False)
    quantidade_subsidios = Column(Integer, default=0, nullable=False)
    quantidade_subsidios_urgente = Column(Integer, default=0, nullable=False)
    quantidade_obrigacao_fazer = Column(Integer, default=0, nullable=False)
    quantidade_obrigacao_fazer_urgente = Column(Integer, default=0, nullable=False)
    quantidade_pendencias_anteriores = Column(Integer, default=0, nullable=False)
    quantidade_concluidas_dia = Column(Integer, default=0, nullable=False)
    observacoes = Column(Text, nullable=True)

    analista = relationship("Analista", back_populates="registros_produtividade")


class DemandaOperacional(Base):
    """Demandas de Obrigações de Fazer e Fornecimento de Subsídios (Modelo Histórico/Legado)."""
    __tablename__ = "demandas_operacionais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_processo = Column(String(25), nullable=False, index=True)
    tipo_produto = Column(String(30), nullable=False)  # "Obrigação de Fazer" ou "Subsídios"
    data_recebimento = Column(Date, nullable=False)
    hora_recebimento = Column(Time, nullable=False)
    data_distribuicao = Column(Date, nullable=True)
    id_analista = Column(Integer, ForeignKey("analistas.id", ondelete="SET NULL"), nullable=True)
    is_urgente = Column(Boolean, default=False, nullable=False)
    possui_multa = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="Não Distribuído", nullable=False)  # "Não Distribuído", "Em Andamento", "Concluído"
    data_conclusao = Column(Date, nullable=True)
    observacoes = Column(Text, nullable=True)

    analista = relationship("Analista", back_populates="demandas_operacionais")


class AcaoMandamental(Base):
    """Ações Mandamentais (Mandados de Segurança, Habeas Corpus, Habeas Data)."""
    __tablename__ = "acoes_mandamentais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_processo = Column(String(25), nullable=False, index=True)
    tipo_acao = Column(String(10), nullable=False)  # "MS", "HC", "HD"
    data_entrada = Column(Date, nullable=False)
    id_analista = Column(Integer, ForeignKey("analistas.id", ondelete="SET NULL"), nullable=True)
    is_urgente_liminar = Column(Boolean, default=False, nullable=False)
    data_manifestacao = Column(Date, nullable=True)
    status_tramitacao = Column(String(30), default="Em Elaboração", nullable=False)  # "Em Elaboração", "Aguardando Julgamento", "Transitado em Julgado"
    data_sentenca = Column(Date, nullable=True)
    resultado_merito = Column(String(40), nullable=True)  # "Favorável (Denegado)", "Desfavorável (Concedido)", "Sem Resolução de Mérito"

    analista = relationship("Analista", back_populates="acoes_mandamentais")


class AporteDiario(Base):
    """Registros diários consolidados de demandas que aportam no setor."""
    __tablename__ = "aportes_diarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_aporte = Column(Date, nullable=False, index=True)
    quantidade_subsidios = Column(Integer, default=0, nullable=False)
    quantidade_subsidios_urgente = Column(Integer, default=0, nullable=False)
    quantidade_obrigacao_fazer = Column(Integer, default=0, nullable=False)
    quantidade_obrigacao_fazer_urgente = Column(Integer, default=0, nullable=False)
    observacoes = Column(Text, nullable=True)


class ConfiguracaoSistema(Base):
    """Controle interno de configurações, migrações e flags de produção do sistema."""
    __tablename__ = "configuracoes_sistema"

    chave = Column(String(50), primary_key=True)
    valor = Column(String(255), nullable=False)


# ==========================================
# INICIALIZAÇÃO DO BANCO (PRODUÇÃO)
# ==========================================

def init_db():
    """Inicializa as tabelas no banco de dados se não existirem."""
    Base.metadata.create_all(bind=engine)


def garantir_limpeza_producao() -> bool:
    """
    Garante que no formato de produção, quaisquer registros de teste/demonstração
    anteriores sejam limpos uma única vez no deploy.
    Grava a flag 'modo_producao_ativo' para proteger todos os novos cadastros reais.
    """
    init_db()
    with get_db_session() as session:
        flag = session.query(ConfiguracaoSistema).filter(ConfiguracaoSistema.chave == "modo_producao_ativo").first()
        if flag and flag.valor == "sim":
            return False

        # Limpa dados legados/fictícios de teste
        session.query(AporteDiario).delete()
        session.query(ProdutividadeOperacional).delete()
        session.query(DemandaOperacional).delete()
        session.query(AcaoMandamental).delete()
        session.query(Analista).delete()

        if not flag:
            session.add(ConfiguracaoSistema(chave="modo_producao_ativo", valor="sim"))
        else:
            flag.valor = "sim"

    with engine.connect() as conn:
        conn.execute(text("VACUUM;"))

    return True


def get_total_aportes_count() -> int:
    """Retorna total de registros de aportes diários no sistema."""
    with get_db_session() as session:
        return session.query(AporteDiario).count()


def get_total_produtividade_count() -> int:
    """Retorna total de registros reais de produtividade operacional."""
    with get_db_session() as session:
        return session.query(ProdutividadeOperacional).count()


def get_total_mandamentais_count() -> int:
    """Retorna total de registros reais de ações mandamentais."""
    with get_db_session() as session:
        return session.query(AcaoMandamental).count()


def get_total_analistas_count() -> int:
    """Retorna total de analistas cadastrados."""
    with get_db_session() as session:
        return session.query(Analista).count()


# ==========================================
# OPERAÇÕES CRUD: APORTES DIÁRIOS (DEMANDAS QUE APORTAM)
# ==========================================

def add_aporte_diario(
    data_aporte: Any,
    quantidade_subsidios: int = 0,
    quantidade_subsidios_urgente: int = 0,
    quantidade_obrigacao_fazer: int = 0,
    quantidade_obrigacao_fazer_urgente: int = 0,
    observacoes: Optional[str] = None,
) -> int:
    """Insere um novo registro consolidado de demandas que aportam por data e retorna o ID gerado."""
    dt_aporte = parse_date_flexible(data_aporte) or date.today()
    with get_db_session() as session:
        reg = AporteDiario(
            data_aporte=dt_aporte,
            quantidade_subsidios=max(0, int(quantidade_subsidios or 0)),
            quantidade_subsidios_urgente=max(0, int(quantidade_subsidios_urgente or 0)),
            quantidade_obrigacao_fazer=max(0, int(quantidade_obrigacao_fazer or 0)),
            quantidade_obrigacao_fazer_urgente=max(0, int(quantidade_obrigacao_fazer_urgente or 0)),
            observacoes=observacoes.strip() if observacoes else None,
        )
        session.add(reg)
        session.flush()
        return reg.id


def get_df_aportes_diarios(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
) -> pd.DataFrame:
    """Retorna DataFrame de demandas que aportam por data com filtros aplicados."""
    with engine.connect() as conn:
        query = """
            SELECT 
                id,
                data_aporte,
                quantidade_subsidios,
                quantidade_subsidios_urgente,
                quantidade_obrigacao_fazer,
                quantidade_obrigacao_fazer_urgente,
                observacoes
            FROM aportes_diarios
            WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if data_inicio:
            query += " AND data_aporte >= :data_inicio"
            params["data_inicio"] = data_inicio.isoformat()
        if data_fim:
            query += " AND data_aporte <= :data_fim"
            params["data_fim"] = data_fim.isoformat()

        query += " ORDER BY data_aporte DESC, id DESC"
        df = pd.read_sql_query(text(query), conn, params=params)

    if not df.empty:
        df["data_aporte"] = pd.to_datetime(df["data_aporte"], errors="coerce").dt.date
        df["quantidade_subsidios"] = df["quantidade_subsidios"].fillna(0).astype(int)
        df["quantidade_subsidios_urgente"] = df["quantidade_subsidios_urgente"].fillna(0).astype(int)
        df["quantidade_obrigacao_fazer"] = df["quantidade_obrigacao_fazer"].fillna(0).astype(int)
        df["quantidade_obrigacao_fazer_urgente"] = df["quantidade_obrigacao_fazer_urgente"].fillna(0).astype(int)
        
        # Colunas computadas utilitárias
        df["subsidios_comum"] = (df["quantidade_subsidios"] - df["quantidade_subsidios_urgente"]).clip(lower=0)
        df["obrigacao_fazer_comum"] = (df["quantidade_obrigacao_fazer"] - df["quantidade_obrigacao_fazer_urgente"]).clip(lower=0)
        df["total_geral_aportado"] = df["quantidade_subsidios"] + df["quantidade_obrigacao_fazer"]
        df["total_urgentes_aportados"] = df["quantidade_subsidios_urgente"] + df["quantidade_obrigacao_fazer_urgente"]
    else:
        df = pd.DataFrame(columns=[
            "id", "data_aporte", "quantidade_subsidios", "quantidade_subsidios_urgente",
            "quantidade_obrigacao_fazer", "quantidade_obrigacao_fazer_urgente",
            "observacoes", "subsidios_comum", "obrigacao_fazer_comum",
            "total_geral_aportado", "total_urgentes_aportados"
        ])
    return df


def bulk_update_aportes_diarios(registros: List[Dict[str, Any]]) -> int:
    """Atualização em lote de registros de aportes diários via DataFrame editado."""
    if not registros:
        return 0
    updated_count = 0
    with get_db_session() as session:
        for rec in registros:
            reg_id = rec.get("id")
            if not reg_id:
                continue
            item = session.query(AporteDiario).filter(AporteDiario.id == int(reg_id)).first()
            if not item:
                continue
            
            if "data_aporte" in rec:
                dt = parse_date_flexible(rec["data_aporte"])
                if dt:
                    item.data_aporte = dt
            if "quantidade_subsidios" in rec:
                item.quantidade_subsidios = max(0, int(rec["quantidade_subsidios"] or 0))
            if "quantidade_subsidios_urgente" in rec:
                item.quantidade_subsidios_urgente = max(0, int(rec["quantidade_subsidios_urgente"] or 0))
            if "quantidade_obrigacao_fazer" in rec:
                item.quantidade_obrigacao_fazer = max(0, int(rec["quantidade_obrigacao_fazer"] or 0))
            if "quantidade_obrigacao_fazer_urgente" in rec:
                item.quantidade_obrigacao_fazer_urgente = max(0, int(rec["quantidade_obrigacao_fazer_urgente"] or 0))
            if "observacoes" in rec:
                item.observacoes = str(rec["observacoes"]) if rec["observacoes"] is not None else ""
            updated_count += 1
    return updated_count


def delete_aporte_diario(id_registro: int) -> bool:
    """Exclui um registro de aporte diário pelo ID."""
    with get_db_session() as session:
        item = session.query(AporteDiario).filter(AporteDiario.id == int(id_registro)).first()
        if item:
            session.delete(item)
            return True
        return False


# ==========================================
# OPERAÇÕES CRUD: ANALISTAS
# ==========================================

def get_analistas(active_only: bool = False, especialidade: Optional[str] = None) -> List[AnalistaDTO]:
    """
    Recupera a lista de analistas cadastrados retornando DTOs seguros desacoplados.
    Evita DetachedInstanceError.
    """
    with get_db_session() as session:
        query = session.query(Analista)
        if active_only:
            query = query.filter(Analista.ativo.is_(True))
        if especialidade:
            query = query.filter(Analista.especialidade == especialidade)
        analistas = query.order_by(Analista.nome).all()
        return [a.to_dto() for a in analistas]


def add_analista(nome: str, especialidade: str, ativo: bool = True) -> AnalistaDTO:
    """Cadastra um novo analista jurídico."""
    with get_db_session() as session:
        analista = Analista(nome=nome.strip(), especialidade=especialidade, ativo=ativo)
        session.add(analista)
        session.flush()
        dto = analista.to_dto()
        return dto


# ==========================================
# OPERAÇÕES CRUD: PRODUTIVIDADE OPERACIONAL (OBRIGAÇÃO DE FAZER & SUBSÍDIOS)
# ==========================================

def add_produtividade_operacional(
    data_referencia: date,
    id_analista: int,
    quantidade_subsidios: int = 0,
    quantidade_subsidios_urgente: int = 0,
    quantidade_obrigacao_fazer: int = 0,
    quantidade_obrigacao_fazer_urgente: int = 0,
    quantidade_pendencias_anteriores: int = 0,
    quantidade_concluidas_dia: int = 0,
    observacoes: Optional[str] = None,
) -> int:
    """Insere um novo registro de produtividade diária por analista e retorna o ID gerado."""
    with get_db_session() as session:
        prod = ProdutividadeOperacional(
            data_referencia=data_referencia,
            id_analista=int(id_analista),
            quantidade_subsidios=max(0, int(quantidade_subsidios or 0)),
            quantidade_subsidios_urgente=max(0, int(quantidade_subsidios_urgente or 0)),
            quantidade_obrigacao_fazer=max(0, int(quantidade_obrigacao_fazer or 0)),
            quantidade_obrigacao_fazer_urgente=max(0, int(quantidade_obrigacao_fazer_urgente or 0)),
            quantidade_pendencias_anteriores=max(0, int(quantidade_pendencias_anteriores or 0)),
            quantidade_concluidas_dia=max(0, int(quantidade_concluidas_dia or 0)),
            observacoes=str(observacoes).strip() if observacoes else "",
        )
        session.add(prod)
        session.flush()
        return prod.id


def bulk_update_produtividade_operacional(records: List[Dict[str, Any]]) -> int:
    """Atualiza múltiplos registros de produtividade diária em uma transação única."""
    updated_count = 0
    with get_db_session() as session:
        for rec in records:
            p_id = rec.get("id")
            if not p_id:
                continue

            prod = session.query(ProdutividadeOperacional).filter(ProdutividadeOperacional.id == p_id).first()
            if not prod:
                continue

            if "data_referencia" in rec:
                dt = parse_date_flexible(rec["data_referencia"])
                if dt:
                    prod.data_referencia = dt

            if "id_analista" in rec and rec["id_analista"]:
                try:
                    prod.id_analista = int(rec["id_analista"])
                except (ValueError, TypeError):
                    pass

            if "quantidade_subsidios" in rec:
                prod.quantidade_subsidios = max(0, int(rec["quantidade_subsidios"] or 0))

            if "quantidade_subsidios_urgente" in rec:
                prod.quantidade_subsidios_urgente = max(0, int(rec["quantidade_subsidios_urgente"] or 0))

            if "quantidade_obrigacao_fazer" in rec:
                prod.quantidade_obrigacao_fazer = max(0, int(rec["quantidade_obrigacao_fazer"] or 0))

            if "quantidade_obrigacao_fazer_urgente" in rec:
                prod.quantidade_obrigacao_fazer_urgente = max(0, int(rec["quantidade_obrigacao_fazer_urgente"] or 0))

            if "quantidade_pendencias_anteriores" in rec:
                prod.quantidade_pendencias_anteriores = max(0, int(rec["quantidade_pendencias_anteriores"] or 0))

            if "quantidade_concluidas_dia" in rec:
                prod.quantidade_concluidas_dia = max(0, int(rec["quantidade_concluidas_dia"] or 0))

            if "observacoes" in rec:
                prod.observacoes = str(rec["observacoes"]) if rec["observacoes"] is not None else ""

            updated_count += 1

    return updated_count


def delete_produtividade_operacional(id_registro: int) -> bool:
    """Exclui um registro de produtividade pelo ID."""
    with get_db_session() as session:
        prod = session.query(ProdutividadeOperacional).filter(ProdutividadeOperacional.id == id_registro).first()
        if prod:
            session.delete(prod)
            return True
        return False


# ==========================================
# OPERAÇÕES CRUD: DEMANDAS OPERACIONAIS (LEGADO)
# ==========================================

def add_demanda_operacional(
    numero_processo: str,
    tipo_produto: str,
    data_recebimento: date,
    hora_recebimento: time,
    data_distribuicao: Optional[date] = None,
    id_analista: Optional[int] = None,
    is_urgente: bool = False,
    possui_multa: bool = False,
    status: str = "Não Distribuído",
    data_conclusao: Optional[date] = None,
    observacoes: Optional[str] = None,
) -> int:
    """Insere uma nova demanda operacional e retorna o ID gerado."""
    if data_conclusao and data_conclusao < data_recebimento:
        raise ValueError("Data de conclusão não pode ser anterior à data de recebimento.")

    with get_db_session() as session:
        demanda = DemandaOperacional(
            numero_processo=numero_processo.strip(),
            tipo_produto=tipo_produto,
            data_recebimento=data_recebimento,
            hora_recebimento=hora_recebimento,
            data_distribuicao=data_distribuicao,
            id_analista=id_analista,
            is_urgente=is_urgente,
            possui_multa=possui_multa,
            status=status,
            data_conclusao=data_conclusao,
            observacoes=observacoes.strip() if observacoes else "",
        )
        session.add(demanda)
        session.flush()
        return demanda.id


def bulk_update_demandas_operacionais(records: List[Dict[str, Any]]) -> int:
    """
    Atualiza múltiplos registros de demandas operacionais em uma transação única.
    Aplica validações de consistência cronológica e sanitização de dados.
    """
    updated_count = 0
    with get_db_session() as session:
        for rec in records:
            demanda_id = rec.get("id")
            if not demanda_id:
                continue

            demanda = session.query(DemandaOperacional).filter(DemandaOperacional.id == demanda_id).first()
            if not demanda:
                continue

            if "status" in rec and rec["status"]:
                demanda.status = str(rec["status"]).strip()

            if "id_analista" in rec:
                val = rec["id_analista"]
                demanda.id_analista = int(val) if val and str(val).isdigit() else None
                if demanda.id_analista and not demanda.data_distribuicao:
                    demanda.data_distribuicao = date.today()

            if "data_distribuicao" in rec and rec["data_distribuicao"]:
                demanda.data_distribuicao = parse_date_flexible(rec["data_distribuicao"])

            if "data_conclusao" in rec:
                d_conc = parse_date_flexible(rec["data_conclusao"])
                if d_conc is None:
                    demanda.data_conclusao = None
                else:
                    if d_conc < demanda.data_recebimento:
                        raise ValueError(
                            f"Processo {demanda.numero_processo}: Data de conclusão ({d_conc.strftime('%d/%m/%Y')}) "
                            f"não pode ser anterior ao recebimento ({demanda.data_recebimento.strftime('%d/%m/%Y')})."
                        )
                    demanda.data_conclusao = d_conc
                    if demanda.status != "Concluído":
                        demanda.status = "Concluído"

            if "is_urgente" in rec:
                demanda.is_urgente = bool(rec["is_urgente"])

            if "possui_multa" in rec:
                demanda.possui_multa = bool(rec["possui_multa"])

            if "observacoes" in rec:
                demanda.observacoes = str(rec["observacoes"]) if rec["observacoes"] is not None else ""

            updated_count += 1

    return updated_count


def distribute_demandas_operacionais_batch(analista_ids: List[int], limit: Optional[int] = None) -> int:
    """
    Simula e executa a distribuição em lote de demandas com status 'Não Distribuído'
    utilizando algoritmo de balanceamento equitativo (Round-Robin).
    """
    if not analista_ids:
        return 0

    with get_db_session() as session:
        query = session.query(DemandaOperacional).filter(
            (DemandaOperacional.status == "Não Distribuído") | (DemandaOperacional.id_analista.is_(None))
        ).order_by(
            DemandaOperacional.is_urgente.desc(),
            DemandaOperacional.possui_multa.desc(),
            DemandaOperacional.data_recebimento.asc(),
            DemandaOperacional.hora_recebimento.asc(),
        )
        if limit:
            query = query.limit(limit)

        demandas_pendentes = query.all()
        if not demandas_pendentes:
            return 0

        hoje = date.today()
        count = 0
        total_analistas = len(analista_ids)

        for idx, dem in enumerate(demandas_pendentes):
            analista_escolhido = analista_ids[idx % total_analistas]
            dem.id_analista = analista_escolhido
            dem.data_distribuicao = hoje
            dem.status = "Em Andamento"
            count += 1

        return count


# ==========================================
# OPERAÇÕES CRUD: AÇÕES MANDAMENTAIS
# ==========================================

def add_acao_mandamental(
    numero_processo: str,
    tipo_acao: str,
    data_entrada: date,
    id_analista: Optional[int] = None,
    is_urgente_liminar: bool = False,
    data_manifestacao: Optional[date] = None,
    status_tramitacao: str = "Em Elaboração",
    data_sentenca: Optional[date] = None,
    resultado_merito: Optional[str] = None,
) -> int:
    """Cadastra uma nova ação mandamental (MS, HC, HD) e retorna seu ID."""
    with get_db_session() as session:
        acao = AcaoMandamental(
            numero_processo=numero_processo.strip(),
            tipo_acao=tipo_acao,
            data_entrada=data_entrada,
            id_analista=id_analista,
            is_urgente_liminar=is_urgente_liminar,
            data_manifestacao=data_manifestacao,
            status_tramitacao=status_tramitacao,
            data_sentenca=data_sentenca,
            resultado_merito=resultado_merito,
        )
        session.add(acao)
        session.flush()
        return acao.id


def bulk_update_acoes_mandamentais(records: List[Dict[str, Any]]) -> int:
    """Atualiza múltiplos registros de ações mandamentais em transação atômica."""
    updated_count = 0
    with get_db_session() as session:
        for rec in records:
            acao_id = rec.get("id")
            if not acao_id:
                continue

            acao = session.query(AcaoMandamental).filter(AcaoMandamental.id == acao_id).first()
            if not acao:
                continue

            if "id_analista" in rec:
                val = rec["id_analista"]
                acao.id_analista = int(val) if val and str(val).isdigit() else None

            if "status_tramitacao" in rec and rec["status_tramitacao"]:
                acao.status_tramitacao = str(rec["status_tramitacao"]).strip()

            if "data_manifestacao" in rec:
                acao.data_manifestacao = parse_date_flexible(rec["data_manifestacao"])

            if "data_sentenca" in rec:
                acao.data_sentenca = parse_date_flexible(rec["data_sentenca"])

            if "resultado_merito" in rec:
                res = rec["resultado_merito"]
                acao.resultado_merito = str(res).strip() if res and not pd.isna(res) and str(res).strip() != "None" else None

            if "is_urgente_liminar" in rec:
                acao.is_urgente_liminar = bool(rec["is_urgente_liminar"])

            updated_count += 1

    return updated_count


# ==========================================
# CONSULTAS ANALÍTICAS PARA DATAFRAMES
# ==========================================

def get_df_produtividade_operacional(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    id_analista: Optional[int] = None,
) -> pd.DataFrame:
    """
    Retorna DataFrame consolidado de produtividade diária por analista.
    """
    with engine.connect() as conn:
        query = """
            SELECT
                p.id,
                p.data_referencia,
                p.id_analista,
                COALESCE(a.nome, 'Não Atribuído') AS analista_nome,
                COALESCE(a.especialidade, 'Obrigações/Subsídios') AS especialidade,
                p.quantidade_subsidios,
                p.quantidade_subsidios_urgente,
                p.quantidade_obrigacao_fazer,
                p.quantidade_obrigacao_fazer_urgente,
                p.quantidade_pendencias_anteriores,
                p.quantidade_concluidas_dia,
                p.observacoes
            FROM produtividade_operacional p
            LEFT JOIN analistas a ON p.id_analista = a.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if data_inicio:
            query += " AND p.data_referencia >= :data_inicio"
            params["data_inicio"] = data_inicio.isoformat()
        if data_fim:
            query += " AND p.data_referencia <= :data_fim"
            params["data_fim"] = data_fim.isoformat()
        if id_analista:
            query += " AND p.id_analista = :id_analista"
            params["id_analista"] = id_analista

        query += " ORDER BY p.data_referencia DESC, a.nome ASC"
        df = pd.read_sql_query(text(query), conn, params=params)

    if not df.empty:
        df["data_referencia"] = pd.to_datetime(df["data_referencia"], errors="coerce").dt.date
        df["total_entradas_dia"] = df["quantidade_subsidios"] + df["quantidade_obrigacao_fazer"]
        df["total_urgentes_dia"] = df["quantidade_subsidios_urgente"] + df["quantidade_obrigacao_fazer_urgente"]
        df["saldo_diario"] = df["total_entradas_dia"] - df["quantidade_concluidas_dia"]
        df["pendencias_finais_dia"] = df["quantidade_pendencias_anteriores"] + df["saldo_diario"]
    else:
        df = pd.DataFrame(columns=[
            "id", "data_referencia", "id_analista", "analista_nome", "especialidade",
            "quantidade_subsidios", "quantidade_subsidios_urgente",
            "quantidade_obrigacao_fazer", "quantidade_obrigacao_fazer_urgente",
            "quantidade_pendencias_anteriores", "quantidade_concluidas_dia",
            "observacoes", "total_entradas_dia", "total_urgentes_dia",
            "saldo_diario", "pendencias_finais_dia"
        ])
    return df


def get_df_demandas_operacionais(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    id_analista: Optional[int] = None,
    tipo_produto: Optional[str] = None,
    apenas_urgentes: Optional[bool] = None,
) -> pd.DataFrame:
    """
    Retorna DataFrame de Demandas Operacionais com joins e filtros aplicados.
    """
    with engine.connect() as conn:
        query = """
            SELECT
                d.id,
                d.numero_processo,
                d.tipo_produto,
                d.data_recebimento,
                d.hora_recebimento,
                d.data_distribuicao,
                d.id_analista,
                COALESCE(a.nome, 'Não Atribuído') AS analista_nome,
                d.is_urgente,
                d.possui_multa,
                d.status,
                d.data_conclusao,
                d.observacoes
            FROM demandas_operacionais d
            LEFT JOIN analistas a ON d.id_analista = a.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}

        if data_inicio:
            query += " AND d.data_recebimento >= :data_inicio"
            params["data_inicio"] = data_inicio.isoformat()
        if data_fim:
            query += " AND d.data_recebimento <= :data_fim"
            params["data_fim"] = data_fim.isoformat()
        if id_analista:
            query += " AND d.id_analista = :id_analista"
            params["id_analista"] = id_analista
        if tipo_produto and tipo_produto != "Todos":
            query += " AND d.tipo_produto = :tipo_produto"
            params["tipo_produto"] = tipo_produto
        if apenas_urgentes is True:
            query += " AND (d.is_urgente = 1 OR d.possui_multa = 1)"
        elif apenas_urgentes is False:
            query += " AND (d.is_urgente = 0 AND d.possui_multa = 0)"

        query += " ORDER BY d.data_recebimento DESC, d.hora_recebimento DESC"

        df = pd.read_sql_query(text(query), conn, params=params)

    if not df.empty:
        df["data_recebimento"] = pd.to_datetime(df["data_recebimento"], errors="coerce").dt.date
        df["data_distribuicao"] = pd.to_datetime(df["data_distribuicao"], errors="coerce").dt.date
        df["data_conclusao"] = pd.to_datetime(df["data_conclusao"], errors="coerce").dt.date
        df["is_urgente"] = df["is_urgente"].astype(bool)
        df["possui_multa"] = df["possui_multa"].astype(bool)

    return df


def get_df_acoes_mandamentais(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    id_analista: Optional[int] = None,
    tipo_acao: Optional[str] = None,
    apenas_liminares: Optional[bool] = None,
) -> pd.DataFrame:
    """
    Retorna DataFrame de Ações Mandamentais com joins e filtros analíticos.
    """
    with engine.connect() as conn:
        query = """
            SELECT
                m.id,
                m.numero_processo,
                m.tipo_acao,
                m.data_entrada,
                m.id_analista,
                COALESCE(a.nome, 'Não Atribuído') AS analista_nome,
                m.is_urgente_liminar,
                m.data_manifestacao,
                m.status_tramitacao,
                m.data_sentenca,
                m.resultado_merito
            FROM acoes_mandamentais m
            LEFT JOIN analistas a ON m.id_analista = a.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}

        if data_inicio:
            query += " AND m.data_entrada >= :data_inicio"
            params["data_inicio"] = data_inicio.isoformat()
        if data_fim:
            query += " AND m.data_entrada <= :data_fim"
            params["data_fim"] = data_fim.isoformat()
        if id_analista:
            query += " AND m.id_analista = :id_analista"
            params["id_analista"] = id_analista
        if tipo_acao and tipo_acao != "Todos":
            query += " AND m.tipo_acao = :tipo_acao"
            params["tipo_acao"] = tipo_acao
        if apenas_liminares is True:
            query += " AND m.is_urgente_liminar = 1"
        elif apenas_liminares is False:
            query += " AND m.is_urgente_liminar = 0"

        query += " ORDER BY m.data_entrada DESC"

        df = pd.read_sql_query(text(query), conn, params=params)

    if not df.empty:
        df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce").dt.date
        df["data_manifestacao"] = pd.to_datetime(df["data_manifestacao"], errors="coerce").dt.date
        df["data_sentenca"] = pd.to_datetime(df["data_sentenca"], errors="coerce").dt.date
        df["is_urgente_liminar"] = df["is_urgente_liminar"].astype(bool)

    return df


def get_df_analistas() -> pd.DataFrame:
    """Retorna DataFrame dos analistas."""
    with engine.connect() as conn:
        query = "SELECT id, nome, especialidade, ativo FROM analistas ORDER BY nome ASC"
        df = pd.read_sql_query(text(query), conn)
    if not df.empty:
        df["ativo"] = df["ativo"].astype(bool)
    return df


def clear_all_records(keep_analistas: bool = False) -> Dict[str, int]:
    """
    Remove todos os registros operacionais e mandamentais do banco de dados SQLite.
    Se keep_analistas for False, também remove o cadastro de analistas.
    Garante execução com schema 100% preservado e executa VACUUM.
    """
    contagem: Dict[str, int] = {}
    with get_db_session() as session:
        contagem["aportes_diarios"] = session.query(AporteDiario).delete()
        contagem["produtividade_operacional"] = session.query(ProdutividadeOperacional).delete()
        contagem["demandas_operacionais"] = session.query(DemandaOperacional).delete()
        contagem["acoes_mandamentais"] = session.query(AcaoMandamental).delete()
        if not keep_analistas:
            contagem["analistas"] = session.query(Analista).delete()
        else:
            contagem["analistas"] = 0

    with engine.connect() as conn:
        conn.execute(text("VACUUM;"))

    return contagem