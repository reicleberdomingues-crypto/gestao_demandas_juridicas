# ⚖️ Gestão Estratégica e Operacional de Demandas Jurídicas

Aplicação corporativa de alta performance desenvolvida em **Python** e **Streamlit**, voltada à gestão de fluxo diário, distribuição equitativa de carga de trabalho, mensuração de produtividade individual/coletiva, acompanhamento de prazos e cálculo automatizado de **KPIs** e **KGIs** para departamentos jurídicos e procuradorias.

---

## 🏛️ 1. Arquitetura Modular Desacoplada

O projeto foi construído seguindo o princípio da Separação de Responsabilidades (*Separation of Concerns*):

```
F:\gestao_demandas_juridicas\
├── database.py              # Camada de Persistência: Modelos relacionais SQLAlchemy, WAL SQLite, transações atômicas, DTOs e CRUD
├── metrics.py               # Camada de Negócio: Regras analíticas, cálculo de dias úteis, KPIs, KGIs e séries temporais
├── app.py                   # Camada de Apresentação: Interface Streamlit com 4 abas, formulários, data_editor e gráficos Plotly
├── seed_data.py             # Carga inicial e demonstrativa com massa de dados jurídicos realistas
├── start.py                 # Inicializador inteligente em Python com verificação e instalação automática de pacotes
├── run.bat                  # Script batch auto-instalador para inicialização direta com duplo clique no Windows
├── test_system.py           # Bateria de testes unitários automatizados para integridade do sistema
├── requirements.txt         # Lista de dependências Python (streamlit, plotly, pandas, sqlalchemy, openpyxl, pypdf)
└── juridico.db              # Banco de dados relacional SQLite transacional (gerado na primeira execução)
```

---

## 🚀 2. Como Executar a Aplicação (Opções Fáceis)

### Opção A: Executar via `run.bat` (Recomendado - 1 Clique)
Basta dar um **duplo clique no arquivo `run.bat`** em `F:\gestao_demandas_juridicas\`.
- O script localiza o interpretador Python automaticamente.
- Se pacotes como `streamlit` ou `plotly` não estiverem instalados, ele instala automaticamente via `pip`.
- Em seguida, abre a aplicação no navegador em `http://localhost:8501`.

### Opção B: Executar via `start.py` (Linha de Comando)
Abra o prompt de comando ou PowerShell e execute:
```bash
python F:\gestao_demandas_juridicas\start.py
```
*(ou se estiver dentro da pasta: `python start.py`)*

### Opção C: Execução Manual Padrão
```bash
cd F:\gestao_demandas_juridicas
pip install -r requirements.txt
streamlit run app.py
```

---

## 📊 3. Regras de Negócio e Indicadores Implementados

### A. Obrigações de Fazer e Subsídios
- **Volume Recebido:** Total de demandas com entrada no período filtrado.
- **Volume Distribuído:** Total de demandas atribuídas a analistas no período.
- **Volume Concluído:** Demandas finalizadas no período.
- **Backlog / Pendências:** Total de demandas ativas (`status != 'Concluído'`).
- **Taxa de Produtividade (%):** Relação percentual `(Concluídas / Distribuídas) * 100`.
- **Tempo Médio de Resposta (TMR):** Diferença em dias úteis entre o recebimento e a conclusão (`numpy.busday_count`).
- **KGI 1 (Tempestividade de Urgentes/Multas):** Percentual de demandas com `is_urgente=True` ou `possui_multa=True` concluídas estritamente na mesma data de recebimento (`data_conclusao == data_recebimento`). *Meta: 100%*.
- **KGI 2 (Conclusão Semanal):** Percentual de demandas concluídas dentro da mesma semana calendário do seu recebimento.

### B. Ações Mandamentais (MS, HC, HD)
- **Histórico Diário de Entrada:** Monitoramento contínuo de novas impetrações.
- **KGI Taxa de Êxito Anual (MS):** Percentual de Mandados de Segurança sentenciados cujo mérito foi favorável à instituição (`Favorável (Denegado)` ou `Sem Resolução de Mérito`).
- **KGI Tempestividade de HC e Liminares:** Percentual de HC ou ações com liminar com manifestação prestada em até 24h / no mesmo dia (`<= 1 dia`). *Meta: 100%*.

---

## 🖥️ 4. Abas e Funcionalidades da Aplicação

1. **📥 Aba 1: Entrada e Distribuição Diária**
   - Formulários com validação estrita de formato CNJ (`NNNNNNN-DD.YYYY.J.TR.OOOO`).
   - Modalidade de entrada para Obrigações de Fazer, Subsídios e Ações Mandamentais.
   - **Distribuição em Lote (Round-Robin)**: Distribuição equitativa automática da fila de pendências entre analistas selecionados.
   - Gestão rápida de analistas (cadastro e ativação/desativação).

2. **⚖️ Aba 2: Gestão e Baixa de Demandas**
   - Tabela editável (`st.data_editor`) com identificadores protegidos contra edição acidental.
   - Atualização de status, resultado de mérito, observações e data de conclusão.
   - **Validação temporal em tempo real**: Bloqueia e emite erro caso a data de conclusão seja anterior ao recebimento.

3. **📊 Aba 3: Painel Gerencial de Produtividade (Dashboard)**
   - Barra lateral com filtros múltiplos combinados (datas, analistas, produto, urgência).
   - Cartões de métricas (`st.metric`) com deltas comparativos.
   - Gráfico de **Entradas vs. Saídas Diárias com Passivo Acumulado** (identificação imediata de gargalos operacionais).
   - Gráfico de barras horizontais de **Produtividade por Analista** com linha de meta corporativa (80%).
   - Velocímetros interativos (Gauges Plotly) dos **KGIs Estratégicos** (Urgência, Êxito de MS e Tempestividade de HC).
   - **Tabela de Alerta Crítico**: Card em destaque vermelho para processos urgentes ou com multa diária pendentes de conclusão.

4. **⚙️ Aba 4: Automação e Integrações**
   - **Leitor Inteligente de Intimações**: Upload de PDF ou colagem de texto com extração automatizada de número CNJ via Regex, diagnóstico de urgência e multa, e botão de importação com 1 clique.
   - **Central de Exportação**: Download em `.xlsx` (Excel multi-abas) e `.csv` (UTF-8 com BOM).
   - **Ferramenta de Amostra**: Botão para regenerar base sintética de demonstração.

---

## 🧪 5. Execução dos Testes Automatizados
Para rodar a suíte de testes de integridade relacional e regras de negócio:
```bash
python F:\gestao_demandas_juridicas\test_system.py
```
