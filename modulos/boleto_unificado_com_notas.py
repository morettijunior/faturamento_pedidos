import time
import pyautogui
from bd import consultar_dados_pedido
from utils import focar_financeiro

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_boleto_unificado_com_notas(numero_pedido):
  """Executa a rotina financeira completa para pedidos com múltiplas notas e

  múltiplas parcelas personalizadas (NFE + NFS/RPS), inserindo cada vencimento
  individualmente
  e emitindo o boleto consolidado.
  """
  # 1. Consulta o BD para pegar todos os dados necessários
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
  qtde_parcelas = dados.get("QTDE_PARCELAS", 1)  # Ex: 2 ou 3 parcelas
  lista_vencimentos = dados.get(
      "VENCIMENTOS", []
  )  # Lista com as datas (ex: ['22102026', '22112026'])

  if not nfe or not rps:
    print(
        f"[AVISO] O pedido {numero_pedido} não possui NFE e RPS simultâneas."
        " Para nota única, utilize o módulo correspondente."
    )
    return

  documentos = [nfe, rps]
  doc_combinado = f"{nfe}/{nfs}"

  # Monta o histórico unificado
  if os_num:
    historico_unificado = f"O.S. {os_num} NFE {nfe} NFS {nfs}"
  else:
    historico_unificado = f"PEDIDO {num_ped} NFE {nfe} NFS {nfs}"

  print(
      f"[FINANCEIRO] Doc Combinado: {doc_combinado} | Parcelas:"
      f" {qtde_parcelas} | Vencimentos: {lista_vencimentos}"
  )

  # 2. Foca no TGA Financeiro
  focar_financeiro()
  time.sleep(1.0)

  # 3. Abre a tela do financeiro (F8)
  pyautogui.press("f8")
  time.sleep(1.5)

  # --- CLIQUE NO BOTÃO ADICIONAR (PROPORCIONAL À TELA) ---
  print("[FINANCEIRO] Clicando no botão 'Adicionar'...")
  largura_tela, altura_tela = pyautogui.size()
  x_proporcional = largura_tela * (160 / 1440)
  y_proporcional = altura_tela * (206 / 900)

  pyautogui.click(x=x_proporcional, y=y_proporcional)
  time.sleep(1.0)

  # --- PREENCHIMENTO DOS DOCUMENTOS ---
  for i, doc in enumerate(documentos):
    print(f"[FINANCEIRO] Inserindo documento {i + 1} de {len(documentos)}: {doc}")

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

  # --- SELEÇÃO MÚLTIPLA PROPORCIONAL AO Nº DE PARCELAS ---
  # Cada nota com X parcelas gera (X * 2) linhas na grade
  total_linhas_grade = qtde_parcelas * 2
  total_descidas = max(1, total_linhas_grade - 1)

  print(
      f"[FINANCEIRO] Selecionando {total_linhas_grade} linhas na grade com"
      " Shift..."
  )
  pyautogui.press("up")
  time.sleep(0.2)
  pyautogui.keyDown("shift")
  for _ in range(total_descidas):
    pyautogui.press("down")
    time.sleep(0.05)
  pyautogui.keyUp("shift")
  time.sleep(0.3)

  # --- GERAÇÃO DA FATURA (ALT + G) ---
  print("[FINANCEIRO] Acionando geração de fatura (Alt + G)...")
  pyautogui.hotkey("alt", "g")
  time.sleep(1.5)

  # 6x Tab para chegar no número de parcelas
  for _ in range(6):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  # Digita a quantidade de parcelas
  pyautogui.write(str(qtde_parcelas), interval=0.08)
  time.sleep(0.3)

  # 2x Tab para o vencimento da primeira parcela
  pyautogui.press("tab")
  pyautogui.press("tab")
  time.sleep(0.2)

  # Digita o vencimento da primeira parcela + Enter
  primeiro_venc = (
      lista_vencimentos[0] if lista_vencimentos else "22102026"
  )  # Fallback de segurança
  pyautogui.write(str(primeiro_venc), interval=0.08)
  time.sleep(0.2)
  pyautogui.press("enter")
  time.sleep(0.5)

  # Alt + G para gerar as parcelas iniciais
  pyautogui.hotkey("alt", "g")
  time.sleep(1.5)

  # 3x Shift+Tab para ir para a janela das parcelas geradas
  for _ in range(3):
    pyautogui.hotkey("shift", "tab")
    time.sleep(0.15)
  time.sleep(0.3)

  # --- AJUSTE MANUAL DOS VENCIMENTOS SEGUINTES (SE HOUVER MAIS DE 1 PARCELA) ---
  if qtde_parcelas > 1:
    print("[FINANCEIRO] Ajustando vencimentos das parcelas adicionais...")
    # Seta para a direita para ir para a coluna de vencimentos
    pyautogui.press("right")
    time.sleep(0.2)

    # Itera a partir da segunda parcela (índice 1 em diante)
    for idx in range(1, qtde_parcelas):
      data_venc = (
          lista_vencimentos[idx] if idx < len(lista_vencimentos) else primeiro_venc
      )

      # Seta para baixo para ir para a próxima linha de vencimento
      pyautogui.press("down")
      time.sleep(0.2)

      # Enter para editar o valor
      pyautogui.press("enter")
      time.sleep(0.2)

      # Limpa e digita a nova data de vencimento + Enter
      pyautogui.hotkey("ctrl", "a")
      pyautogui.press("delete")
      time.sleep(0.1)
      pyautogui.write(str(data_venc), interval=0.08)
      time.sleep(0.2)
      pyautogui.press("enter")
      time.sleep(0.3)

  # --- AVANÇAR E PREENCHER DADOS FINAIS ---
  print("[FINANCEIRO] Avançando para os dados finais da fatura (Alt + A)...")
  pyautogui.hotkey("alt", "a")
  time.sleep(1.0)

  # Digita NF (tipo documento)
  pyautogui.write("NF", interval=0.08)
  time.sleep(0.2)

  # 3x Tab até o número do documento
  for _ in range(3):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  # Digita o número do documento combinado (ex: 12345/12345)
  pyautogui.write(doc_combinado, interval=0.08)
  time.sleep(0.3)

  # 6x Tab até o histórico
  for _ in range(6):
    pyautogui.press("tab")
    time.sleep(0.15)
  time.sleep(0.2)

  # Insere o histórico unificado
  pyautogui.hotkey("ctrl", "a")
  pyautogui.press("delete")
  time.sleep(0.1)
  pyautogui.write(historico_unificado, interval=0.08)
  time.sleep(0.5)

  # Terminar e Confirmar (Alt + T e S)
  print("[FINANCEIRO] Finalizando fatura...")
  pyautogui.hotkey("alt", "t")
  time.sleep(1.0)
  pyautogui.press("s")
  time.sleep(2.0)

  # --- EMISSÃO DO BOLETO CONSOLIDADO ---
  print(
      "[FINANCEIRO] Fechando e reabrindo F8 para emitir o boleto consolidado..."
  )
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

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

  # Abre a tela do boleto (Espaço)
  pyautogui.press("space")
  time.sleep(1.5)

  # 2x Tab para o portador
  pyautogui.press("tab")
  time.sleep(0.2)
  pyautogui.press("tab")
  time.sleep(0.3)

  # Digita o portador (06) e avança
  pyautogui.write("06", interval=0.08)
  time.sleep(0.2)
  pyautogui.press("tab")
  time.sleep(0.5)

  # Confirma a geração do boleto (Alt + O) e salva/imprime ('S' e 'S')
  pyautogui.hotkey("alt", "o")
  time.sleep(1.5)
  pyautogui.press("s")
  time.sleep(1.0)
  pyautogui.press("s")
  time.sleep(2.5)

  # Fecha a tela do boleto (Alt + F)
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  # Vai para o próximo lançamento com a seta para baixo
  pyautogui.press("down")
  time.sleep(0.2)

  print(
      f"[FINANCEIRO] Boleto unificado com {qtde_parcelas} parcelas do pedido"
      f" {numero_pedido} emitido com sucesso!"
  )


# --- BLOCO DE TESTE ISOLADO ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: BOLETO UNIFICADO COM PARCELAS E VENCIMENTOS ===")
  input(
      "Certifique-se de que o TGA Financeiro está maximizado e acessível.\n"
      "Pressione ENTER para continuar..."
  )

  try:
    num_teste = input(
        "Digite o número de um pedido parcelado (NFE + NFS) para testar: "
    )
    emitir_boleto_unificado_com_notas(num_teste)
    print("[SUCESSO] Processo finalizado com êxito!")
  except Exception as e:
    print(f"\n[ERRO NO TESTE]: {e}")