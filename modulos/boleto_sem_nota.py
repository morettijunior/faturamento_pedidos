import time
import pyautogui
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boleto_sem_nota(numero_pedido):
  """Executa a rotina financeira para um pedido SEM nota fiscal."""
  print(f"[FINANCEIRO] Consultando dados no BD para o pedido: {numero_pedido}")
  dados = consultar_dados_pedido(numero_pedido)

  if not dados:
    print(f"[ERRO] Não foi possível recuperar os dados do pedido {numero_pedido} no BD.")
    return

  parcelas = dados.get("PARCELAS", [])
  if not parcelas:
    print(f"[ERRO] Nenhuma parcela encontrada na FLAN para o pedido {numero_pedido}.")
    return

  os_num = dados.get("OS")
  if os_num:
    historico = f"O.S. {os_num}".upper()
  else:
    historico = f"PEDIDO {dados['NUMERO_PEDIDO']}".upper()

  # Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  # Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  # Navega até o campo do número do documento (Tab 2x)
  pyautogui.press("tab")
  time.sleep(0.2)
  pyautogui.press("tab")
  time.sleep(0.3)

  pyautogui.write(str(numero_pedido), interval=0.08)
  time.sleep(0.3)
  pyautogui.press("tab")
  time.sleep(1.2)

  for i in range(len(parcelas)):
    print(f"[FINANCEIRO] Processando parcela {i + 1} de {len(parcelas)}...")

    if i > 0:
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
      pyautogui.press("down")
      time.sleep(0.3)

    pyautogui.hotkey("ctrl", "t")
    time.sleep(1.0)

    for _ in range(4):
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
    time.sleep(0.3)

    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)

    pyautogui.write(historico, interval=0.08)
    time.sleep(0.5)

    pyautogui.hotkey("alt", "s")
    time.sleep(0.8)
    pyautogui.press("s")
    time.sleep(1.5)

    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

    pyautogui.press("space")
    time.sleep(1.5)

    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.3)

    pyautogui.write("06", interval=0.08)
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.5)

    pyautogui.hotkey("alt", "o")
    time.sleep(1.5)

    pyautogui.press("s")
    time.sleep(1.0)
    pyautogui.press("s")
    time.sleep(2.5)

    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)
  print(f"[FINANCEIRO] Boletos sem nota do pedido {numero_pedido} emitidos com sucesso.")