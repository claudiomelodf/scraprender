# Extrator de Informações de Produtos - Documentação

## Visão Geral

Este sistema foi desenvolvido para resolver o problema de integração entre assistentes virtuais e links de produtos. Ele permite extrair informações detalhadas de produtos a partir de URLs, possibilitando que seu assistente virtual forneça respostas precisas sobre preços, disponibilidade e especificações de produtos.

## Componentes do Sistema

O sistema é composto por três módulos principais:

1. **produto_scraper.py**: Biblioteca principal que extrai informações de produtos a partir de URLs.
2. **webhook_handler.py**: Servidor web que fornece endpoints para integração com sistemas de mensagens.
3. **teste_scraper.py**: Ferramenta para testar a extração de informações de produtos.

## Requisitos

- Python 3.6 ou superior
- Bibliotecas: requests, beautifulsoup4, lxml, flask

## Instalação

1. Clone ou baixe os arquivos para um diretório em seu servidor
2. Instale as dependências:

```bash
pip install requests beautifulsoup4 lxml flask
```

3. Torne os scripts executáveis (em sistemas Linux/Unix):

```bash
chmod +x produto_scraper.py webhook_handler.py teste_scraper.py
```

## Como Usar

### Extração Direta de Informações (produto_scraper.py)

Este módulo pode ser usado diretamente em seu código Python:

```python
from produto_scraper import ProdutoScraper

# Criar uma instância do scraper
scraper = ProdutoScraper()

# Extrair informações de um produto
url = "https://www.ciainfor.com.br/seu-produto"
info_produto = scraper.extrair_info_ciainfor(url)

# Formatar as informações em uma resposta amigável
resposta = scraper.formatar_resposta(info_produto)
print(resposta)
```

### Servidor Webhook (webhook_handler.py)

Este módulo fornece um servidor web que pode receber mensagens de clientes e responder com informações de produtos:

1. Inicie o servidor:

```bash
python webhook_handler.py
```

2. O servidor estará disponível em `http://seu-servidor:5000` com os seguintes endpoints:

   - `/webhook` (POST): Recebe mensagens e extrai informações de produtos
   - `/produto` (GET): Consulta informações de um produto diretamente pela URL
   - `/health` (GET): Verifica se o serviço está funcionando

3. Para integrar com seu sistema de mensagens, configure-o para enviar mensagens para o endpoint `/webhook` com o seguinte formato:

```json
{
  "message": "Olá, tudo bem? Preciso de ajuda com o produto https://www.ciainfor.com.br/seu-produto"
}
```

### Ferramenta de Teste (teste_scraper.py)

Esta ferramenta permite testar a extração de informações de produtos:

```bash
# Testar com uma URL específica
python teste_scraper.py "https://www.ciainfor.com.br/seu-produto"

# Testar com exemplos pré-definidos
python teste_scraper.py
```

## Integração com Assistentes Virtuais

### Opção 1: Integração via Webhook

1. Configure seu assistente virtual para enviar mensagens para o endpoint `/webhook`
2. O sistema irá processar a mensagem, extrair informações do produto e retornar uma resposta formatada
3. Seu assistente virtual pode então usar essa resposta para responder ao cliente

### Opção 2: Integração Direta via API

1. Importe o módulo `produto_scraper.py` em seu código
2. Use a classe `ProdutoScraper` para extrair informações de produtos
3. Use o método `formatar_resposta()` para formatar as informações em uma resposta amigável

### Opção 3: Integração via Consulta HTTP

1. Configure seu assistente virtual para fazer requisições HTTP para o endpoint `/produto`
2. Passe a URL do produto como parâmetro: `/produto?url=https://www.ciainfor.com.br/seu-produto`
3. O sistema irá retornar as informações do produto em formato JSON

## Personalização

### Adicionando Suporte a Outros Sites

Para adicionar suporte a outros sites de e-commerce, você pode estender a classe `ProdutoScraper` e implementar métodos específicos para cada site:

```python
def extrair_info_outro_site(self, url):
    # Implementação específica para outro site
    # ...
    return resultado
```

Em seguida, atualize o método `processar_mensagem()` para usar o novo método:

```python
if "ciainfor.com.br" in url:
    return self.extrair_info_ciainfor(url)
elif "outro-site.com.br" in url:
    return self.extrair_info_outro_site(url)
```

### Personalizando a Resposta

Você pode personalizar o formato da resposta modificando o método `formatar_resposta()` na classe `ProdutoScraper`.

## Solução de Problemas

### Erro 404 ao acessar URL

Verifique se a URL do produto está correta e acessível. Alguns sites podem bloquear requisições automatizadas.

### Informações Incorretas ou Incompletas

O sistema usa técnicas de web scraping para extrair informações, o que pode ser afetado por mudanças na estrutura do site. Se as informações estiverem incorretas ou incompletas, pode ser necessário atualizar os seletores CSS no método `extrair_info_ciainfor()`.

### Problemas de Desempenho

Se o sistema estiver lento, considere implementar cache para evitar requisições repetidas ao mesmo produto em um curto período de tempo.

## Limitações

- O sistema atualmente suporta apenas o site ciainfor.com.br
- A extração de informações depende da estrutura do site, que pode mudar ao longo do tempo
- Alguns sites podem bloquear requisições automatizadas

## Próximos Passos

- Implementar cache para melhorar o desempenho
- Adicionar suporte a mais sites de e-commerce
- Implementar autenticação para proteger os endpoints
- Adicionar suporte a mais idiomas
