# Testes Automatizados

Este diretório contém os testes automatizados do projeto Direito Fácil API.

## Estrutura de Testes

- `test_rag_service.py` - Testes para o serviço RAG (embeddings, busca, geração de respostas)
- `test_prompt_builder.py` - Testes para o sistema de prompts dinâmicos
- `test_main.py` - Testes da aplicação principal
- `test_user.py` - Testes de usuários
- `test_performance.py` - Testes de performance
- `conftest.py` - Configurações e fixtures compartilhadas

## Executar os Testes

### Todos os testes
```bash
pytest
```

### Testes específicos
```bash
# Apenas testes do RAG Service
pytest tests/test_rag_service.py

# Apenas testes do Prompt Builder
pytest tests/test_prompt_builder.py

# Um teste específico
pytest tests/test_rag_service.py::TestRAGService::test_cache_key_generation
```

### Com cobertura
```bash
pytest --cov=app --cov-report=html
```

### Com saída verbosa
```bash
pytest -v
```

### Testes assíncronos
```bash
pytest -k "async"
```

## Cobertura de Testes

### RAG Service (`test_rag_service.py`)
- ✅ Cache de embeddings (geração, hit, miss, limite de tamanho)
- ✅ Busca de documentos relevantes
- ✅ Geração de respostas jurídicas
- ✅ Diferentes níveis de complexidade
- ✅ Health checks
- ✅ Estatísticas do cache

### Prompt Builder (`test_prompt_builder.py`)
- ✅ Geração de prompts para todos os níveis de complexidade
- ✅ Prompts de usuário com e sem contexto
- ✅ Disclaimers por categoria jurídica
- ✅ Instruções adicionais

## Boas Práticas

1. **Isolamento**: Cada teste deve ser independente
2. **Mocks**: Use mocks para chamadas externas (OpenAI, ChromaDB)
3. **Fixtures**: Reutilize fixtures para setup comum
4. **Nomes descritivos**: Nome do teste deve descrever o que está sendo testado
5. **AAA Pattern**: Arrange, Act, Assert

## Exemplo de Teste

```python
@pytest.mark.asyncio
async def test_generate_legal_response(rag_service, sample_docs):
    # Arrange
    question = "Quais são meus direitos?"
    
    # Act
    response = await rag_service.generate_legal_response(
        question=question,
        relevant_docs=sample_docs,
        complexity=ComplexityLevel.SIMPLE
    )
    
    # Assert
    assert isinstance(response, LegalResponse)
    assert len(response.sources) > 0
    assert 0 <= response.confidence_score <= 100
```

## Configuração do pytest

Veja `pytest.ini` para configurações globais.

## CI/CD

Os testes são executados automaticamente no CI/CD antes de cada deploy.
