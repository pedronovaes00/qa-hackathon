#!/usr/bin/env python3
"""
Script para aplicar correcoes automaticas de locators.
Le o arquivo JSON gerado pela analise e aplica as correcoes.
"""
import os
import sys
from corretor import ler_fix_json, aplicar_e_validar

def main():
    print("=" * 60)
    print("  APLICAR CORRECAO DE LOCATORS")
    print("=" * 60)
    print()

    # Le o JSON com as correcoes
    resultado = ler_fix_json()
    
    if not resultado:
        print("Erro: Nenhum arquivo de correcao encontrado.")
        print("Execute o teste primeiro para gerar o JSON de correcao.")
        return 1

    locators_por_nome = resultado.get("locator_names", {})
    locators = resultado.get("locators", {})
    
    if not locators_por_nome and not locators:
        print("Erro: JSON nao contem correcoes.")
        return 1

    # Mostra o que vai ser corrigido (APENAS os que mudaram)
    print("Correcoes encontradas:")
    print()
    
    # Usa "locators" que contem apenas os seletores que mudaram
    if locators:
        for antigo, novo in locators.items():
            print(f"  {antigo:20s} -> {novo}")
    elif locators_por_nome:
        # Fallback: se locators estiver vazio, usa locator_names (compatibilidade)
        for nome, novo in locators_por_nome.items():
            print(f"  {nome:18s} -> {novo}")
    else:
        print("Erro: Nenhuma correcao encontrada no JSON.")
        return 1
    
    print()
    print("-" * 60)
    
    # Pergunta se quer aplicar
    try:
        resposta = input("\nAplicar correcoes e re-testar? (s/N): ")
    except (EOFError, KeyboardInterrupt):
        print("\nOperacao cancelada.")
        return 1
    
    if resposta.strip().lower() != "s":
        print("Operacao cancelada.")
        return 1
    
    print()
    print("Aplicando correcoes...")
    print("=" * 60)
    
    # Aplica as correcoes e valida (sempre com --headed)
    sucesso = aplicar_e_validar(resultado, is_headed=True)
    
    print()
    print("=" * 60)
    if sucesso:
        print("  SUCESSO: Correcoes aplicadas e validadas!")
    else:
        print("  ERRO: Falha ao aplicar ou validar correcoes.")
    print("=" * 60)
    
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
