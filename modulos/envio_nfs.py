import time
import pyautogui
from utils import focar_estoque
from bd import verificar_nfs_transmitida  # Importa a função de validação no BD

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def enviar_nfs(numero_pedido):
  """Executa a rotina completa de transmissão da NFS via navegação por teclado e atalhos."""
  focar_estoque()
  time.sleep(0.5)

  print(f"[ENVIO NFS] Iniciando transmissão para o pedido: {numero_pedido}")

  # 1. Abre a tela de NFS (Ctrl + Alt + S)
  pyautogui.hotkey("ctrl", "alt", "s")
  time.sleep(1.5)

  # 2. Navega até o botão transmitir usando Shift + Tab duas vezes
  pyautogui.hotkey("shift", "tab")
  time.sleep(0.2)
  pyautogui.hotkey("shift", "tab")
  time.sleep(0.3)

  # 3. Aciona a transmissão (Espaço)
  pyautogui.press("space")
  time.sleep(5.0)  # Tempo seguro para o retorno da prefeitura / processamento

  # --- VALIDAÇÃO DE SUCESSO NO BANCO DE DADOS (POLLING DE 30s) ---
  print(
      f"[ENVIO NFS] Verificando se a NFS do pedido {numero_pedido} foi"
      " transmitida (Status 'E')..."
  )
  tempo_limite = 30
  tempo_decorrido = 0
  sucesso = False

  while tempo_decorrido < tempo_limite:
    time.sleep(2.0)
    tempo_decorrido += 2.0
    print(
        "[ENVIO NFS] Checando status no banco..."
        f" ({int(tempo_decorrido)}s/{tempo_limite}s)"
    )

    if verificar_nfs_transmitida(numero_pedido):
      sucesso = True
      break

  if not sucesso:
    raise Exception(
        f"A NFS do pedido {numero_pedido} não foi transmitida pela Prefeitura"
        " dentro do tempo limite de 30 segundos (Prefeitura fora do ar ou"
        " rejeitada)."
    )

  print(f"[ENVIO NFS] Confirmação obtida no BD! NFS com Status 'E' confirmada.")
  # ------------------------------------------------------------------

  # 4. Cancela a impressão (Alt + C)
  pyautogui.hotkey("alt", "c")
  time.sleep(1.0)

  # 5. Cancela o envio de e-mail pressionando 'N'
  pyautogui.press("n")
  time.sleep(1.0)

  # 6. Retorna ao botão de sair usando Shift + Tab
  pyautogui.hotkey("shift", "tab")
  time.sleep(0.3)

  # 7. Sai e retorna à tela inicial (Espaço)
  pyautogui.press("space")
  time.sleep(0.5)

  print(
      f"[ENVIO NFS] NFS do pedido {numero_pedido} enviada e finalizada com"
      " sucesso."
  )


# --- BLOCO DE TESTE ISOLADO DO ENVIO NFS ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: ENVIO NFS ===")
  input(
      "Certifique-se de que o VS Code está como Administrador.\n"
      "Pressione ENTER para digitar o número do pedido..."
  )

  try:
    num_teste = input(
        "Digite um número de pedido real já faturado para testar o envio de"
        " NFS: "
    )
    enviar_nfs(num_teste)
    print("[SUCESSO] Teste de envio de NFS finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE ENVIO NFS]: {e}")