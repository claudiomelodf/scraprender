#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from flask import Flask, request, jsonify, Response
from produto_scraper import ProdutoScraper

app = Flask(__name__)
scraper = ProdutoScraper()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se o serviço está online"""
    return jsonify({"status": "online"})

@app.route('/produto', methods=['GET'])
def get_produto():
    """Endpoint para extrair informações de um produto a partir da URL"""
    url = request.args.get('url')
    if not url:
        return jsonify({"status": "erro", "mensagem": "URL não fornecida"}), 400
    
    info_produto = scraper.extrair_info_ciainfor(url)
    resposta = scraper.formatar_resposta(info_produto)
    
    # Configurar a resposta JSON para não escapar caracteres Unicode
    return Response(
        json.dumps({
            "status": "sucesso",
            "resposta": resposta,
            "dados_produto": info_produto
        }, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/produto_tabular', methods=['GET'])
def get_produto_tabular():
    """Endpoint para extrair informações de um produto em formato tabular (tipo Excel)"""
    url = request.args.get('url')
    if not url:
        return jsonify({"status": "erro", "mensagem": "URL não fornecida"}), 400
    
    info_produto = scraper.extrair_info_ciainfor(url)
    
    # Organizar dados em formato tabular
    dados_tabulares = {
        "colunas": ["Nome", "Preço", "Disponibilidade", "Código", "URL"],
        "dados": [
            [
                info_produto.get("nome", ""),
                info_produto.get("preco", ""),
                info_produto.get("disponibilidade", ""),
                info_produto.get("codigo", ""),
                info_produto.get("url", "")
            ]
        ]
    }
    
    # Adicionar especificações como colunas adicionais, se existirem
    if "especificacoes" in info_produto and info_produto["especificacoes"]:
        dados_tabulares["especificacoes"] = {
            "colunas": ["Especificação", "Valor"],
            "dados": []
        }
        
        for spec in info_produto["especificacoes"]:
            if ":" in spec:
                chave, valor = spec.split(":", 1)
                dados_tabulares["especificacoes"]["dados"].append([chave.strip(), valor.strip()])
            else:
                dados_tabulares["especificacoes"]["dados"].append([spec, ""])
    
    # Configurar a resposta JSON para não escapar caracteres Unicode
    return Response(
        json.dumps({
            "status": "sucesso",
            "dados_tabulares": dados_tabulares,
            "dados_produto": info_produto
        }, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para processar webhooks do Whaticket"""
    try:
        data = request.json
        mensagem = data.get('message', '')
        
        resultado = scraper.processar_mensagem(mensagem)
        resposta = scraper.formatar_resposta(resultado)
        
        # Configurar a resposta JSON para não escapar caracteres Unicode
        return Response(
            json.dumps({
                "status": "sucesso",
                "resposta": resposta,
                "dados_produto": resultado
            }, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return Response(
            json.dumps({
                "status": "erro",
                "mensagem": f"Erro ao processar webhook: {str(e)}"
            }, ensure_ascii=False),
            status=500,
            mimetype='application/json'
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
