import time
import pyautogui
from utils import focar_estoque

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


def emitir_nfs(numero_pedido):
  """Emite a NFS utilizando o fluxo global via Ctrl + F9 e fecha a tela ao terminar."""
  focar_estoque()
  time.sleep(1.0)

  print(f"[NFS] Iniciando faturamento global para o pedido: {numero_pedido}")

  # 1. Abre a tela global de faturamento (Ctrl + F9)
  pyautogui.hotkey("ctrl", "f9")
  time.sleep(1.5)  # Tempo para a tela global abrir

  # 2. Limpeza rápida e otimizada dos 8 deletes
  for _ in range(8):
    pyautogui.press("delete")
  time.sleep(0.1)  # Apenas um respiro curto no final

  # 3. Seleciona o movimento da venda (2.2.03) e confirma
  pyautogui.write("2.2.03", interval=0.08)
  pyautogui.press("enter")
  time.sleep(0.8)

  # 4. Vai para o campo documento (Alt + D)
  pyautogui.hotkey("alt", "d")
  time.sleep(0.3)

  # 5. Digita o número do pedido e confirma
  pyautogui.write(str(numero_pedido), interval=0.08)
  pyautogui.press("enter")
  time.sleep(0.8)

  # 6. Filtra os dados (Alt + R)
  pyautogui.hotkey("alt", "r")
  time.sleep(1.2)  # Tempo para a consulta SQL retornar o registro

  # 7. Aciona o faturamento (Alt + T)
  pyautogui.hotkey("alt", "t")
  time.sleep(1.0)

  # 8. Roteiro específico para a NFS (2.2.07)
  pyautogui.write("2.2.07", interval=0.08)
  pyautogui.hotkey("alt", "p")
  time.sleep(1.0)

  pyautogui.press("enter")
  time.sleep(1.5)

  # 9. Salva o movimento e confirma com 'Sim'
  pyautogui.hotkey("alt", "s")
  time.sleep(0.8)
  pyautogui.press("s")
  time.sleep(2.0)

  # 10. Fecha a tela de faturamento global (Alt + F)
  pyautogui.hotkey("alt", "f")
  time.sleep(1.0)

  print(
      f"[NFS] NFS do pedido {numero_pedido} processada, salva e tela fechada com"
      " sucesso."
  )


# --- BLOCO DE TESTE ISOLADO DO MÓDULO NFS ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: MÓDULO NFS (COM FECHAMENTO DA TELA) ===")
  input(
      "Certifique-se de que o VS Code está como Administrador.\n"
      "Pressione ENTER para digitar o número do pedido..."
  )

  try:
    num_teste = input("Digite um número de pedido real para testar a NFS: ")
    emitir_nfs(num_teste)
    print("[SUCESSO] Teste do módulo NFS finalizado com êxito!")

  except Exception as e:
    print(f"\n[ERRO NO TESTE DE NFS]: {e}")