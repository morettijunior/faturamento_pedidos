import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

# Configuração de caminhos
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "modulos"))

try:
    from modulos.bd import conectar_banco, buscar_dados_os_para_lote
except ImportError:
    conectar_banco = None
    buscar_dados_os_para_lote = None

try:
    from modulos.faturar_pedido import processar_faturamento_os
except ImportError:
    processar_faturamento_os = None


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
        command=self.abrir_janela_faturamento_os,
        **estilo_botao,
    )
    btn_os.pack(pady=10)

    # 2. Faturamento de Notas
    btn_notas = tk.Button(
        frame_botoes,
        text="2. Faturamento de Notas (NFE / NFS)",
        bg="#17a2b8",
        command=self.abrir_janela_faturamento_notas,
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
        command=self.abrir_janela_emissao_boletos,
        **estilo_boletos,
    )
    btn_boletos.pack(pady=10)

    # 4. Envio de Documentos
    btn_envio = tk.Button(
        frame_botoes,
        text="4. Envio de Documentos (E-mail / WhatsApp)",
        bg="#28a745",
        command=self.abrir_janela_envio_documentos,
        **estilo_botao,
    )
    btn_envio.pack(pady=10)

  # --- MÓDULO 1: FATURAMENTO DE O.S. EM LOTE ---
  def abrir_janela_faturamento_os(self):
    top = tk.Toplevel(self.root)
    top.title("Faturamento de O.S. em Lote (EV)")
    top.geometry("1120x650")
    top.resizable(False, False)
    top.config(bg="#f8f9fa")

    # Garante que ao fechar a subjanela, voltamos para o menu principal limpo e sem recriar nada indevido
    top.transient(self.root)

    tk.Label(
        top, text="Módulo de Faturamento de O.S. em Lote (Até 10 Pedidos)", 
        font=("Arial", 12, "bold"), bg="#f8f9fa", fg="#1d3557"
    ).pack(pady=10)

    # Cabeçalhos com azul corporativo forte (#1d3557) e texto branco
    frame_cab = tk.Frame(top, bg="#1d3557", padx=5, pady=8)
    frame_cab.pack(fill="x", padx=15)

    tk.Label(frame_cab, text="Nº O.S.", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=10, anchor="w").grid(row=0, column=0, padx=2)
    tk.Label(frame_cab, text="DATA EMISSÃO", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=12, anchor="center").grid(row=0, column=1, padx=2)
    tk.Label(frame_cab, text="VALOR FINAL (R$)", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=14, anchor="center").grid(row=0, column=2, padx=2)
    tk.Label(frame_cab, text="PARCELAS", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=18, anchor="center").grid(row=0, column=3, padx=2)
    tk.Label(frame_cab, text="OBSERVAÇÕES (Enter para nova linha)", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=35, anchor="w").grid(row=0, column=4, padx=2)
    tk.Label(frame_cab, text="PERSONALIZAR", font=("Arial", 9, "bold"), bg="#1d3557", fg="white", width=15, anchor="center").grid(row=0, column=5, padx=2)

    # Canvas com Scroll para as 10 linhas
    container = tk.Frame(top, bg="#f8f9fa")
    container.pack(fill="both", expand=True, padx=15, pady=5)

    canvas = tk.Canvas(container, bg="#f8f9fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#f8f9fa")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    opcoes_parcelas = [
        "30 DIAS",
        "30/60 DIAS",
        "30/60/90 DIAS",
        "20/40 DIAS",
        "20/40/60 DIAS",
        "30/60/90/120 DIAS"
    ]

    linhas_dados = []

    for i in range(10):
      cor_fundo = "#ffffff" if i % 2 == 0 else "#e3f2fd"

      row_frame = tk.Frame(scroll_frame, bg=cor_fundo, pady=5, padx=4, relief="solid", bd=1)
      row_frame.pack(fill="x", pady=2)

      # 1. Nº O.S.
      txt_os = tk.Entry(row_frame, width=11, font=("Arial", 10, "bold"), bg="#ffffff")
      txt_os.grid(row=0, column=0, padx=2)

      # 2. Data Emissão
      txt_data = tk.Entry(row_frame, width=12, font=("Arial", 10), justify="center", bg="#ffffff")
      txt_data.grid(row=0, column=1, padx=2)

      # 3. Valor Final
      txt_valor = tk.Entry(row_frame, width=14, font=("Arial", 10, "bold"), justify="center", bg="#ffffff")
      txt_valor.grid(row=0, column=2, padx=2)

      # 4. Parcelas (Combobox)
      combo_parc = ttk.Combobox(row_frame, values=opcoes_parcelas, width=16, state="readonly", font=("Arial", 9))
      combo_parc.grid(row=0, column=3, padx=2)
      combo_parc.set("30 DIAS")

      # 5. Observações (Text widget)
      txt_obs = tk.Text(row_frame, width=38, height=2, font=("Arial", 9), wrap="word", bg="#ffffff")
      txt_obs.grid(row=0, column=4, padx=2)

      parcelas_customizadas_linha = []
      ultimo_valor_buscado = {"os": ""}

      # Função para carregar dados do banco ao sair do campo O.S. ou apertar Enter
      def carregar_dados_os(e, t_os=txt_os, t_dt=txt_data, t_val=txt_valor, t_obs=txt_obs, cache=ultimo_valor_buscado):
        os_num = t_os.get().strip()
        if not os_num:
          cache["os"] = ""
          return
        
        # Evita execução duplicada gerada simultaneamente por FocusOut e Return
        if cache["os"] == os_num:
          return
        cache["os"] = os_num

        data_encontrada = datetime.now().strftime("%d/%m/%Y")
        valor_encontrado = "0.00"
        obs_encontrada = ""

        if buscar_dados_os_para_lote:
          dados_db = buscar_dados_os_para_lote(os_num)
          if dados_db:
            # Validação 1: O.S. precisa estar encerrada
            if not dados_db["encerrada"]:
              messagebox.showerror("Erro de Validação", f"O.S. {os_num} DEVE SER ENCERRADA ANTES DE FATURADA.", parent=top)
              cache["os"] = ""
              t_os.delete(0, tk.END)
              t_os.focus_set()
              return
            
            # Validação 2: O.S. não pode já ter sido faturada (Exibe o número do pedido EV existente)
            if dados_db["ja_faturada"]:
              pedido_num = dados_db.get("pedido_ev", "EV")
              messagebox.showerror("Erro de Validação", f"O.S. {os_num} JÁ FOI FATURADA (PEDIDO {pedido_num} JÁ EXISTENTE).", parent=top)
              cache["os"] = ""
              t_os.delete(0, tk.END)
              t_os.focus_set()
              return
            
            data_encontrada = dados_db["data"]
            valor_encontrado = dados_db["valor"]
            obs_encontrada = dados_db["obs"]
          else:
            messagebox.showwarning("Aviso", f"O.S. {os_num} não foi encontrada no banco de dados.", parent=top)
            cache["os"] = ""
            t_os.delete(0, tk.END)
            t_os.focus_set()
            return

        t_dt.delete(0, tk.END)
        t_dt.insert(0, data_encontrada)
        t_val.delete(0, tk.END)
        t_val.insert(0, valor_encontrado)
        t_obs.delete("1.0", tk.END)
        t_obs.insert("1.0", obs_encontrada)

      txt_os.bind("<FocusOut>", carregar_dados_os)
      txt_os.bind("<Return>", carregar_dados_os)

      # 6. Botão Personalizar Parcelas
      def abrir_personalizar(t_val=txt_valor, t_dt=txt_data, c_parc=combo_parc, ref_list=parcelas_customizadas_linha, num_linha=i+1):
        try:
          val_str = t_val.get().strip().replace("R$", "").replace(".", "").replace(",", ".").strip()
          valor_total = float(val_str) if val_str else 0.0
        except ValueError:
          messagebox.showerror("Erro", f"Valor final inválido na linha {num_linha}.", parent=top)
          return

        condicao = c_parc.get()
        data_base_str = t_dt.get().strip()
        try:
          data_base = datetime.strptime(data_base_str, "%d/%m/%Y")
        except ValueError:
          data_base = datetime.now()

        dias_map = {
            "30 DIAS": [30],
            "30/60 DIAS": [30, 60],
            "30/60/90 DIAS": [30, 60, 90],
            "20/40 DIAS": [20, 40],
            "20/40/60 DIAS": [20, 40, 60],
            "30/60/90/120 DIAS": [30, 60, 90, 120]
        }
        dias = dias_map.get(condicao, [30])
        qtd = len(dias)

        sub = tk.Toplevel(top)
        sub.title(f"Personalizar Parcelas - Linha {num_linha}")
        sub.geometry("450x380")
        sub.resizable(False, False)
        sub.grab_set()

        tk.Label(sub, text=f"Editando Parcelas (Linha {num_linha})", font=("Arial", 10, "bold")).pack(pady=10)

        columns = ("parcela", "vencimento", "valor")
        tree = ttk.Treeview(sub, columns=columns, show="headings", height=5)
        tree.heading("parcela", text="Nº Parcela")
        tree.heading("vencimento", text="Vencimento")
        tree.heading("valor", text="Valor (R$)")
        tree.column("parcela", width=80, anchor="center")
        tree.column("vencimento", width=150, anchor="center")
        tree.column("valor", width=160, anchor="center")
        tree.pack(pady=5)

        if ref_list and len(ref_list) == qtd:
          dados_parcelas = ref_list
        else:
          dados_parcelas = []
          valor_parcela = round(valor_total / qtd, 2)
          soma_parc = 0.0
          for idx, d in enumerate(dias):
            venc = data_base + timedelta(days=d)
            if idx == qtd - 1:
              val_atual = round(valor_total - soma_parc, 2)
            else:
              val_atual = valor_parcela
              soma_parc += val_atual
            dados_parcelas.append({
                "num": idx + 1,
                "vencimento": venc.strftime("%d/%m/%Y"),
                "valor": f"{val_atual:.2f}".replace(".", ",")
            })

        for item in dados_parcelas:
          tree.insert("", tk.END, values=(f"Parcela {item['num']}", item["vencimento"], item["valor"]))

        frame_edit = tk.Frame(sub)
        frame_edit.pack(pady=10)

        tk.Label(frame_edit, text="Venc.:").grid(row=0, column=0, padx=2)
        ent_venc = tk.Entry(frame_edit, width=12)
        ent_venc.grid(row=0, column=1, padx=2)

        tk.Label(frame_edit, text="Valor:").grid(row=0, column=2, padx=2)
        ent_val = tk.Entry(frame_edit, width=12)
        ent_val.grid(row=0, column=3, padx=2)

        def carregar_selecao(event):
          selecionado = tree.selection()
          if selecionado:
            vals = tree.item(selecionado[0], "values")
            ent_venc.delete(0, tk.END)
            ent_venc.insert(0, vals[1])
            ent_val.delete(0, tk.END)
            ent_val.insert(0, vals[2])

        tree.bind("<<TreeviewSelect>>", carregar_selecao)

        def atualizar_linha():
          selecionado = tree.selection()
          if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma parcela na tabela.", parent=sub)
            return
          item_id = selecionado[0]
          vals = tree.item(item_id, "values")
          tree.item(item_id, values=(vals[0], ent_venc.get(), ent_val.get()))

        btn_atualizar = tk.Button(frame_edit, text="Alterar", bg="#ffc107", command=atualizar_linha)
        btn_atualizar.grid(row=0, column=4, padx=5)

        def salvar_personalizacao():
          novas = []
          for idx, child in enumerate(tree.get_children()):
            vals = tree.item(child, "values")
            novas.append({
                "num": idx + 1,
                "vencimento": vals[1],
                "valor": vals[2]
            })
          ref_list.clear()
          ref_list.extend(novas)
          messagebox.showinfo("Sucesso", "Parcelas customizadas salvas!", parent=sub)
          sub.destroy()

        btn_salvar_sub = tk.Button(sub, text="Salvar e Fechar", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=salvar_personalizacao)
        btn_salvar_sub.pack(pady=10)

      btn_pers = tk.Button(row_frame, text="Personalizar", bg="#495057", fg="white", font=("Arial", 9, "bold"), command=abrir_personalizar)
      btn_pers.grid(row=0, column=5, padx=5)

      linhas_dados.append({
          "os": txt_os,
          "data": txt_data,
          "valor": txt_valor,
          "parcelas": combo_parc,
          "obs": txt_obs,
          "custom_parcelas": parcelas_customizadas_linha
      })

    def processar_lote_os():
      tarefas = []
      for idx, linha in enumerate(linhas_dados):
        num_os = linha["os"].get().strip()
        if num_os:
          tarefas.append({
              "linha": idx + 1,
              "os": num_os,
              "data": linha["data"].get().strip(),
              "valor": linha["valor"].get().strip(),
              "condicao": linha["parcelas"].get(),
              "obs": linha["obs"].get("1.0", tk.END).strip(),
              "parcelas_personalizadas": linha["custom_parcelas"]
          })

      if not tarefas:
        messagebox.showwarning("Aviso", "Preencha pelo menos uma O.S. na tela!", parent=top)
        return

      sucessos = 0
      erros = 0
      relatorio_erros = []

      for t in tarefas:
        try:
          if processar_faturamento_os:
            processar_faturamento_os(t)
          sucessos += 1
        except Exception as ex:
          erros += 1
          relatorio_erros.append(f"Linha {t['linha']} (O.S. {t['os']}): {str(ex)}")

      msg_final = f"Processamento de Lote Finalizado!\n\n• Sucessos: {sucessos}\n• Erros: {erros}"
      if relatorio_erros:
        msg_final += "\n\nDetalhes dos Erros:\n" + "\n".join(relatorio_erros)
        messagebox.showerror("Atenção com Erros no Lote", msg_final, parent=top)
      else:
        messagebox.showinfo("Sucesso Total!", msg_final, parent=top)
        top.destroy()

    btn_exec = tk.Button(
        top, text="EXECUTAR LOTE DE O.S. NO ERP",
        bg="#28a745", fg="white", font=("Arial", 11, "bold"),
        command=processar_lote_os, height=2, width=40
    )
    btn_exec.pack(pady=15)

  def abrir_janela_faturamento_notas(self):
    top = tk.Toplevel(self.root)
    top.title("Faturamento de Notas Fiscais em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Emissão e Envio de NFE e NFS", font=("Arial", 12, "bold")).pack(pady=20)

  def abrir_janela_emissao_boletos(self):
    top = tk.Toplevel(self.root)
    top.title("Emissão de Boletos em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Boletos", font=("Arial", 12, "bold")).pack(pady=20)

  def abrir_janela_envio_documentos(self):
    top = tk.Toplevel(self.root)
    top.title("Envio de Documentos em Lote")
    top.geometry("650x550")
    tk.Label(top, text="Módulo de Disparos via E-mail e WhatsApp", font=("Arial", 12, "bold")).pack(pady=20)


if __name__ == "__main__":
  root = tk.Tk()
  app = CentralFaturamentoERP(root)
  root.mainloop()