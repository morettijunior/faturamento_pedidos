import time
import pyautogui
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boleto_unificado_com_notas(numero_pedido):
  """Executa a rotina financeira unificada para pedidos com múltiplas notas e parcelas."""
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
  qtde_parcelas = dados.get("QTDE_PARCELAS", 1)
  lista_vencimentos = dados.get("VENCIMENTOS", [])

  if not nfe or not rps:
    print(f"[AVISO] O pedido {numero_pedido} não possui NFE e RPS simultâneas.")
    return

  documentos = [nfe, rps]
  doc_combinado = f"{nfe}/{nfs}"

  if os_num:
    historico_unificado = f"O.S. {os_num} NFE {nfe} NFS {nfs}".upper()
  else:
    historico_unificado = f"PEDIDO {num_ped} NFE {nfe} NFS {nfs}".upper()   

  # Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  # Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  # Clica no botão Adicionar
  largura_tela, altura_tela = pyautogui.size()
  pyautogui.click(x=largura_tela * (160 / 1440), y=altura_tela * (206 / 900))
  time.sleep(1.0)

  # Preenche os documentos
  for i, doc in enumerate(documentos):
    if i == 0:
      for _ in range(4):
        pyautogui.hotkey("shift", "tab")
        time.sleep(0.2)
      time.sleep(0.3)
    else:
      pyautogui.hotkey("alt", "c")
      time.sleep(0.3)
      pyautogui.press("tab")
      time.sleep(0.2)
      pyautogui.press("tab")
      time.sleep(0.3)

    pyautogui.write(str(doc), interval=0.08)
    time.sleep(0.3)
    pyautogui.press("tab")
    time.sleep(1.2)

  # Seleção múltipla na grade
  total_linhas_grade = qtde_parcelas * 2
  total_descidas = max(1, total_linhas_grade - 1)

  pyautogui.press("up")
  time.sleep(0.2)
  pyautogui.keyDown("shift")
  for _ in range(total_descidas):
    pyautogui.press("down")
    time.sleep(0.05)
  pyautogui.keyUp("shift")
  time.sleep(0.3)

  # Geração da fatura (Alt + G)
  pyautogui.hotkey("alt", "g")
  time.sleep(1.5)

  for _ in range(6):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  pyautogui.write(str(qtde_parcelas), interval=0.08)
  time.sleep(0.3)

  pyautogui.press("tab")
  pyautogui.press("tab")
  time.sleep(0.2)

  primeiro_venc = lista_vencimentos[0] if lista_vencimentos else "22102026"
  pyautogui.write(str(primeiro_venc), interval=0.08)
  time.sleep(0.2)
  pyautogui.press("enter")
  time.sleep(0.5)

  pyautogui.hotkey("alt", "g")
  time.sleep(1.5)

  for _ in range(3):
    pyautogui.hotkey("shift", "tab")
    time.sleep(0.15)
  time.sleep(0.3)

  if qtde_parcelas > 1:
    pyautogui.press("right")
    time.sleep(0.2)
    for idx in range(1, qtde_parcelas):
      data_venc = lista_vencimentos[idx] if idx < len(lista_vencimentos) else primeiro_venc
      pyautogui.press("down")
      time.sleep(0.2)
      pyautogui.press("enter")
      time.sleep(0.2)
      pyautogui.hotkey("ctrl", "a")
      pyautogui.press("delete")
      time.sleep(0.1)
      pyautogui.write(str(data_venc), interval=0.08)
      time.sleep(0.2)
      pyautogui.press("enter")
      time.sleep(0.3)

  # Dados finais da fatura
  pyautogui.hotkey("alt", "a")
  time.sleep(1.0)
  pyautogui.write("NF", interval=0.08)
  time.sleep(0.2)

  for _ in range(3):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  pyautogui.write(doc_combinado, interval=0.08)
  time.sleep(0.3)

  for _ in range(6):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  pyautogui.hotkey("ctrl", "a")
  pyautogui.press("delete")
  time.sleep(0.1)
  pyautogui.write(historico_unificado, interval=0.08)
  time.sleep(0.5)

  pyautogui.hotkey("alt", "t")
  time.sleep(1.0)
  pyautogui.press("s")
  time.sleep(2.0)

  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  # --- EMISSÃO DO BOLETO CONSOLIDADO ---
  pyautogui.press("f8")
  time.sleep(1.5)

  pyautogui.press("tab")
  time.sleep(0.2)
  pyautogui.press("tab")
  time.sleep(0.3)

  pyautogui.write(doc_combinado, interval=0.08)
  time.sleep(0.3)
  pyautogui.press("tab")
  time.sleep(1.2)

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
  pyautogui.press("down")
  time.sleep(0.2)

  print(f"[FINANCEIRO] Boleto unificado do pedido {numero_pedido} emitido com sucesso!")  