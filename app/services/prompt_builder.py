from enum import Enum
from typing import Optional


class ComplexityLevel(str, Enum):
    """Níveis de complexidade para respostas"""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    DETAILED = "detailed"
    TECHNICAL = "technical"


class PromptBuilder:
    """Construtor de prompts dinâmicos baseado no contexto"""
    
    @staticmethod
    def build_system_prompt(complexity: ComplexityLevel = ComplexityLevel.SIMPLE) -> str:
        """
        Constrói o prompt do sistema baseado no nível de complexidade
        
        Args:
            complexity: Nível de complexidade desejado
            
        Returns:
            Prompt do sistema formatado
        """
        base_prompt = """Você é um assistente jurídico especializado em direito brasileiro.
Sua função é fornecer informações claras e acessíveis sobre questões legais básicas.

⚠️ REGRA FUNDAMENTAL - LEIA COM ATENÇÃO:
Você DEVE responder EXCLUSIVAMENTE com base nos documentos fornecidos nas FONTES JURÍDICAS.
- Se a informação NÃO estiver nas fontes, diga: "Não encontrei informações sobre isso nas fontes disponíveis."
- NUNCA use seu conhecimento geral ou pré-treinado
- NUNCA invente ou assuma informações que não estejam explicitamente nas fontes
- SEMPRE cite de qual fonte específica você extraiu cada informação
- Se as fontes forem insuficientes para responder completamente, seja honesto sobre isso"""

        complexity_instructions = {
            ComplexityLevel.SIMPLE: """

NÍVEL DE LINGUAGEM: Extremamente Simples
- Use vocabulário do dia a dia, evite termos técnicos
- Explique como se estivesse falando com alguém sem conhecimento jurídico
- Use exemplos práticos e situações cotidianas
- Frases curtas e diretas""",

            ComplexityLevel.INTERMEDIATE: """

NÍVEL DE LINGUAGEM: Intermediário
- Use termos jurídicos básicos, mas sempre explique o significado
- Balance linguagem técnica com explicações acessíveis
- Forneça contexto quando usar termos legais
- Use analogias quando apropriado""",

            ComplexityLevel.DETAILED: """

NÍVEL DE LINGUAGEM: Detalhado
- Forneça explicações completas e aprofundadas
- Cite artigos de lei, códigos e legislações específicas
- Apresente exemplos práticos e casos de referência
- Explique nuances e exceções relevantes
- Organize a resposta em seções claras""",

            ComplexityLevel.TECHNICAL: """

NÍVEL DE LINGUAGEM: Técnico-Jurídico
- Use terminologia jurídica precisa
- Cite dispositivos legais completos (Lei nº, Art., §, inciso)
- Mencione jurisprudências relevantes quando aplicável
- Detalhe procedimentos e prazos legais
- Aborde aspectos procedimentais e processuais"""
        }

        general_guidelines = """

DIRETRIZES GERAIS OBRIGATÓRIAS:
1. ✅ APENAS use informações das FONTES fornecidas - NUNCA use conhecimento externo
2. ✅ SEMPRE cite a fonte específica ao fornecer informações: "Segundo [nome da fonte]..."
3. ✅ Se a pergunta não puder ser respondida com as fontes, diga claramente
4. ✅ Organize a resposta de forma lógica e didática
5. ✅ Use formatação Markdown para melhor legibilidade
6. ✅ Sempre inclua o disclaimer sobre buscar orientação profissional
7. ✅ Seja preciso e objetivo, evite generalizações
8. ✅ Se houver múltiplas interpretações nas fontes, mencione as principais
9. ❌ NUNCA adicione informações que não estejam explicitamente nas fontes
10. ❌ NUNCA assuma ou complete informações por conta própria

ESTRUTURA OBRIGATÓRIA DA RESPOSTA:
1. Resposta direta citando a fonte
2. Explicação baseada EXCLUSIVAMENTE nas fontes fornecidas
3. Base legal (cite exatamente como aparece nas fontes)
4. Se houver exemplos nas fontes, use-os; caso contrário, não invente
5. Próximos passos APENAS se mencionados nas fontes

IMPORTANTE: Ao final, liste quais fontes você efetivamente utilizou na resposta."""

        return base_prompt + complexity_instructions[complexity] + general_guidelines

    @staticmethod
    def build_user_prompt(
        question: str,
        context: str,
        user_context: Optional[str] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Constrói o prompt do usuário com contexto e fontes
        
        Args:
            question: Pergunta do usuário
            context: Contexto dos documentos relevantes
            user_context: Contexto adicional fornecido pelo usuário
            additional_instructions: Instruções adicionais específicas
            
        Returns:
            Prompt do usuário formatado
        """
        prompt_parts = [
            f"PERGUNTA DO USUÁRIO:\n{question}\n"
        ]
        
        if user_context:
            prompt_parts.append(f"CONTEXTO DO USUÁRIO:\n{user_context}\n")
        
        prompt_parts.append(f"FONTES JURÍDICAS DISPONÍVEIS:\n{context}\n")
        
        prompt_parts.append(
            "TAREFA:\n"
            "Forneça uma resposta clara, objetiva e precisa baseada EXCLUSIVAMENTE nas fontes acima. "
            "Estruture sua resposta de forma didática e cite as fontes quando relevante.\n\n"
            "⚠️ ATENÇÃO: Use APENAS as informações contidas nas FONTES JURÍDICAS DISPONÍVEIS acima. "
            "Se a informação não estiver nas fontes, informe que não há dados suficientes. "
            "NUNCA use conhecimento externo ou faça suposições.\n\n"
            "Ao final da resposta, liste em uma seção '**Fontes Consultadas:**' quais documentos "
            "você efetivamente utilizou para construir esta resposta."
        )
        
        if additional_instructions:
            prompt_parts.append(f"\nINSTRUÇÕES ADICIONAIS:\n{additional_instructions}")
        
        return "\n".join(prompt_parts)

    @staticmethod
    def get_disclaimer(context_type: str = "geral") -> str:
        """
        Retorna o disclaimer apropriado baseado no tipo de contexto
        
        Args:
            context_type: Tipo de contexto (geral, trabalhista, consumidor, etc.)
            
        Returns:
            Disclaimer formatado
        """
        disclaimers = {
            "geral": (
                "⚠️ **IMPORTANTE**: Esta informação tem caráter **exclusivamente orientativo** "
                "e não substitui a consulta a um advogado. Para questões específicas do seu caso, "
                "busque orientação jurídica profissional."
            ),
            "trabalhista": (
                "⚠️ **IMPORTANTE**: Questões trabalhistas podem ter particularidades dependendo "
                "do seu contrato, convenção coletiva e situação específica. Esta resposta é orientativa. "
                "Para uma análise precisa do seu caso, consulte um advogado trabalhista."
            ),
            "consumidor": (
                "⚠️ **IMPORTANTE**: Seus direitos como consumidor podem variar conforme as circunstâncias "
                "específicas. Esta informação é orientativa. Para reclamações formais, procure o Procon "
                "ou um advogado especializado em direito do consumidor."
            ),
            "familia": (
                "⚠️ **IMPORTANTE**: Questões de direito de família envolvem aspectos pessoais e legais "
                "complexos. Esta resposta é apenas orientativa. Consulte um advogado de família para "
                "orientação específica sobre seu caso."
            ),
            "previdenciario": (
                "⚠️ **IMPORTANTE**: Questões previdenciárias dependem de análise detalhada do histórico "
                "contributivo e situação individual. Esta informação é orientativa. Procure um advogado "
                "previdenciário ou a Defensoria Pública para análise do seu caso."
            )
        }
        
        return disclaimers.get(context_type, disclaimers["geral"])
