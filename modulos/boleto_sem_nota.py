import time
import pyautogui
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boleto_sem_nota(numero_pedido):
  """Executa a rotina financeira para um pedido SEM nota fiscal

  (seja 1 boleto ou múltiplos boletos), consultando o BD para preencher
  o histórico correto e processando todas as parcelas em sequência.
  """
  # 1. Consulta o BD para pegar as parcelas e verificar se tem O.S.
  print(f"[FINANCEIRO] Consultando dados no BD para o pedido: {numero_pedido}")
  dados = consultar_dados_pedido(numero_pedido)

  if not dados:
    print(f"[ERRO] Não foi possível recuperar os dados do pedido {numero_pedido} no BD.")
    return

  parcelas = dados.get("PARCELAS", [])
  if not parcelas:
    print(f"[ERRO] Nenhuma parcela encontrada na FLAN para o pedido {numero_pedido}.")
    return

  # Define o texto do histórico com base na presença de O.S.
  os_num = dados.get("OS")
  if os_num:
    historico = f"O.S. {os_num}"
  else:
    historico = f"PEDIDO {dados['NUMERO_PEDIDO']}"

  print(
      f"[FINANCEIRO] Total de parcelas encontradas: {len(parcelas)} | Histórico:"
      f" '{historico}'"
  )

  # 2. Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  print(f"[FINANCEIRO] Iniciando emissão de boleto(s) sem nota para o pedido: {numero_pedido}")

  # 3. Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  # 4. Navega até o campo para digitar o número do documento (Tab 2x)
  pyautogui.press("tab")
  time.sleep(0.2)
  pyautogui.press("tab")
  time.sleep(0.3)

  # 5. Digita o número do pedido e avança/filtra (Tab)
  pyautogui.write(str(numero_pedido), interval=0.08)
  time.sleep(0.3)
  pyautogui.press("tab")
  time.sleep(1.2)  # Tempo para a listagem carregar as parcelas

  # 6. Loop dinâmico para processar cada parcela (funciona para 1 ou várias)
  for i in range(len(parcelas)):
    print(f"[FINANCEIRO] Processando parcela {i + 1} de {len(parcelas)}...")

    # Se não for a primeira parcela, resgata o foco com Shift+Tab 2x e desce para a próxima linha
    if i > 0:
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
      pyautogui.press("down")
      time.sleep(0.3)

    # 6.1. Edita o lançamento atual (Ctrl + T)
    pyautogui.hotkey("ctrl", "t")
    time.sleep(1.0)

    # 6.2. Navega até o campo do histórico (Shift + Tab 4x)
    for _ in range(4):
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
    time.sleep(0.3)

    # 6.3. Limpa o histórico atual e digita o correto
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)

    pyautogui.write(historico, interval=0.08)
    time.sleep(0.5)

    # 6.4. Salva o lançamento (Alt + S) e confirma com 'S'
    pyautogui.hotkey("alt", "s")
    time.sleep(0.8)
    pyautogui.press("s")
    time.sleep(1.5)

    # 6.5. Fecha a tela de lançamento individual (Alt + F)
    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

    # 6.6. Abre o boleto bancário (Espaço)
    pyautogui.press("space")
    time.sleep(1.5)

    # 6.7. Vai para o campo portador (Tab 2x)
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.3)

    # 6.8. Digita o portador (06) e avança (Tab)
    pyautogui.write("06", interval=0.08)
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.5)

    # 6.9. Confirma a geração do boleto (Alt + O)
    pyautogui.hotkey("alt", "o")
    time.sleep(1.5)

    # 6.10. Confirmações de salvamento e impressão ('S' e 'S')
    pyautogui.press("s")
    time.sleep(1.0)
    pyautogui.press("s")
    time.sleep(2.5)

    # 6.11. Fecha a tela do boleto (Alt + F) -> Retorna para a tela de manutenção
    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

  # 7. Fecha a tela principal do financeiro (Alt + F) ao concluir todas as parcelas
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  print(
      f"[FINANCEIRO] Todos os {len(parcelas)} boletos sem nota do pedido {numero_pedido}"
      " foram emitidos e finalizados com sucesso."
  )


# --- BLOCO DE TESTE ISOLADO ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: BOLETO SEM NOTA (GERAL) ===")
  input(
      "Certifique-se de que o VS Code está como Administrador\n"
      "e o TGA Financeiro está acessível.\n"
      "Pressione ENTER para continuar..."
  )

  try:
    num_teste = input("Digite o número de um pedido SEM nota para testar: ")
    emitir_boleto_sem_nota(num_teste)
    print("[SUCESSO] Teste do boleto sem nota finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE BOLETO SEM NOTA]: {e}")