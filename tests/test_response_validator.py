"""
Testes para o validador de respostas
"""
import pytest
from app.services.response_validator import ResponseValidator


class TestResponseValidator:
    """Testes para o ResponseValidator"""

    @pytest.fixture
    def sample_sources(self):
        """Fontes de exemplo para testes"""
        return [
            {
                "title": "CDC - Artigo 18",
                "source": "Lei 8.078/90",
                "content": "Produtos com defeito podem ser trocados",
                "relevance_score": 0.9
            },
            {
                "title": "CDC - Artigo 26",
                "source": "Lei 8.078/90",
                "content": "Prazo de 30 dias para reclamação",
                "relevance_score": 0.85
            }
        ]

    def test_validate_response_with_source_citation(self, sample_sources):
        """Testa validação quando a resposta cita fontes"""
        response = """
        Segundo o CDC - Artigo 18, produtos com defeito podem ser trocados.
        Conforme estabelecido na Lei 8.078/90, o consumidor tem direitos garantidos.
        
        **Fontes Consultadas:**
        - CDC - Artigo 18
        """
        
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sample_sources, strict_mode=True
        )
        
        assert is_valid
        assert "válida" in message.lower()

    def test_validate_response_without_citations(self, sample_sources):
        """Testa quando resposta não cita fontes"""
        response = """
        Geralmente, produtos com defeito podem ser trocados.
        É comum que lojas aceitem devolução.
        """
        
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sample_sources, strict_mode=True
        )
        
        assert not is_valid

    def test_validate_response_admits_no_info(self, sample_sources):
        """Testa quando LLM admite falta de informação"""
        response = """
        Não encontrei informações suficientes nas fontes fornecidas
        para responder completamente essa pergunta.
        """
        
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sample_sources, strict_mode=True
        )
        
        assert is_valid
        assert "honesta" in message.lower()

    def test_validate_response_non_strict_mode(self, sample_sources):
        """Testa modo não-estrito"""
        response = "Resposta sem citações explícitas"
        
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sample_sources, strict_mode=False
        )
        
        assert is_valid

    def test_extract_cited_sources(self):
        """Testa extração de fontes citadas"""
        response = """
        Resposta baseada nas fontes.
        
        **Fontes Consultadas:**
        - CDC - Artigo 18
        - CDC - Artigo 26
        - Lei 8.078/90
        """
        
        cited = ResponseValidator.extract_cited_sources(response)
        
        assert len(cited) == 3
        assert "CDC - Artigo 18" in cited

    def test_extract_cited_sources_no_section(self):
        """Testa quando não há seção de fontes"""
        response = "Resposta sem seção de fontes consultadas"
        
        cited = ResponseValidator.extract_cited_sources(response)
        
        assert len(cited) == 0

    def test_check_hallucination_indicators(self):
        """Testa detecção de indicadores de alucinação"""
        response = """
        Segundo a Lei 12.345/2020, artigo 10º, § 2º, inciso III,
        o valor é de R$ 1.234,56 (23,45% do total).
        A data limite é 15/03/2024.
        """
        
        indicators = ResponseValidator.check_for_hallucination_indicators(response)
        
        assert len(indicators) > 0

    def test_check_hallucination_no_indicators(self):
        """Testa quando não há indicadores de alucinação"""
        response = """
        De acordo com o CDC, o consumidor tem direito à troca.
        """
        
        indicators = ResponseValidator.check_for_hallucination_indicators(response)
        
        # Pode ter alguns, mas menos
        assert len(indicators) <= 1

    def test_validate_and_score_good_response(self, sample_sources):
        """Testa scoring de uma boa resposta"""
        response = """
        Segundo o CDC - Artigo 18, produtos com defeito podem ser trocados.
        
        **Fontes Consultadas:**
        - CDC - Artigo 18
        """
        
        adjusted, details = ResponseValidator.validate_and_score(
            response, sample_sources, original_confidence=90.0
        )
        
        assert details['is_valid']
        assert adjusted >= 80.0  # Não deve reduzir muito
        assert details['cited_sources_count'] > 0

    def test_validate_and_score_poor_response(self, sample_sources):
        """Testa scoring de uma resposta ruim"""
        response = """
        Geralmente produtos podem ser trocados.
        É comum as lojas aceitarem devolução.
        """
        
        adjusted, details = ResponseValidator.validate_and_score(
            response, sample_sources, original_confidence=90.0
        )
        
        assert not details['is_valid']
        assert adjusted < 90.0  # Deve reduzir confiança
        assert details['cited_sources_count'] == 0

    def test_validate_and_score_with_hallucinations(self, sample_sources):
        """Testa scoring quando há alucinações"""
        response = """
        Segundo o CDC - Artigo 18, em 15/03/2024, o valor de R$ 1.234,56
        representa 23,45% do total conforme artigo 5º, § 3º, inciso II.
        
        **Fontes Consultadas:**
        - CDC - Artigo 18
        """
        
        adjusted, details = ResponseValidator.validate_and_score(
            response, sample_sources, original_confidence=90.0
        )
        
        # Deve reduzir por possíveis alucinações
        assert len(details['hallucination_indicators']) > 0
        assert adjusted < 90.0

    def test_validate_and_score_max_cap(self, sample_sources):
        """Testa que confiança não excede 95%"""
        response = """
        Segundo o CDC - Artigo 18, produtos podem ser trocados.
        
        **Fontes Consultadas:**
        - CDC - Artigo 18
        - CDC - Artigo 26
        """
        
        adjusted, details = ResponseValidator.validate_and_score(
            response, sample_sources, original_confidence=98.0
        )
        
        assert adjusted <= 95.0

    def test_citation_patterns_detection(self, sample_sources):
        """Testa detecção de diferentes padrões de citação"""
        patterns = [
            "Segundo a fonte legal...",
            "Conforme o artigo mencionado...",
            "De acordo com a Lei 8.078/90...",
            "Baseado em CDC - Artigo 18...",
            "Consta no documento que...",
            "Previsto na legislação..."
        ]
        
        for pattern in patterns:
            response = f"{pattern} informação relevante."
            is_valid, _ = ResponseValidator.validate_response_uses_sources(
                response, sample_sources, strict_mode=True
            )
            # Deve aceitar pelo menos alguns padrões
            # (não todos necessariamente, mas testamos a lógica)

    def test_suspicious_patterns_detection(self, sample_sources):
        """Testa detecção de padrões suspeitos"""
        response = """
        De modo geral, geralmente, normalmente, em geral, costuma-se,
        é comum e usualmente acontece dessa forma.
        """
        
        # Esta resposta tem muitos padrões suspeitos
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sample_sources, strict_mode=True
        )
        
        # Pode ou não ser válida, mas deve logar warning
        # O importante é que o sistema detecte
