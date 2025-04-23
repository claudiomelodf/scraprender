#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
import datetime
from flask import Flask, request, jsonify, Response
from produto_scraper import ProdutoScraper

app = Flask(__name__)
scraper = ProdutoScraper()

# Configuração do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'produtos.db')

def init_db():
    """Inicializa o banco de dados se não existir"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        url TEXT PRIMARY KEY,
        nome TEXT,
        preco TEXT,
        disponibilidade TEXT,
        codigo TEXT,
        descricao TEXT,
        especificacoes TEXT,
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em {DB_PATH}")

def get_produto_from_db(url):
    """Busca um produto no banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        colunas = ['url', 'nome', 'preco', 'disponibilidade', 'codigo', 'descricao', 'especificacoes', 'data_atualizacao']
        produto = dict(zip(colunas, result))
        
        # Converter especificações de volta para lista
        if produto['especificacoes']:
            produto['especificacoes'] = json.loads(produto['especificacoes'])
        else:
            produto['especificacoes'] = []
            
        return produto
    return None

def save_produto_to_db(produto):
    """Salva ou atualiza um produto no banco de dados"""
    if not produto or 'url' not in produto:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Converter especificações para JSON
    especificacoes_json = json.dumps(produto.get('especificacoes', []), ensure_ascii=False)
    
    cursor.execute('''
    INSERT OR REPLACE INTO produtos 
    (url, nome, preco, disponibilidade, codigo, descricao, especificacoes, data_atualizacao) 
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        produto.get('url', ''),
        produto.get('nome', ''),
        produto.get('preco', ''),
        produto.get('disponibilidade', ''),
        produto.get('codigo', ''),
        produto.get('descricao', ''),
        especificacoes_json
    ))
    
    conn.commit()
    conn.close()
    return True

def formatar_para_chatgpt(info_produto):
    """
    Formata as informações do produto em um formato otimizado para o ChatGPT,
    garantindo que o código do produto seja incluído e removendo informações repetidas
    """
    if "erro" in info_produto:
        return {
            "status": "erro",
            "mensagem": info_produto.get("erro", "Erro ao processar produto"),
            "chatgpt_texto": f"Não foi possível obter informações sobre o produto. Erro: {info_produto.get('erro', 'Erro desconhecido')}"
        }
    
    # Filtrar especificações para remover informações de contato repetidas
    especificacoes_filtradas = []
    contatos_adicionados = set()
    
    for spec in info_produto.get('especificacoes', []):
        # Verificar se é informação de contato
        if any(palavra in spec.lower() for palavra in ['telefone', 'whatsapp', 'e-mail', 'tel']):
            # Extrair apenas o número/email
            if ':' in spec:
                tipo, valor = spec.split(':', 1)
                valor = valor.strip()
                if valor not in contatos_adicionados:
                    contatos_adicionados.add(valor)
                    especificacoes_filtradas.append(spec)
        else:
            # Não é contato, adicionar normalmente
            especificacoes_filtradas.append(spec)
    
    # Criar resumo da descrição (primeiros 200 caracteres)
    descricao_resumida = info_produto.get('descricao', '')[:200]
    if len(info_produto.get('descricao', '')) > 200:
        descricao_resumida += "..."
    
    # Garantir que o código do produto seja incluído
    codigo = info_produto.get('codigo', '')
    if not codigo or codigo.strip() == '':
        codigo = "Não informado"
    
    # Texto formatado para o ChatGPT
    chatgpt_texto = f"""
Informações do Produto:
Nome: {info_produto.get('nome', 'Não informado')}
Preço: {info_produto.get('preco', 'Não informado')}
Disponibilidade: {info_produto.get('disponibilidade', 'Não informado')}
Código: {codigo}

Descrição Resumida:
{descricao_resumida}

Especificações Principais:
{chr(10).join([f"• {spec}" for spec in especificacoes_filtradas[:5]])}

Link do Produto: {info_produto.get('url', '')}
    """.strip()
    
    return {
        "status": "sucesso",
        "nome": info_produto.get('nome', ''),
        "preco": info_produto.get('preco', ''),
        "disponibilidade": info_produto.get('disponibilidade', ''),
        "codigo": codigo,
        "descricao_resumida": descricao_resumida,
        "especificacoes_filtradas": especificacoes_filtradas[:5],
        "url": info_produto.get('url', ''),
        "chatgpt_texto": chatgpt_texto
    }

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
    
    # Verificar se deve forçar atualização
    force_update = request.args.get('force', 'false').lower() == 'true'
    
    # Verificar formato (completo ou chatgpt)
    formato = request.args.get('formato', 'completo').lower()
    
    # Verificar se o produto já está no banco de dados
    produto_db = None if force_update else get_produto_from_db(url)
    
    if produto_db and not force_update:
        # Produto encontrado no banco, retornar diretamente
        info_produto = produto_db
        fonte = "cache"
    else:
        # Produto não encontrado no banco ou forçando atualização, extrair informações
        info_produto = scraper.extrair_info_ciainfor(url)
        fonte = "web"
        
        # Salvar no banco de dados
        if "erro" not in info_produto:
            save_produto_to_db(info_produto)
    
    # Formatar resposta conforme o formato solicitado
    if formato == 'chatgpt':
        resposta = formatar_para_chatgpt(info_produto)
    else:
        resposta = {
            "status": "sucesso",
            "resposta": scraper.formatar_resposta(info_produto),
            "dados_produto": info_produto,
            "fonte": fonte
        }
    
    return Response(
        json.dumps(resposta, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para processar webhooks do Whaticket"""
    try:
        data = request.json
        mensagem = data.get('message', '')
        
        # Verificar formato (completo ou chatgpt)
        formato = request.args.get('formato', 'chatgpt').lower()
        
        # Processar a mensagem
        resultado = scraper.processar_mensagem(mensagem)
        
        # Se encontrou um produto, salvar no banco
        if "erro" not in resultado and "url" in resultado:
            save_produto_to_db(resultado)
        
        # Formatar resposta conforme o formato solicitado
        if formato == 'chatgpt':
            resposta = formatar_para_chatgpt(resultado)
        else:
            resposta = {
                "status": "sucesso",
                "resposta": scraper.formatar_resposta(resultado),
                "dados_produto": resultado
            }
        
        return Response(
            json.dumps(resposta, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return Response(
            json.dumps({
                "status": "erro",
                "mensagem": f"Erro ao processar webhook: {str(e)}",
                "chatgpt_texto": f"Não foi possível processar a mensagem. Erro: {str(e)}"
            }, ensure_ascii=False),
            status=500,
            mimetype='application/json'
        )

@app.route('/chatgpt_produto', methods=['GET'])
def chatgpt_produto():
    """Endpoint específico para retornar informações de produto formatadas para o ChatGPT"""
    url = request.args.get('url')
    if not url:
        return jsonify({"status": "erro", "mensagem": "URL não fornecida"}), 400
    
    # Verificar se deve forçar atualização
    force_update = request.args.get('force', 'false').lower() == 'true'
    
    # Verificar se o produto já está no banco de dados
    produto_db = None if force_update else get_produto_from_db(url)
    
    if produto_db and not force_update:
        # Produto encontrado no banco, retornar diretamente
        info_produto = produto_db
    else:
        # Produto não encontrado no banco ou forçando atualização, extrair informações
        info_produto = scraper.extrair_info_ciainfor(url)
        
        # Salvar no banco de dados
        if "erro" not in info_produto:
            save_produto_to_db(info_produto)
    
    # Formatar para o ChatGPT
    resposta = formatar_para_chatgpt(info_produto)
    
    return Response(
        json.dumps(resposta, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# Inicializar o banco de dados ao iniciar o aplicativo
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
