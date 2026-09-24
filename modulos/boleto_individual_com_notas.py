import time
import pyautogui
import pyperclip
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boletos_individuais_com_notas(numero_pedido):
  """Executa a rotina financeira para um pedido com múltiplas notas (NFE + NFS/RPS)."""
  print(f"[FINANCEIRO] Consultando dados no BD para o pedido: {numero_pedido}")
  dados = consultar_dados_pedido(numero_pedido)

  if not dados:
    print(f"[ERRO] Não foi possível recuperar os dados do pedido {numero_pedido} no BD.")
    return

  nfe = dados.get("NFE")
  rps = dados.get("RPS")
  nfs = dados.get("NFS", rps)
  os_num = dados.get("OS")
  num_ped = dados.get("NUMERO_PEDIDO")

  documentos_para_processar = []
  if nfe:
    documentos_para_processar.append(("NFE", nfe))
  if rps:
    documentos_para_processar.append(("RPS", rps))

  if not documentos_para_processar:
    print(f"[AVISO] O pedido {numero_pedido} não possui NFE nem RPS registradas.")
    return

  # Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  # Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  for tipo_doc, num_doc in documentos_para_processar:
    print(f"[FINANCEIRO] Filtrando e processando {tipo_doc} número: {num_doc}...")

    prefixo = f"O.S. {os_num}" if os_num else f"PEDIDO {num_ped}"
    if tipo_doc == "NFE":
      historico = f"{prefixo} NFE {num_doc}".upper()
    else:
      historico = f"{prefixo} NFS {num_doc}".upper()

    # Navega até o campo do documento (Tab 2x)
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.3)

    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)

    pyautogui.write(str(num_doc), interval=0.08)
    time.sleep(0.3)
    pyautogui.press("tab")
    time.sleep(1.2)

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

    # Inserção do histórico via Ctrl + V garantindo maiúsculo
    pyperclip.copy(historico)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
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
    time.sleep(2.5)  # Tempo aumentado (+1s)

    pyautogui.press("s")
    time.sleep(1.0)
    pyautogui.press("s")
    time.sleep(3.5)  # Tempo extra de consolidação (+1s)

    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)
  print(f"[FINANCEIRO] Boletos individuais do pedido {numero_pedido} emitidos com sucesso.")