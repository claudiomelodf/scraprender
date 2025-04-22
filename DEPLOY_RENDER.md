# Instruções para Deploy no Render

Este documento contém instruções passo a passo para implantar o Extrator de Informações de Produtos no Render e integrá-lo com o Whaticket.

## Pré-requisitos

1. Uma conta no [Render](https://render.com/)
2. Uma conta no [GitHub](https://github.com/) ou outro serviço Git
3. Acesso ao seu sistema Whaticket

## Passo 1: Preparar o Repositório Git

1. Crie um novo repositório no GitHub (ou outro serviço Git)
2. Faça o upload dos arquivos deste projeto para o repositório:

```bash
# Após criar o repositório no GitHub
git remote add origin https://github.com/seu-usuario/seu-repositorio.git
git branch -M main
git commit -m "Versão inicial do Extrator de Informações de Produtos"
git push -u origin main
```

## Passo 2: Implantar no Render

### Opção 1: Deploy Automático com Blueprint (Recomendado)

1. Faça login no [Render](https://dashboard.render.com/)
2. Clique em "New" e selecione "Blueprint"
3. Conecte sua conta GitHub e selecione o repositório que você criou
4. O Render detectará automaticamente o arquivo `render.yaml` e configurará o serviço
5. Clique em "Apply" para iniciar o deploy

### Opção 2: Deploy Manual

1. Faça login no [Render](https://dashboard.render.com/)
2. Clique em "New" e selecione "Web Service"
3. Conecte sua conta GitHub e selecione o repositório que você criou
4. Configure o serviço:
   - **Nome**: produto-scraper (ou outro nome de sua escolha)
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webhook_handler:app`
5. Clique em "Create Web Service" para iniciar o deploy

## Passo 3: Configurar a Integração com o Whaticket

Após o deploy bem-sucedido, o Render fornecerá uma URL para seu serviço (por exemplo, `https://produto-scraper.onrender.com`).

### Configuração no Whaticket

1. Acesse o painel administrativo do seu Whaticket
2. Vá para a seção de configurações de integrações ou webhooks
3. Adicione um novo webhook com as seguintes configurações:
   - **URL do Webhook**: `https://produto-scraper.onrender.com/webhook`
   - **Método**: POST
   - **Eventos**: Mensagens recebidas (ou equivalente no seu sistema)
   - **Formato**: JSON

### Teste da Integração

1. Envie uma mensagem de teste para seu número do Whaticket com o formato:
   ```
   Olá, tudo bem? Preciso de ajuda com o produto https://www.ciainfor.com.br/seu-produto
   ```
2. Verifique se o webhook está recebendo a mensagem e respondendo corretamente
3. Verifique os logs no Render para identificar possíveis problemas

## Solução de Problemas

### Webhook não está recebendo mensagens

- Verifique se a URL do webhook está correta no Whaticket
- Verifique se o serviço está em execução no Render
- Verifique os logs no Render para identificar possíveis erros

### Erro 500 ao acessar o webhook

- Verifique os logs no Render para identificar o erro específico
- Verifique se todas as dependências estão instaladas corretamente
- Verifique se o formato da mensagem enviada pelo Whaticket é compatível com o esperado pelo webhook

### Informações de produtos não estão sendo extraídas corretamente

- Verifique se a URL do produto está correta e acessível
- Verifique se o site do produto não bloqueou requisições do Render
- Verifique se a estrutura do site mudou e precisa de atualizações no código

## Personalização para o Whaticket

Dependendo da estrutura exata das mensagens enviadas pelo Whaticket, pode ser necessário ajustar o código do webhook para processar corretamente as mensagens.

Abra o arquivo `webhook_handler.py` e localize a seção que extrai a mensagem do webhook:

```python
# Extrair a mensagem do webhook (ajuste conforme a estrutura do seu webhook)
if 'message' in data:
    mensagem = data['message']
elif 'text' in data:
    mensagem = data['text']
else:
    return jsonify({"status": "erro", "mensagem": "Formato de mensagem não reconhecido"}), 400
```

Ajuste esta seção conforme a estrutura específica das mensagens enviadas pelo seu sistema Whaticket.

## Monitoramento e Manutenção

- Verifique regularmente os logs no Render para identificar possíveis problemas
- Configure alertas no Render para ser notificado em caso de falhas
- Atualize o código conforme necessário para acompanhar mudanças nos sites de produtos

## Próximos Passos

- Adicione suporte a mais sites de e-commerce
- Implemente cache para melhorar o desempenho
- Adicione autenticação para proteger o webhook
- Configure um domínio personalizado para o serviço
