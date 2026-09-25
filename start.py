"""
start.py - Inicializador e Verificador Automático da Aplicação
Sistema de Gestão Estratégica e Operacional de Demandas Jurídicas.
"""

import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

REQUIRED_PACKAGES = [
    ("streamlit", "streamlit>=1.30.0"),
    ("plotly", "plotly>=5.18.0"),
    ("pandas", "pandas>=2.0.0"),
    ("numpy", "numpy>=1.24.0"),
    ("sqlalchemy", "sqlalchemy>=2.0.0"),
    ("openpyxl", "openpyxl>=3.1.0"),
]

def check_and_install_dependencies():
    """Verifica e instala dependências ausentes de forma automática."""
    print("=" * 65)
    print("  VERIFICADOR DE AMBIENTE: GESTÃO DE DEMANDAS JURÍDICAS")
    print("=" * 65)

    missing = []
    for module_name, pip_spec in REQUIRED_PACKAGES:
        try:
            __import__(module_name)
            print(f" [OK] {module_name} disponível.")
        except ImportError:
            print(f" [!] {module_name} ausente.")
            missing.append(pip_spec)

    if missing:
        print("\nInstalando dependências ausentes via pip...")
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        try:
            subprocess.run(cmd, check=True)
            print("[OK] Instalação concluída com sucesso!\n")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao instalar dependências: {e}")
            sys.exit(1)
    else:
        print("\nTodas as dependências estão presentes e funcionais.\n")

def initialize_database():
    """Inicializa banco de dados em modo de produção limpo."""
    print("Inicializando banco de dados relacional em modo de produção...")
    try:
        import database as db
        db.init_db()
        db.garantir_limpeza_producao()
        print("[OK] Banco de dados pronto para produção!")
    except Exception as e:
        print(f"[AVISO] Não foi possível inicializar a base antecipadamente: {e}")

def run_streamlit():
    """Inicia o servidor Streamlit."""
    print("=" * 65)
    print("  INICIANDO APLICAÇÃO WEB STREAMLIT...")
    print("  URL Local: http://localhost:8501")
    print("  Para encerrar: Pressione Ctrl + C no terminal")
    print("=" * 65)

    app_path = BASE_DIR / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nAplicação encerrada pelo usuário.")

if __name__ == "__main__":
    check_and_install_dependencies()
    initialize_database()
    run_streamlit()
