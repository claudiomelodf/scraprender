#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from produto_scraper import ProdutoScraper

def testar_extracao_produto(url):
    """
    Testa a extração de informações de um produto específico
    """
    print(f"\n\n=== Testando extração para URL: {url} ===")
    scraper = ProdutoScraper()
    
    # Extrair informações
    info = scraper.extrair_info_ciainfor(url)
    
    # Exibir resultado em JSON formatado
    print("\nInformações extraídas (JSON):")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    
    # Exibir resposta formatada
    print("\nResposta formatada para o cliente:")
    print("-" * 80)
    print(scraper.formatar_resposta(info))
    print("-" * 80)
    
    return info

def testar_processamento_mensagem(mensagem):
    """
    Testa o processamento de uma mensagem com gatilho
    """
    print(f"\n\n=== Testando processamento de mensagem ===")
    print(f"Mensagem: {mensagem}")
    
    scraper = ProdutoScraper()
    
    # Processar mensagem
    resultado = scraper.processar_mensagem(mensagem)
    
    # Exibir resultado em JSON formatado
    print("\nResultado do processamento (JSON):")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Exibir resposta formatada
    print("\nResposta formatada para o cliente:")
    print("-" * 80)
    print(scraper.formatar_resposta(resultado))
    print("-" * 80)
    
    return resultado

if __name__ == "__main__":
    # Verificar se foi fornecida uma URL como argumento
    if len(sys.argv) > 1:
        url = sys.argv[1]
        testar_extracao_produto(url)
    else:
        # URLs de teste
        urls_teste = [
            "https://www.ciainfor.com.br/cabo-vga-macho-x-vga-macho-15-metros-cfiltro",
            # Adicione mais URLs para teste conforme necessário
        ]
        
        # Testar extração para cada URL
        for url in urls_teste:
            testar_extracao_produto(url)
        
        # Testar processamento de mensagens
        mensagens_teste = [
            "Olá,%20tudo%20bem?%20Preciso%20de%20ajuda%20com%20o%20produto%20https://www.ciainfor.com.br/cabo-vga-macho-x-vga-macho-15-metros-cfiltro",
            "Preciso%20de%20ajuda%20com%20o%20produto%20Memoria%20DDR4%2016GB%203200MHz%20XMP%20ARGB%20Spectrix%20Black%20XPG%20https://www.ciainfor.com.br/memoria-ddr4-16gb-3200mhz-xmp-argb-spectrix-black-xpg-ax4u32001g16a-sb41",
            "Mensagem sem gatilho ou URL"
        ]
        
        for mensagem in mensagens_teste:
            testar_processamento_mensagem(mensagem)
