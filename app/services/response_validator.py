"""
Validador de respostas para garantir que usam apenas as fontes fornecidas
"""
import logging
from typing import List, Dict, Tuple
import re

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Valida se a resposta do LLM está baseada nas fontes fornecidas"""
    
    @staticmethod
    def validate_response_uses_sources(
        response: str, 
        sources: List[Dict],
        strict_mode: bool = True
    ) -> Tuple[bool, str]:
        """
        Valida se a resposta menciona/usa as fontes fornecidas
        
        Args:
            response: Resposta gerada pelo LLM
            sources: Lista de documentos fonte
            strict_mode: Se True, exige que pelo menos uma fonte seja citada
            
        Returns:
            Tuple (is_valid, message)
        """
        if not response or not sources:
            return False, "Resposta ou fontes vazias"
        
        # Verificar se há menção a "não encontrei" ou similares
        no_info_patterns = [
            r'não encontrei',
            r'não há informações',
            r'não tenho informações',
            r'informações insuficientes',
            r'não constam? nas fontes',
            r'fontes não contêm',
        ]
        
        response_lower = response.lower()
        has_no_info_statement = any(
            re.search(pattern, response_lower) 
            for pattern in no_info_patterns
        )
        
        # Se o LLM admitiu não ter informação, é válido
        if has_no_info_statement:
            logger.info("Resposta válida: LLM admitiu falta de informação nas fontes")
            return True, "Resposta honesta sobre limitação das fontes"
        
        # Verificar se menciona alguma fonte
        sources_mentioned = 0
        source_titles = [s.get('title', '') for s in sources]
        
        for title in source_titles:
            if title and title.lower() in response_lower:
                sources_mentioned += 1
        
        # Verificar padrões de citação
        citation_patterns = [
            r'segundo\s+(?:a|o)\s+(?:fonte|documento|lei|artigo)',
            r'conforme\s+(?:a|o)',
            r'de acordo com\s+(?:a|o)',
            r'baseado em',
            r'consta (?:na|no)',
            r'previsto (?:na|no)',
            r'\*\*fontes consultadas:\*\*',
        ]
        
        has_citations = any(
            re.search(pattern, response_lower) 
            for pattern in citation_patterns
        )
        
        if strict_mode:
            if sources_mentioned == 0 and not has_citations:
                return False, "Resposta não menciona nenhuma fonte nem tem padrões de citação"
        
        # Verificar por padrões suspeitos (conhecimento geral)
        suspicious_patterns = [
            r'de modo geral',
            r'geralmente',
            r'normalmente',
            r'em geral',
            r'costuma-se',
            r'é comum',
            r'usualmente',
        ]
        
        suspicious_count = sum(
            1 for pattern in suspicious_patterns 
            if re.search(pattern, response_lower)
        )
        
        if suspicious_count > 2:
            logger.warning(f"Resposta suspeita: {suspicious_count} padrões de conhecimento geral detectados")
        
        # Validação final
        if has_citations or sources_mentioned > 0:
            confidence = "alta" if sources_mentioned > 1 else "média"
            return True, f"Resposta válida com confiança {confidence}"
        elif not strict_mode:
            return True, "Modo permissivo: resposta aceita"
        else:
            return False, "Resposta não demonstra uso claro das fontes"
    
    @staticmethod
    def extract_cited_sources(response: str) -> List[str]:
        """
        Extrai as fontes citadas na resposta
        
        Args:
            response: Resposta do LLM
            
        Returns:
            Lista de fontes mencionadas
        """
        cited = []
        
        # Procurar por seção "Fontes Consultadas"
        sources_section_match = re.search(
            r'\*\*fontes consultadas:?\*\*(.+?)(?:\n\n|\Z)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        
        if sources_section_match:
            sources_text = sources_section_match.group(1)
            # Extrair itens de lista
            cited = re.findall(r'[-*]\s*(.+?)(?:\n|$)', sources_text)
        
        return cited
    
    @staticmethod
    def check_for_hallucination_indicators(response: str) -> List[str]:
        """
        Verifica indicadores de possível alucinação (informação inventada)
        
        Args:
            response: Resposta do LLM
            
        Returns:
            Lista de indicadores encontrados
        """
        indicators = []
        
        # Padrões de alucinação
        hallucination_patterns = {
            'datas_especificas': r'\d{1,2}/\d{1,2}/\d{4}',  # Datas muito específicas
            'numeros_muito_precisos': r'\d+,\d{2}',  # Valores monetários muito precisos
            'percentuais_especificos': r'\d+[,.]\d+%',  # Percentuais muito específicos
            'artigos_especificos': r'art(?:igo)?\.?\s*\d+[º°]?,?\s*§\s*\d+[º°]?,?\s*inciso\s+[IVXLCDM]+',
        }
        
        response_lower = response.lower()
        
        for indicator_name, pattern in hallucination_patterns.items():
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                indicators.append(f"{indicator_name}: {len(matches)} ocorrências")
        
        # Avisos genéricos que podem indicar conhecimento geral
        generic_warnings = [
            'pode variar',
            'depende do caso',
            'consulte um advogado',
            'cada caso é único',
        ]
        
        generic_count = sum(
            1 for warning in generic_warnings 
            if warning in response_lower
        )
        
        if generic_count > 3:
            indicators.append(f"excesso_avisos_genericos: {generic_count}")
        
        return indicators
    
    @staticmethod
    def validate_and_score(
        response: str,
        sources: List[Dict],
        original_confidence: float
    ) -> Tuple[float, Dict]:
        """
        Valida a resposta e ajusta o score de confiança
        
        Args:
            response: Resposta gerada
            sources: Fontes fornecidas
            original_confidence: Score original de confiança
            
        Returns:
            Tuple (adjusted_confidence, validation_details)
        """
        is_valid, message = ResponseValidator.validate_response_uses_sources(
            response, sources, strict_mode=True
        )
        
        cited_sources = ResponseValidator.extract_cited_sources(response)
        hallucination_indicators = ResponseValidator.check_for_hallucination_indicators(response)
        
        # Ajustar confiança baseado na validação
        adjusted_confidence = original_confidence
        
        if not is_valid:
            adjusted_confidence *= 0.5  # Reduz 50% se não usar fontes
            logger.warning(f"Confiança reduzida: {message}")
        
        if len(cited_sources) == 0:
            adjusted_confidence *= 0.8  # Reduz 20% se não citar fontes explicitamente
        
        if len(hallucination_indicators) > 0:
            adjusted_confidence *= 0.9  # Reduz 10% por possíveis alucinações
            logger.warning(f"Indicadores de alucinação: {hallucination_indicators}")
        
        validation_details = {
            'is_valid': is_valid,
            'validation_message': message,
            'cited_sources_count': len(cited_sources),
            'cited_sources': cited_sources,
            'hallucination_indicators': hallucination_indicators,
            'original_confidence': original_confidence,
            'adjusted_confidence': min(adjusted_confidence, 95.0),  # Max 95%
        }
        
        return min(adjusted_confidence, 95.0), validation_details
