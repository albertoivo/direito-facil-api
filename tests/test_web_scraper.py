"""
Testes para o serviço de Web Scraping
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
from app.services.web_scraper import WebScraperService


@pytest.fixture
def scraper():
    """Fixture para instanciar o WebScraperService"""
    return WebScraperService()


@pytest.mark.asyncio
class TestWebScraperService:
    """Testes para o WebScraperService"""

    async def test_extract_content_success(self, scraper):
        """Testa extração bem-sucedida de conteúdo de uma URL"""
        html_content = """
        <html>
            <head><title>Test Document</title></head>
            <body>
                <h1>Lei 8.078/90</h1>
                <p>Código de Defesa do Consumidor</p>
                <p>Art. 1º - Este código estabelece normas de proteção...</p>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            content = await scraper.extract_content("http://example.com/lei")
            
            assert "Lei 8.078/90" in content
            assert "Código de Defesa do Consumidor" in content
            assert "Art. 1º" in content
            assert "console.log" not in content  # Scripts devem ser removidos

    async def test_extract_content_http_error(self, scraper):
        """Testa tratamento de erro HTTP (404, 500, etc.)"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=mock_response
                )
            )
            
            with pytest.raises(ValueError) as exc_info:
                await scraper.extract_content("http://example.com/notfound")
            
            assert "Erro HTTP 404" in str(exc_info.value)

    async def test_extract_content_timeout(self, scraper):
        """Testa tratamento de timeout"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            with pytest.raises(ValueError) as exc_info:
                await scraper.extract_content("http://example.com/slow")
            
            assert "Timeout" in str(exc_info.value)

    async def test_extract_content_network_error(self, scraper):
        """Testa tratamento de erro de rede"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            
            with pytest.raises(ValueError) as exc_info:
                await scraper.extract_content("http://example.com/error")
            
            assert "Erro de rede" in str(exc_info.value)

    async def test_extract_content_insufficient_content(self, scraper):
        """Testa tratamento de conteúdo insuficiente"""
        html_content = """
        <html>
            <body>
                <p>Short</p>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError) as exc_info:
                await scraper.extract_content("http://example.com/short")
            
            assert "Conteúdo insuficiente" in str(exc_info.value)

    async def test_extract_content_removes_unwanted_elements(self, scraper):
        """Testa remoção de elementos indesejados (scripts, styles, nav, etc.)"""
        html_content = """
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <nav>Menu de navegação</nav>
                <header>Cabeçalho</header>
                <main>
                    <h1>Conteúdo Principal</h1>
                    <p>Este é o conteúdo útil que deve ser extraído.</p>
                    <p>Mais informações importantes sobre a legislação.</p>
                </main>
                <footer>Rodapé</footer>
                <script>alert('test');</script>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            content = await scraper.extract_content("http://example.com/page")
            
            # Verifica que conteúdo útil foi mantido
            assert "Conteúdo Principal" in content
            assert "conteúdo útil" in content
            
            # Verifica que elementos indesejados foram removidos
            assert "Menu de navegação" not in content
            assert "Cabeçalho" not in content
            assert "Rodapé" not in content
            assert "color: red" not in content
            assert "alert('test')" not in content

    def test_validate_url_valid_http(self, scraper):
        """Testa validação de URL HTTP válida"""
        assert scraper.validate_url("http://example.com") is True

    def test_validate_url_valid_https(self, scraper):
        """Testa validação de URL HTTPS válida"""
        assert scraper.validate_url("https://planalto.gov.br/lei") is True

    def test_validate_url_invalid_no_protocol(self, scraper):
        """Testa rejeição de URL sem protocolo"""
        assert scraper.validate_url("example.com") is False

    def test_validate_url_invalid_empty(self, scraper):
        """Testa rejeição de URL vazia"""
        assert scraper.validate_url("") is False
        assert scraper.validate_url(None) is False

    def test_validate_url_invalid_type(self, scraper):
        """Testa rejeição de tipo inválido"""
        assert scraper.validate_url(123) is False
        assert scraper.validate_url([]) is False

    async def test_extract_content_with_follow_redirects(self, scraper):
        """Testa que o scraper segue redirecionamentos"""
        html_content = """
        <html>
            <body>
                <h1>Conteúdo Final</h1>
                <p>Este é o conteúdo após redirecionamento.</p>
                <p>Este texto foi adicionado para garantir que o conteúdo tenha pelo menos 100 caracteres.</p>
                <p>Mais conteúdo para atender ao limite mínimo de caracteres.</p>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            # Verifica se follow_redirects=True foi passado
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.get = AsyncMock(return_value=mock_response)
            
            content = await scraper.extract_content("http://example.com/redirect")
            
            assert "Conteúdo Final" in content
            # Verifica que AsyncClient foi criado com follow_redirects=True
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args.kwargs
            assert call_kwargs.get('follow_redirects') is True
