#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import logging
import os
from produto_scraper import ProdutoScraper

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
scraper = ProdutoScraper()

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint para receber mensagens de webhook e processar informações de produtos
    """
    try:
        data = request.json
        logger.info(f"Webhook recebido: {data}")
        
        # Extrair a mensagem do webhook (ajuste conforme a estrutura do seu webhook)
        if 'message' in data:
            mensagem = data['message']
        elif 'text' in data:
            mensagem = data['text']
        else:
            return jsonify({"status": "erro", "mensagem": "Formato de mensagem não reconhecido"}), 400
        
        # Processar a mensagem para extrair informações do produto
        resultado = scraper.processar_mensagem(mensagem)
        
        # Formatar a resposta
        resposta = scraper.formatar_resposta(resultado)
        
        # Retornar a resposta formatada
        return jsonify({
            "status": "sucesso",
            "resposta": resposta,
            "dados_produto": resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/produto', methods=['GET'])
def produto():
    """
    Endpoint para consultar informações de um produto diretamente pela URL
    """
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({"status": "erro", "mensagem": "Parâmetro 'url' é obrigatório"}), 400
        
        # Extrair informações do produto
        if "ciainfor.com.br" in url:
            resultado = scraper.extrair_info_ciainfor(url)
        else:
            return jsonify({"status": "erro", "mensagem": "Domínio não suportado"}), 400
        
        # Formatar a resposta
        resposta = scraper.formatar_resposta(resultado)
        
        # Retornar a resposta formatada
        return jsonify({
            "status": "sucesso",
            "resposta": resposta,
            "dados_produto": resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta de produto: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint para verificar se o serviço está funcionando
    """
    return jsonify({"status": "online"})

if __name__ == "__main__":
    # Obter porta do ambiente ou usar 5000 como padrão
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar o servidor Flask
    app.run(host="0.0.0.0", port=port, debug=False)
