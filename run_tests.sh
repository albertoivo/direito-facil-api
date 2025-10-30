#!/bin/bash

# Script para executar testes do Direito Fácil API

echo "🧪 Iniciando testes do Direito Fácil API..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest não está instalado${NC}"
    echo "Instale com: pip install -r requirements.txt"
    exit 1
fi

# Função para executar testes
run_tests() {
    local test_type=$1
    local test_path=$2
    
    echo -e "${YELLOW}📝 Executando $test_type...${NC}"
    pytest "$test_path" -v
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $test_type passou!${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ $test_type falhou!${NC}"
        echo ""
        return 1
    fi
}

# Menu de opções
case "$1" in
    "all"|"")
        echo "Executando todos os testes..."
        pytest -v
        ;;
    "rag")
        run_tests "Testes do RAG Service" "tests/test_rag_service.py"
        ;;
    "prompt")
        run_tests "Testes do Prompt Builder" "tests/test_prompt_builder.py"
        ;;
    "validator")
        run_tests "Testes do Response Validator" "tests/test_response_validator.py"
        ;;
    "coverage")
        echo -e "${YELLOW}📊 Executando testes com cobertura...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term
        echo -e "${GREEN}✅ Relatório de cobertura gerado em htmlcov/index.html${NC}"
        ;;
    "watch")
        echo -e "${YELLOW}👀 Modo watch ativado (requer pytest-watch)${NC}"
        ptw -- -v
        ;;
    "quick")
        echo -e "${YELLOW}⚡ Testes rápidos (sem testes lentos)${NC}"
        pytest -v -m "not slow"
        ;;
    *)
        echo "Uso: ./run_tests.sh [opção]"
        echo ""
        echo "Opções:"
        echo "  all       - Executar todos os testes (padrão)"
        echo "  rag       - Executar apenas testes do RAG Service"
        echo "  prompt    - Executar apenas testes do Prompt Builder"
        echo "  validator - Executar apenas testes do Response Validator"
        echo "  coverage  - Executar com relatório de cobertura"
        echo "  watch     - Modo watch (reexecuta ao salvar)"
        echo "  quick     - Testes rápidos (pula testes lentos)"
        exit 1
        ;;
esac

exit $?
