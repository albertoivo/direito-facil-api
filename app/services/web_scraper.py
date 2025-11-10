import httpx
from bs4 import BeautifulSoup
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebScraperService:
    """Serviço para extrair conteúdo de URLs de documentos legais"""
    
    def __init__(self, timeout: float = 120.0):
        """
        Inicializa o serviço de web scraping
        
        Args:
            timeout: Tempo limite para requisições HTTP em segundos (padrão: 120s)
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def extract_content(self, url: str) -> str:
        """
        Extrai o conteúdo textual de uma URL
        
        Args:
            url: URL do documento legal
            
        Returns:
            Texto extraído da página
            
        Raises:
            ValueError: Se não conseguir acessar a URL ou extrair conteúdo
        """
        try:
            logger.info(f"Iniciando extração de conteúdo de: {url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                follow_redirects=True,
                headers=self.headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            logger.info(f"Resposta HTTP recebida: {response.status_code}")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove elementos que não contêm conteúdo útil
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                element.decompose()
            
            # Extrai texto
            text = soup.get_text(separator='\n', strip=True)
            
            # Limpa linhas vazias e espaços extras
            lines = []
            for line in text.split('\n'):
                cleaned_line = line.strip()
                if cleaned_line:
                    lines.append(cleaned_line)
            
            content = '\n'.join(lines)
            
            if not content or len(content) < 100:
                raise ValueError(f"Conteúdo insuficiente extraído da URL (apenas {len(content)} caracteres)")
            
            logger.info(f"Conteúdo extraído com sucesso: {len(content)} caracteres, {len(lines)} linhas")
            return content
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Erro HTTP {e.response.status_code} ao acessar {url}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except httpx.TimeoutException:
            error_msg = f"Timeout ao acessar {url} (limite: {self.timeout}s)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Erro de rede ao acessar {url}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Erro ao processar o conteúdo de {url}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def validate_url(self, url: str) -> bool:
        """
        Valida se uma URL é válida e segura
        
        Args:
            url: URL a ser validada
            
        Returns:
            True se a URL é válida, False caso contrário
        """
        if not url or not isinstance(url, str):
            return False
        
        # Verifica se começa com http:// ou https://
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Lista de domínios confiáveis (pode ser expandida)
        trusted_domains = [
            'planalto.gov.br',
            'in.gov.br',
            'senado.leg.br',
            'camara.leg.br',
            'stf.jus.br',
            'stj.jus.br',
            'tst.jus.br',
        ]
        
        # Verifica se é de um domínio confiável (opcional)
        # Comentado para permitir qualquer domínio HTTP/HTTPS válido
        # for domain in trusted_domains:
        #     if domain in url:
        #         return True
        
        return True
