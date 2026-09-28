import time
import pyautogui
from utils import focar_estoque

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_nfe(numero_pedido):
  """Emite a NFE utilizando o fluxo global via Ctrl + F9 e fecha a tela ao terminar."""
  focar_estoque()
  time.sleep(0.5)

  print(f"[NFE] Iniciando faturamento global para o pedido: {numero_pedido}")

  # 1. Abre a tela global de faturamento (Ctrl + F9)
  pyautogui.hotkey("ctrl", "f9")
  time.sleep(2.0)  # Tempo para a tela global abrir

  # 2. Limpeza rápida e otimizada do campo
# Apaga voltando com o backspace rapidamente
  for _ in range(6):  # Número seguro de vezes para cobrir o campo
    pyautogui.press("delete")
    time.sleep(0.05)

  # 3. Seleciona o movimento da venda (2.2.03) e confirma
  pyautogui.write("2.2.03", interval=0.05)
  pyautogui.press("enter")
  time.sleep(0.5)

  # 4. Vai para o campo documento (Alt + D)
  pyautogui.hotkey("alt", "d")
  time.sleep(0.3)

  # 5. Digita o número do pedido e confirma
  pyautogui.write(str(numero_pedido), interval=0.05)
  pyautogui.press("enter")
  time.sleep(0.5)

  # 6. Filtra os dados (Alt + R)
  pyautogui.hotkey("alt", "r")
  time.sleep(1.0)  # Tempo para a consulta SQL retornar o registro

  # 7. Aciona o faturamento (Alt + T)
  pyautogui.hotkey("alt", "t")
  time.sleep(1.0)

  # 8. Roteiro específico para a NFE (2.2.02)
  pyautogui.write("2.2.02", interval=0.05)
  pyautogui.hotkey("alt", "p")
  time.sleep(0.5)

  pyautogui.press("enter")
  time.sleep(2.0)

  # 9. Salva o movimento e confirma com 'Sim'
  pyautogui.hotkey("alt", "s")
  time.sleep(0.5)
  pyautogui.press("enter")
  time.sleep(0.5)
  pyautogui.press("s")
  time.sleep(2.0)

  # 10. Fecha a tela de faturamento global (Alt + F)
  pyautogui.hotkey("alt", "f")
  time.sleep(0.5)

  print(
      f"[NFE] NFE do pedido {numero_pedido} processada, salva e tela fechada com"
      " sucesso."
  )


# --- BLOCO DE TESTE ISOLADO DO MÓDULO NFE ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: MÓDULO NFE (COM FECHAMENTO DA TELA) ===")
  input(
      "Certifique-se de que o VS Code está como Administrador.\n"
      "Pressione ENTER para digitar o número do pedido..."
  )

  try:
    num_teste = input("Digite um número de pedido real para testar a NFE: ")
    emitir_nfe(num_teste)
    print("[SUCESSO] Teste do módulo NFE finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE NFE]: {e}")