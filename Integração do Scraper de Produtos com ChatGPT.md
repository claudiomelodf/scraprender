# Integração do Scraper de Produtos com ChatGPT

Este documento explica como integrar o extrator de informações de produtos com o ChatGPT através do Whaticket, permitindo que seu assistente virtual forneça informações detalhadas sobre produtos quando os clientes enviarem links.

## Visão Geral da Solução

A solução implementada permite que:

1. O Whaticket receba mensagens de clientes contendo links de produtos
2. O sistema extraia automaticamente informações detalhadas desses produtos
3. As informações sejam formatadas de maneira otimizada para o ChatGPT
4. O ChatGPT utilize essas informações para responder ao cliente de forma natural e informativa

## Componentes da Solução

1. **Extrator de Produtos (`produto_scraper.py`)**: Biblioteca que analisa páginas de produtos e extrai dados estruturados
2. **Servidor Webhook (`webhook_handler_chatgpt.py`)**: API que processa mensagens e formata dados para o ChatGPT
3. **Banco de Dados SQLite**: Armazena informações de produtos para respostas mais rápidas e funcionamento offline

## Novos Endpoints Implementados

### 1. `/chatgpt_produto`

Endpoint específico para obter informações de produtos formatadas para o ChatGPT.

**URL**: `https://scraprender.onrender.com/chatgpt_produto?url=URL_DO_PRODUTO`

**Método**: GET

**Parâmetros**:
- `url`: URL completa do produto (obrigatório)
- `force`: `true` para forçar nova extração (opcional, padrão: `false`)

**Resposta**:
```json
{
  "status": "sucesso",
  "nome": "Nome do produto",
  "preco": "Preço do produto",
  "disponibilidade": "Status de disponibilidade",
  "codigo": "Código do produto",
  "descricao_resumida": "Resumo da descrição do produto",
  "especificacoes_filtradas": ["Especificação 1", "Especificação 2", ...],
  "url": "URL do produto",
  "chatgpt_texto": "Texto formatado pronto para uso pelo ChatGPT"
}
```

### 2. `/webhook` (com parâmetro `formato=chatgpt`)

Endpoint para processar mensagens do Whaticket e extrair informações de produtos.

**URL**: `https://scraprender.onrender.com/webhook?formato=chatgpt`

**Método**: POST

**Corpo da Requisição**:
```json
{
  "message": "Mensagem do cliente contendo link de produto"
}
```

**Resposta**: Mesmo formato do endpoint `/chatgpt_produto`

## Configuração no Whaticket

Para integrar com o Whaticket, configure um HTTP Request com as seguintes configurações:

1. **URL**: `https://scraprender.onrender.com/webhook?formato=chatgpt`
2. **Método**: POST
3. **Headers**: `Content-Type: application/json`
4. **Body**:
```json
{
  "message": "{{message}}"
}
```

## Configuração no ChatGPT

Para que o ChatGPT utilize as informações extraídas, adicione estas instruções ao seu prompt:

```
Quando receber informações de um produto no formato abaixo, utilize-as para responder ao cliente de forma natural e informativa:

Informações do Produto:
Nome: [Nome do produto]
Preço: [Preço]
Disponibilidade: [Disponibilidade]
Código: [Código]

Descrição Resumida:
[Descrição resumida]

Especificações Principais:
• [Especificação 1]
• [Especificação 2]
...

Link do Produto: [URL]

Ao responder:
1. Não mencione que está lendo dados formatados
2. Responda como se tivesse conhecimento natural sobre o produto
3. Destaque as características mais relevantes
4. Ofereça-se para fornecer mais detalhes se o cliente desejar
```

## Melhorias Implementadas

1. **Formatação Otimizada para ChatGPT**: Extração apenas das informações mais relevantes
2. **Remoção de Informações Repetidas**: Filtragem de contatos telefônicos duplicados
3. **Inclusão do Código do Produto**: Garantia de que o código do produto seja sempre incluído
4. **Resumo da Descrição**: Limitação da descrição para facilitar a leitura
5. **Especificações Principais**: Seleção das 5 especificações mais relevantes

## Exemplo de Uso

1. Cliente envia: "Preciso de ajuda com o produto https://www.ciainfor.com.br/cabo-vga-macho-x-vga-macho-15-metros-cfiltro"
2. Whaticket encaminha a mensagem para o webhook
3. Webhook extrai informações do produto e retorna dados formatados
4. ChatGPT recebe os dados formatados e responde ao cliente

## Solução de Problemas

### Produto não encontrado

Se o produto não for encontrado ou a URL for inválida, o sistema retornará uma mensagem de erro que o ChatGPT pode usar para informar ao cliente que não foi possível obter informações sobre o produto.

### Informações incompletas

Se algumas informações do produto estiverem faltando (como código ou especificações), o sistema preencherá com "Não informado" para garantir uma resposta consistente.

### Problemas de conexão

O sistema utiliza um banco de dados SQLite para armazenar informações de produtos previamente consultados, permitindo respostas mesmo quando o site original estiver indisponível.

## Próximos Passos

1. **Adicionar suporte a mais sites**: Expandir o extrator para suportar outros sites de e-commerce
2. **Melhorar a extração de especificações**: Implementar algoritmos mais avançados para identificar especificações relevantes
3. **Adicionar histórico de preços**: Rastrear mudanças de preços ao longo do tempo
4. **Implementar autenticação**: Adicionar camada de segurança para proteger o webhook
