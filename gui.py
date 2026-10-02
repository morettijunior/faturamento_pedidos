import os
import sys
import tkinter as tk
from tkinter import messagebox

# Configuração de caminhos
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "modulos"))

# Importação dos módulos específicos de telas
try:
    from modulos.gui_modulo_os import JanelaFaturamentoOS
except ImportError:
    JanelaFaturamentoOS = None


class CentralFaturamentoERP:

  def __init__(self, root):
    self.root = root
    self.root.title("Central de Automação ERP - Menu Principal")
    self.root.geometry("550x450")
    self.root.resizable(False, False)
    self.root.config(bg="#f4f6f9")

    self.criar_menu_principal()

  def criar_menu_principal(self):
    lbl_titulo = tk.Label(
        self.root,
        text="CENTRAL DE FATURAMENTO E AUTOMAÇÃO",
        font=("Arial", 14, "bold"),
        bg="#f4f6f9",
        fg="#333333",
    )
    lbl_titulo.pack(pady=25)

    lbl_sub = tk.Label(
        self.root,
        text="Selecione abaixo a rotina que deseja executar em lote:",
        font=("Arial", 10),
        bg="#f4f6f9",
        fg="#666666",
    )
    lbl_sub.pack(pady=5)

    frame_botoes = tk.Frame(self.root, bg="#f4f6f9")
    frame_botoes.pack(pady=20)

    estilo_botao = {
        "font": ("Arial", 11, "bold"),
        "fg": "white",
        "width": 35,
        "height": 2,
        "bd": 0,
        "cursor": "hand2",
    }

    # 1. Faturamento de O.S.
    btn_os = tk.Button(
        frame_botoes,
        text="1. Faturamento de O.S. (Gerar Pedidos)",
        bg="#007bff",
        command=self.abrir_modulo_os,
        **estilo_botao,
    )
    btn_os.pack(pady=10)

    # 2. Faturamento de Notas
    btn_notas = tk.Button(
        frame_botoes,
        text="2. Faturamento de Notas (NFE / NFS)",
        bg="#17a2b8",
        command=self.abrir_modulo_notas,
        **estilo_botao,
    )
    btn_notas.pack(pady=10)

    # 3. Emissão de Boletos
    estilo_boletos = estilo_botao.copy()
    estilo_boletos["fg"] = "#333333"
    btn_boletos = tk.Button(
        frame_botoes,
        text="3. Emissão de Boletos (Financeiro / FLAN)",
        bg="#ffc107",
        command=self.abrir_modulo_boletos,
        **estilo_boletos,
    )
    btn_boletos.pack(pady=10)

    # 4. Envio de Documentos
    btn_envio = tk.Button(
        frame_botoes,
        text="4. Envio de Documentos (E-mail / WhatsApp)",
        bg="#28a745",
        command=self.abrir_modulo_envio,
        **estilo_botao,
    )
    btn_envio.pack(pady=10)

  def abrir_modulo_os(self):
    if JanelaFaturamentoOS:
      JanelaFaturamentoOS(self.root)
    else:
      messagebox.showerror("Erro", "Módulo gui_modulo_os.py não encontrado na pasta modulos.")

  def abrir_modulo_notas(self):
    top = tk.Toplevel(self.root)
    top.title("Faturamento de Notas Fiscais em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Emissão e Envio de NFE e NFS", font=("Arial", 12, "bold")).pack(pady=20)

  def abrir_modulo_boletos(self):
    top = tk.Toplevel(self.root)
    top.title("Emissão de Boletos em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Boletos", font=("Arial", 12, "bold")).pack(pady=20)

  def abrir_modulo_envio(self):
    top = tk.Toplevel(self.root)
    top.title("Envio de Documentos em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Disparos via E-mail e WhatsApp", font=("Arial", 12, "bold")).pack(pady=20)


if __name__ == "__main__":
  root = tk.Tk()
  app = CentralFaturamentoERP(root)
  root.mainloop()