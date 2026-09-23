import time
import pyautogui
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boletos_individuais_com_notas(numero_pedido):
  """Executa a rotina financeira para um pedido com múltiplas notas (NFE + NFS/RPS),

  filtrando no ERP pelo número da NFE ou do RPS correspondente.
  """
  # 1. Consulta o BD para pegar NFE, RPS, OS e dados do pedido
  print(f"[FINANCEIRO] Consultando dados no BD para o pedido: {numero_pedido}")
  dados = consultar_dados_pedido(numero_pedido)

  if not dados:
    print(f"[ERRO] Não foi possível recuperar os dados do pedido {numero_pedido} no BD.")
    return

  nfe = dados.get("NFE")
  rps = dados.get("RPS")
  os_num = dados.get("OS")
  num_ped = dados.get("NUMERO_PEDIDO")

  documentos_para_processar = []
  if nfe:
    documentos_para_processar.append(("NFE", nfe))
  if rps:
    documentos_para_processar.append(("RPS", rps))

  if not documentos_para_processar:
    print(
        f"[AVISO] O pedido {numero_pedido} não possui NFE nem RPS registradas para"
        " faturamento individual."
    )
    return

  print(
      f"[FINANCEIRO] Documentos para filtro (NFE/RPS): {documentos_para_processar} |"
      f" O.S.: {os_num}"
  )

  # 2. Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  print(f"[FINANCEIRO] Iniciando emissão de boletos individuais para o pedido: {numero_pedido}")

  # 3. Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  # 4. Processa cada documento (NFE ou RPS) de forma independente
  for tipo_doc, num_doc in documentos_para_processar:
    print(f"[FINANCEIRO] Filtrando e processando {tipo_doc} número: {num_doc}...")

    # Monta o histórico específico conforme a regra informada
    if os_num:
      if tipo_doc == "NFE":
        historico = f"O.S. {os_num} NFE {nfe}"
      else:
        historico = f"O.S. {os_num} NFS {dados.get('NFS', num_doc)}"
    else:
      # Sem O.S. (Apenas peças)
      historico = f"PEDIDO {num_ped} NFE {nfe}"

    print(f"[FINANCEIRO] Histórico definido: '{historico}'")

    # Navega até o campo para digitar o número do documento (Tab 2x)
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.3)

    # Limpa o filtro anterior e digita estritamente o número da NFE ou do RPS
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)

    pyautogui.write(str(num_doc), interval=0.08)
    time.sleep(0.3)
    pyautogui.press("tab")
    time.sleep(1.2)  # Tempo para a listagem carregar os lançamentos daquela nota

    # Edita o lançamento (Ctrl + T)
    pyautogui.hotkey("ctrl", "t")
    time.sleep(1.0)

    # Navega até o campo do histórico (Shift + Tab 4x)
    for _ in range(4):
      pyautogui.hotkey("shift", "tab")
      time.sleep(0.2)
    time.sleep(0.3)

    # Limpa o histórico atual e insere o formatado corretamente
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)

    pyautogui.write(historico, interval=0.08)
    time.sleep(0.5)

    # Salva o lançamento (Alt + S) e confirma com 'S'
    pyautogui.hotkey("alt", "s")
    time.sleep(0.8)
    pyautogui.press("s")
    time.sleep(1.5)

    # Fecha a tela de lançamento individual (Alt + F)
    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

    # Abre o boleto bancário (Espaço)
    pyautogui.press("space")
    time.sleep(1.5)

    # Vai para o campo portador (Tab 2x)
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.3)

    # Digita o portador (06) e avança (Tab)
    pyautogui.write("06", interval=0.08)
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.5)

    # Confirma a geração do boleto (Alt + O)
    pyautogui.hotkey("alt", "o")
    time.sleep(1.5)

    # Confirmações de salvamento e impressão ('S' e 'S')
    pyautogui.press("s")
    time.sleep(1.0)
    pyautogui.press("s")
    time.sleep(2.5)

    # Fecha a tela do boleto (Alt + F) -> Retorna para a tela de manutenção
    pyautogui.hotkey("alt", "f")
    time.sleep(1.0)

  # 5. Fecha a tela principal do financeiro (Alt + F) ao concluir
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  print(
      f"[FINANCEIRO] Todos os boletos individuais do pedido {numero_pedido}"
      " foram emitidos com sucesso."
  )


# --- BLOCO DE TESTE ISOLADO ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: BOLETO INDIVIDUAL COM NOTAS ===")
  input(
      "Certifique-se de que o VS Code está como Administrador\n"
      "e o TGA Financeiro está acessível.\n"
      "Pressione ENTER para continuar..."
  )

  try:
    num_teste = input("Digite o número de um pedido com NFE e NFS emitidas para testar: ")
    emitir_boletos_individuais_com_notas(num_teste)
    print("[SUCESSO] Teste de boletos individuais com notas finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE BOLETOS INDIVIDUAIS]: {e}")