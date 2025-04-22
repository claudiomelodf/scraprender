#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProdutoScraper:
    """
    Classe para extrair informações de produtos a partir de URLs da Cia da Informática
    e outros sites de e-commerce.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
    def extrair_nome_produto_da_url(self, url):
        """Extrai o nome do produto a partir da URL"""
        try:
            # Pega o último segmento da URL
            path = urllib.parse.urlparse(url).path
            nome_produto = path.strip('/').split('/')[-1]
            # Substitui hífens por espaços e capitaliza
            nome_produto = nome_produto.replace('-', ' ').title()
            return nome_produto
        except Exception as e:
            logger.error(f"Erro ao extrair nome do produto da URL: {e}")
            return "Produto"
    
    def extrair_info_ciainfor(self, url):
        """
        Extrai informações de produtos do site ciainfor.com.br
        """
        try:
            logger.info(f"Extraindo informações do produto: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extrair informações básicas
            nome_produto = soup.select_one('h1') or soup.select_one('.product-name')
            nome_produto = nome_produto.text.strip() if nome_produto else self.extrair_nome_produto_da_url(url)
            
            # Extrair preço
            preco_element = soup.select_one('.product-price') or soup.select_one('.price-new')
            preco = preco_element.text.strip() if preco_element else "Preço não disponível"
            
            # Extrair código do produto
            codigo_element = soup.find(string=re.compile('Código:'))
            codigo = codigo_element.next_element.strip() if codigo_element else "Não informado"
            
            # Extrair disponibilidade
            disponibilidade_element = soup.find(string=re.compile('Estoque:'))
            disponibilidade = "Disponível" if disponibilidade_element and "Disponível" in disponibilidade_element.parent.text else "Não informado"
            
            # Extrair descrição
            descricao_element = soup.select_one('.product-description') or soup.select_one('.tab-content')
            descricao = ""
            if descricao_element:
                descricao = descricao_element.get_text(strip=True, separator='\n')
            else:
                # Tentar extrair de parágrafos
                paragrafos = soup.select('p')
                descricao = '\n'.join([p.text.strip() for p in paragrafos if len(p.text.strip()) > 50])
            
            # Extrair especificações técnicas
            especificacoes = []
            specs_elements = soup.select('li') or soup.select('.product-features li')
            for spec in specs_elements:
                spec_text = spec.text.strip()
                if spec_text and len(spec_text) > 5 and '-' in spec_text:
                    especificacoes.append(spec_text)
            
            # Montar resultado
            resultado = {
                "nome": nome_produto,
                "preco": preco,
                "codigo": codigo,
                "disponibilidade": disponibilidade,
                "descricao": descricao,
                "especificacoes": especificacoes,
                "url": url
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações do produto: {e}")
            return {
                "erro": f"Não foi possível extrair informações do produto: {str(e)}",
                "url": url
            }
    
    def processar_mensagem(self, mensagem):
        """
        Processa uma mensagem para identificar o gatilho e extrair informações do produto
        """
        # Decodificar a mensagem (substituir %20 por espaços, etc)
        mensagem_decodificada = urllib.parse.unquote(mensagem)
        
        # Verificar se contém o gatilho
        gatilho = "Preciso de ajuda com o produto"
        if gatilho.lower() in mensagem_decodificada.lower():
            logger.info("Gatilho detectado na mensagem")
            
            # Extrair URL usando expressão regular
            urls = re.findall(r'https?://[^\s]+', mensagem_decodificada)
            
            if urls:
                url = urls[0]
                logger.info(f"URL encontrada: {url}")
                
                # Verificar domínio e chamar o extrator apropriado
                if "ciainfor.com.br" in url:
                    return self.extrair_info_ciainfor(url)
                else:
                    # Implementar outros extratores conforme necessário
                    return {
                        "erro": "Domínio não suportado. Atualmente só extraímos informações de ciainfor.com.br",
                        "url": url
                    }
            else:
                return {
                    "erro": "Nenhuma URL encontrada na mensagem",
                    "mensagem_original": mensagem_decodificada
                }
        else:
            return {
                "erro": "Gatilho não encontrado na mensagem",
                "mensagem_original": mensagem_decodificada
            }
    
    def formatar_resposta(self, info_produto):
        """
        Formata as informações do produto em uma resposta amigável
        """
        if "erro" in info_produto:
            return f"Desculpe, {info_produto['erro']}"
        
        resposta = f"Informações sobre o produto: {info_produto['nome']}\n\n"
        resposta += f"💰 Preço: {info_produto['preco']}\n"
        resposta += f"📦 Disponibilidade: {info_produto['disponibilidade']}\n"
        resposta += f"🔢 Código: {info_produto['codigo']}\n\n"
        
        if info_produto['descricao']:
            resposta += f"📝 Descrição:\n{info_produto['descricao']}\n\n"
        
        if info_produto['especificacoes']:
            resposta += "🔍 Especificações:\n"
            for spec in info_produto['especificacoes']:
                resposta += f"• {spec}\n"
        
        resposta += f"\n🔗 Link do produto: {info_produto['url']}"
        
        return resposta

# Exemplo de uso
if __name__ == "__main__":
    scraper = ProdutoScraper()
    
    # Exemplo 1: URL direta
    url_teste = "https://www.ciainfor.com.br/cabo-vga-macho-x-vga-macho-15-metros-cfiltro"
    info = scraper.extrair_info_ciainfor(url_teste)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print("\nResposta formatada:")
    print(scraper.formatar_resposta(info))
    
    # Exemplo 2: Mensagem com gatilho
    mensagem_teste = "Olá,%20tudo%20bem?%20Preciso%20de%20ajuda%20com%20o%20produto%20https://www.ciainfor.com.br/cabo-vga-macho-x-vga-macho-15-metros-cfiltro"
    info = scraper.processar_mensagem(mensagem_teste)
    print("\n\nProcessamento de mensagem:")
    print(json.dumps(info, indent=2, ensure_ascii=False))
