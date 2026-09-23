import time
import pyautogui
from utils import focar_estoque

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def enviar_nfe(numero_pedido):
  """Executa a rotina completa de transmissão, tratamento de telas e fechamento da NFE."""
  focar_estoque()
  time.sleep(1.0)

  print(f"[ENVIO NFE] Iniciando transmissão para o pedido: {numero_pedido}")

  # 1. Abre a tela de NFE (Ctrl + N)
  pyautogui.hotkey("ctrl", "n")
  time.sleep(1.5)

  # 2. Transmite (Alt + 1)
  pyautogui.hotkey("alt", "1")
  time.sleep(3.0)  # Tempo de espera seguro para a transmissão e retorno da SEFAZ

  # 3. Fecha a pré-visualização (Alt + F)
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  # 4. Foca na janela de envio de e-mail clicando no CENTRO exato da tela (dinâmico para qualquer resolução)
  largura, altura = pyautogui.size()
  centro_x = largura / 2
  centro_y = altura / 2

  pyautogui.click(x=centro_x, y=centro_y)
  time.sleep(0.4)
  pyautogui.hotkey("alt", "f4")
  time.sleep(1.0)

  # 5. Filtra e atualiza (Alt + F)
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  # 6. Exporta (Alt + 7)
  pyautogui.hotkey("alt", "7")
  time.sleep(1.5)

  # 7. Fecha a janela do Windows que é aberta no processo (Alt + F4)
  pyautogui.hotkey("alt", "f4")
  time.sleep(0.8)

  # 8. Fecha o movimento e volta para a tela inicial do ERP (Alt + E)
  pyautogui.hotkey("alt", "e")
  time.sleep(1.0)

  print(f"[ENVIO NFE] NFE do pedido {numero_pedido} enviada e finalizada com sucesso.")


# --- BLOCO DE TESTE ISOLADO DO ENVIO NFE ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: ENVIO NFE ===")
  input(
      "Certifique-se de que o VS Code está como Administrador.\n"
      "Pressione ENTER para digitar o número do pedido..."
  )

  try:
    num_teste = input("Digite um número de pedido real já faturado para testar o envio: ")
    enviar_nfe(num_teste)
    print("[SUCESSO] Teste de envio de NFE finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE ENVIO NFE]: {e}")