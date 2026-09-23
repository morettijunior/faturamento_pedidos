import time

try:
  import pygetwindow as gw
except ImportError:
  gw = None

# Configurações globais de segurança do pyautogui
FAILSAFE = True
PAUSE = 0.25


def _focar_janela_por_prefixo(prefixo):
  """Função genérica auxiliar para focar qualquer janela que comece com o prefixo informado."""
  if gw is None:
    return

  try:
    janelas = [
        w for w in gw.getAllWindows() if w.title and w.title.startswith(prefixo)
    ]
    if janelas:
      janela = janelas[0]
      if janela.isMinimized:
        janela.restore()
      janela.activate()
      time.sleep(0.4)
  except Exception as e:
    print(f"[AVISO] Erro ao tentar focar na janela '{prefixo}': {e}")


def focar_estoque():
  """Traz a janela do TGA Estoque para o primeiro plano dinamicamente."""
  _focar_janela_por_prefixo("TGA Estoque")


def focar_financeiro():
  """Traz a janela do TGA Financeiro para o primeiro plano dinamicamente."""
  _focar_janela_por_prefixo("TGA Financeiro")