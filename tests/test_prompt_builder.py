"""
Testes para o sistema de prompts dinâmicos
"""
import pytest
from app.services.prompt_builder import PromptBuilder, ComplexityLevel


class TestPromptBuilder:
    """Testes para a classe PromptBuilder"""

    @pytest.fixture
    def prompt_builder(self):
        """Fixture para criar instância do PromptBuilder"""
        return PromptBuilder()

    def test_build_system_prompt_simple(self, prompt_builder):
        """Testa geração de prompt simples"""
        prompt = prompt_builder.build_system_prompt(ComplexityLevel.SIMPLE)
        
        assert "Extremamente Simples" in prompt
        assert "vocabulário do dia a dia" in prompt
        assert "assistente jurídico" in prompt.lower()

    def test_build_system_prompt_intermediate(self, prompt_builder):
        """Testa geração de prompt intermediário"""
        prompt = prompt_builder.build_system_prompt(ComplexityLevel.INTERMEDIATE)
        
        assert "Intermediário" in prompt
        assert "termos jurídicos básicos" in prompt
        assert "assistente jurídico" in prompt.lower()

    def test_build_system_prompt_detailed(self, prompt_builder):
        """Testa geração de prompt detalhado"""
        prompt = prompt_builder.build_system_prompt(ComplexityLevel.DETAILED)
        
        assert "Detalhado" in prompt
        assert "artigos de lei" in prompt
        assert "assistente jurídico" in prompt.lower()

    def test_build_system_prompt_technical(self, prompt_builder):
        """Testa geração de prompt técnico"""
        prompt = prompt_builder.build_system_prompt(ComplexityLevel.TECHNICAL)
        
        assert "Técnico-Jurídico" in prompt
        assert "terminologia jurídica" in prompt
        assert "jurisprudências" in prompt

    def test_all_complexity_levels_have_guidelines(self, prompt_builder):
        """Testa se todos os níveis incluem diretrizes gerais"""
        for complexity in ComplexityLevel:
            prompt = prompt_builder.build_system_prompt(complexity)
            
            assert "DIRETRIZES GERAIS OBRIGATÓRIAS" in prompt
            assert "APENAS use informações das FONTES fornecidas" in prompt
            assert "ESTRUTURA OBRIGATÓRIA DA RESPOSTA" in prompt

    def test_build_user_prompt_basic(self, prompt_builder):
        """Testa geração de prompt do usuário básico"""
        question = "Quais são meus direitos?"
        context = "Contexto jurídico..."
        
        prompt = prompt_builder.build_user_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "PERGUNTA DO USUÁRIO" in prompt
        assert "FONTES JURÍDICAS" in prompt

    def test_build_user_prompt_with_user_context(self, prompt_builder):
        """Testa prompt com contexto adicional do usuário"""
        question = "Teste"
        context = "Contexto"
        user_context = "Contexto adicional do usuário"
        
        prompt = prompt_builder.build_user_prompt(question, context, user_context)
        
        assert user_context in prompt
        assert "CONTEXTO DO USUÁRIO" in prompt

    def test_build_user_prompt_without_user_context(self, prompt_builder):
        """Testa prompt sem contexto adicional"""
        question = "Teste"
        context = "Contexto"
        
        prompt = prompt_builder.build_user_prompt(question, context)
        
        assert "CONTEXTO DO USUÁRIO" not in prompt

    def test_build_user_prompt_with_additional_instructions(self, prompt_builder):
        """Testa prompt com instruções adicionais"""
        question = "Teste"
        context = "Contexto"
        instructions = "Seja breve e direto"
        
        prompt = prompt_builder.build_user_prompt(
            question, context, additional_instructions=instructions
        )
        
        assert instructions in prompt
        assert "INSTRUÇÕES ADICIONAIS" in prompt

    def test_get_disclaimer_geral(self, prompt_builder):
        """Testa disclaimer geral"""
        disclaimer = prompt_builder.get_disclaimer("geral")
        
        assert "IMPORTANTE" in disclaimer
        assert "orientativo" in disclaimer
        assert "advogado" in disclaimer.lower()

    def test_get_disclaimer_trabalhista(self, prompt_builder):
        """Testa disclaimer trabalhista"""
        disclaimer = prompt_builder.get_disclaimer("trabalhista")
        
        assert "trabalhista" in disclaimer.lower()
        assert "convenção coletiva" in disclaimer.lower()

    def test_get_disclaimer_consumidor(self, prompt_builder):
        """Testa disclaimer de direito do consumidor"""
        disclaimer = prompt_builder.get_disclaimer("consumidor")
        
        assert "consumidor" in disclaimer.lower()
        assert "Procon" in disclaimer

    def test_get_disclaimer_familia(self, prompt_builder):
        """Testa disclaimer de direito de família"""
        disclaimer = prompt_builder.get_disclaimer("familia")
        
        assert "família" in disclaimer.lower()
        assert "aspectos pessoais" in disclaimer.lower()

    def test_get_disclaimer_previdenciario(self, prompt_builder):
        """Testa disclaimer previdenciário"""
        disclaimer = prompt_builder.get_disclaimer("previdenciario")
        
        assert "previdenciár" in disclaimer.lower()
        assert "contributivo" in disclaimer.lower()

    def test_get_disclaimer_unknown_type(self, prompt_builder):
        """Testa que tipo desconhecido retorna disclaimer geral"""
        disclaimer = prompt_builder.get_disclaimer("tipo_inexistente")
        disclaimer_geral = prompt_builder.get_disclaimer("geral")
        
        assert disclaimer == disclaimer_geral

    def test_all_disclaimers_have_warning(self, prompt_builder):
        """Testa se todos os disclaimers têm aviso"""
        types = ["geral", "trabalhista", "consumidor", "familia", "previdenciario"]
        
        for dtype in types:
            disclaimer = prompt_builder.get_disclaimer(dtype)
            assert "⚠️" in disclaimer or "IMPORTANTE" in disclaimer
