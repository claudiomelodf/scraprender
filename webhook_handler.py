#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
import datetime
import io
import csv
import pandas as pd
from flask import Flask, request, jsonify, Response, send_file
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

def get_all_produtos_from_db(limit=100, offset=0):
    """Obtém todos os produtos do banco de dados com paginação"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM produtos')
    total = cursor.fetchone()[0]
    
    cursor.execute('''
    SELECT url, nome, preco, disponibilidade, codigo, data_atualizacao 
    FROM produtos ORDER BY data_atualizacao DESC LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    results = cursor.fetchall()
    conn.close()
    
    produtos = []
    for result in results:
        colunas = ['url', 'nome', 'preco', 'disponibilidade', 'codigo', 'data_atualizacao']
        produto = dict(zip(colunas, result))
        produtos.append(produto)
    
    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'produtos': produtos
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
    
    # Verificar se o produto já está no banco de dados
    produto_db = None if force_update else get_produto_from_db(url)
    
    if produto_db and not force_update:
        # Produto encontrado no banco, retornar diretamente
        resposta = scraper.formatar_resposta(produto_db)
        return Response(
            json.dumps({
                "status": "sucesso",
                "resposta": resposta,
                "dados_produto": produto_db,
                "fonte": "cache"
            }, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
    
    # Produto não encontrado no banco ou forçando atualização, extrair informações
    info_produto = scraper.extrair_info_ciainfor(url)
    
    # Salvar no banco de dados
    if "erro" not in info_produto:
        save_produto_to_db(info_produto)
    
    # Formatar resposta
    resposta = scraper.formatar_resposta(info_produto)
    
    return Response(
        json.dumps({
            "status": "sucesso",
            "resposta": resposta,
            "dados_produto": info_produto,
            "fonte": "web"
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
    
    # Verificar se deve forçar atualização
    force_update = request.args.get('force', 'false').lower() == 'true'
    
    # Verificar se o produto já está no banco de dados
    produto_db = None if force_update else get_produto_from_db(url)
    
    if produto_db and not force_update:
        # Produto encontrado no banco, usar dados do cache
        info_produto = produto_db
        fonte = "cache"
    else:
        # Produto não encontrado no banco ou forçando atualização, extrair informações
        info_produto = scraper.extrair_info_ciainfor(url)
        fonte = "web"
        
        # Salvar no banco de dados
        if "erro" not in info_produto:
            save_produto_to_db(info_produto)
    
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
            "dados_produto": info_produto,
            "fonte": fonte
        }, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/produto_excel', methods=['GET'])
def get_produto_excel():
    """Endpoint para extrair informações de um produto e retornar como arquivo Excel"""
    url = request.args.get('url')
    if not url:
        return jsonify({"status": "erro", "mensagem": "URL não fornecida"}), 400
    
    # Verificar formato de saída (csv ou xlsx)
    formato = request.args.get('formato', 'xlsx').lower()
    if formato not in ['csv', 'xlsx']:
        formato = 'xlsx'  # Padrão para Excel
    
    # Verificar se deve forçar atualização
    force_update = request.args.get('force', 'false').lower() == 'true'
    
    # Verificar se o produto já está no banco de dados
    produto_db = None if force_update else get_produto_from_db(url)
    
    if produto_db and not force_update:
        # Produto encontrado no banco, usar dados do cache
        info_produto = produto_db
    else:
        # Produto não encontrado no banco ou forçando atualização, extrair informações
        info_produto = scraper.extrair_info_ciainfor(url)
        
        # Salvar no banco de dados
        if "erro" not in info_produto:
            save_produto_to_db(info_produto)
    
    # Criar DataFrame com informações principais
    dados_principais = {
        'Atributo': ['Nome', 'Preço', 'Disponibilidade', 'Código', 'URL'],
        'Valor': [
            info_produto.get('nome', ''),
            info_produto.get('preco', ''),
            info_produto.get('disponibilidade', ''),
            info_produto.get('codigo', ''),
            info_produto.get('url', '')
        ]
    }
    df_principal = pd.DataFrame(dados_principais)
    
    # Criar DataFrame com descrição
    descricao = info_produto.get('descricao', '')
    df_descricao = pd.DataFrame({'Descrição': [descricao]})
    
    # Criar DataFrame com especificações
    especificacoes = []
    for spec in info_produto.get('especificacoes', []):
        if ':' in spec:
            chave, valor = spec.split(':', 1)
            especificacoes.append({'Especificação': chave.strip(), 'Valor': valor.strip()})
        else:
            especificacoes.append({'Especificação': spec, 'Valor': ''})
    
    df_especificacoes = pd.DataFrame(especificacoes) if especificacoes else pd.DataFrame({'Especificação': [], 'Valor': []})
    
    # Criar arquivo de saída
    if formato == 'csv':
        # Criar CSV
        output = io.StringIO()
        
        # Escrever dados principais
        output.write("INFORMAÇÕES DO PRODUTO\n")
        df_principal.to_csv(output, index=False)
        
        # Escrever descrição
        output.write("\nDESCRIÇÃO\n")
        df_descricao.to_csv(output, index=False)
        
        # Escrever especificações
        output.write("\nESPECIFICAÇÕES\n")
        if not df_especificacoes.empty:
            df_especificacoes.to_csv(output, index=False)
        
        # Preparar resposta
        output.seek(0)
        
        nome_produto = info_produto.get('nome', 'produto').replace(' ', '_')[:30]
        nome_arquivo = f"{nome_produto}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{nome_arquivo}"'
            }
        )
    else:
        # Criar Excel (XLSX)
        output = io.BytesIO()
        
        # Criar Excel Writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Escrever dados principais
            df_principal.to_excel(writer, sheet_name='Produto', index=False)
            
            # Escrever descrição
            df_descricao.to_excel(writer, sheet_name='Descrição', index=False)
            
            # Escrever especificações
            if not df_especificacoes.empty:
                df_especificacoes.to_excel(writer, sheet_name='Especificações', index=False)
        
        # Preparar resposta
        output.seek(0)
        
        nome_produto = info_produto.get('nome', 'produto').replace(' ', '_')[:30]
        nome_arquivo = f"{nome_produto}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nome_arquivo
        )

@app.route('/produtos_excel', methods=['GET'])
def get_produtos_excel():
    """Endpoint para listar todos os produtos do banco de dados como arquivo Excel"""
    # Verificar formato de saída (csv ou xlsx)
    formato = request.args.get('formato', 'xlsx').lower()
    if formato not in ['csv', 'xlsx']:
        formato = 'xlsx'  # Padrão para Excel
    
    # Obter produtos do banco de dados
    limit = int(request.args.get('limit', 1000))
    offset = int(request.args.get('offset', 0))
    
    resultado = get_all_produtos_from_db(limit, offset)
    produtos = resultado['produtos']
    
    if not produtos:
        return jsonify({"status": "erro", "mensagem": "Nenhum produto encontrado no banco de dados"}), 404
    
    # Criar DataFrame com produtos
    df_produtos = pd.DataFrame(produtos)
    
    # Formatar data de atualização
    if 'data_atualizacao' in df_produtos.columns:
        df_produtos['data_atualizacao'] = pd.to_datetime(df_produtos['data_atualizacao']).dt.strftime('%d/%m/%Y %H:%M:%S')
    
    # Renomear colunas para português
    colunas_pt = {
        'url': 'URL',
        'nome': 'Nome',
        'preco': 'Preço',
        'disponibilidade': 'Disponibilidade',
        'codigo': 'Código',
        'data_atualizacao': 'Data de Atualização'
    }
    df_produtos = df_produtos.rename(columns=colunas_pt)
    
    # Criar arquivo de saída
    if formato == 'csv':
        # Criar CSV
        output = io.StringIO()
        df_produtos.to_csv(output, index=False)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename="produtos.csv"'
            }
        )
    else:
        # Criar Excel (XLSX)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_produtos.to_excel(writer, sheet_name='Produtos', index=False)
            
            # Adicionar informações sobre a exportação
            info = {
                'Informação': ['Total de Produtos', 'Data de Exportação'],
                'Valor': [resultado['total'], datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')]
            }
            pd.DataFrame(info).to_excel(writer, sheet_name='Informações', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='produtos.xlsx'
        )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para processar webhooks do Whaticket"""
    try:
        data = request.json
        mensagem = data.get('message', '')
        
        # Processar a mensagem
        resultado = scraper.processar_mensagem(mensagem)
        
        # Se encontrou um produto, salvar no banco
        if "erro" not in resultado and "url" in resultado:
            save_produto_to_db(resultado)
        
        # Formatar resposta
        resposta = scraper.formatar_resposta(resultado)
        
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

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    """Endpoint para listar todos os produtos no banco de dados"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    resultado = get_all_produtos_from_db(limit, offset)
    
    return Response(
        json.dumps({
            "status": "sucesso",
            "total": resultado['total'],
            "limit": resultado['limit'],
            "offset": resultado['offset'],
            "produtos": resultado['produtos']
        }, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/limpar_cache', methods=['POST'])
def limpar_cache():
    """Endpoint para limpar o cache de um produto específico ou todos os produtos"""
    url = request.json.get('url', None)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if url:
        # Limpar cache de um produto específico
        cursor.execute('DELETE FROM produtos WHERE url = ?', (url,))
        mensagem = f"Cache limpo para o produto: {url}"
    else:
        # Limpar todo o cache
        cursor.execute('DELETE FROM produtos')
        mensagem = "Cache de todos os produtos foi limpo"
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "sucesso",
        "mensagem": mensagem
    })

# Inicializar o banco de dados ao iniciar o aplicativo
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
