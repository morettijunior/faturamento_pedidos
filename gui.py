import time
import tkinter as tk
from tkinter import messagebox


class AppAutomacaoERP:

  def __init__(self, root):
    self.root = root
    self.root.title("Robô de Faturamento ERP - Lote de Pedidos")
    self.root.geometry("820x660")
    self.root.resizable(False, False)

    self.linhas_gui = []
    self.criar_interface()

  def criar_interface(self):
    # Cabeçalho da Tabela Visual
    tk.Label(
        self.root, text="Nº do Pedido", font=("Arial", 10, "bold")
    ).place(x=30, y=15)
    tk.Label(
        self.root, text="Opções de Execução por Pedido", font=("Arial", 10, "bold")
    ).place(x=180, y=15)

    # Criando 20 linhas dinâmicas na tela
    y_inicial = 45
    for i in range(20):
      # Campo de texto para o número do pedido
      txt_pedido = tk.Entry(self.root, width=12, font=("Arial", 10))
      txt_pedido.place(x=30, y=y_inicial)

      # Variáveis de controle das Checkboxes
      var_nfe = tk.BooleanVar()
      var_nfs = tk.BooleanVar()
      var_boleto_cada = tk.BooleanVar()
      var_unificado = tk.BooleanVar()

      # Checkboxes com os novos textos
      chk_nfe = tk.Checkbutton(self.root, text="NFE", variable=var_nfe)
      chk_nfe.place(x=140, y=y_inicial - 2)

      chk_nfs = tk.Checkbutton(self.root, text="NFS", variable=var_nfs)
      chk_nfs.place(x=200, y=y_inicial - 2)

      chk_boleto_cada = tk.Checkbutton(
          self.root, text="BOLETO P/ CADA NOTA", variable=var_boleto_cada
      )
      chk_boleto_cada.place(x=265, y=y_inicial - 2)

      chk_unificado = tk.Checkbutton(
          self.root, text="BOLETO UNIFICADO", variable=var_unificado
      )
      chk_unificado.place(x=435, y=y_inicial - 2)

      # Armazena a referência para leitura posterior (com as novas chaves)
      self.linhas_gui.append({
          "pedido": txt_pedido,
          "nfe": var_nfe,
          "nfs": var_nfs,
          "boleto_cada": var_boleto_cada,
          "unificado": var_unificado,
      })

      # Incrementa o Y para a próxima linha
      y_inicial += 26

    # Botão de Execução Geral
    btn_executar = tk.Button(
        self.root,
        text="EXECUTAR LOTE NO ERP",
        bg="#28a745",
        fg="white",
        font=("Arial", 11, "bold"),
        command=self.iniciar_processamento,
    )
    btn_executar.place(x=30, y=575, width=755, height=40)

  def iniciar_processamento(self):
    fila_tarefas = []

    # Coleta apenas as linhas preenchidas pelo usuário
    for idx, linha in enumerate(self.linhas_gui):
      num_pedido = linha["pedido"].get().strip()
      if num_pedido:
        fila_tarefas.append({
            "linha": idx + 1,
            "pedido": num_pedido,
            "nfe": linha["nfe"].get(),
            "nfs": linha["nfs"].get(),
            "boleto_cada": linha["boleto_cada"].get(),
            "unificado": linha["unificado"].get(),
        })

    if not fila_tarefas:
      messagebox.showwarning(
          "Aviso", "Preencha pelo menos um pedido na interface!"
      )
      return

    # Inicia a esteira de automação
    self.executar_automacao_erp(fila_tarefas)

  def executar_automacao_erp(self, fila):
    relatorio_sucesso = []

    try:
      for item in fila:
        pedido = item["pedido"]
        print(f"Processando Pedido: {pedido}...")

        # ==========================================
        # AQUI ENTRARÃO OS COMANDOS DO PYAUTOGUI / PYWINAUTO
        # ==========================================
        time.sleep(1)  # Simula tempo de digitação e navegação no ERP

        num_nfe_gerada = None
        num_nfs_gerada = None

        # 1. PROCESSAMENTO DE NOTAS (NFE / NFS)
        if item["nfe"] or item["nfs"]:
          # SIMULAÇÃO DE ERRO CRÍTICO (Ex: Se digitar 999, simula queda da SEFAZ)
          if pedido == "999":
            raise Exception(
                f"SEFAZ FORA DO AR / REJEIÇÃO no Pedido {pedido}. Conexão"
                " perdida com o webservice."
            )

          # Simula notas geradas com sucesso
          if item["nfe"]:
            num_nfe_gerada = "84920"
          if item["nfs"]:
            num_nfs_gerada = "3102"

        # 2. PROCESSAMENTO DE BOLETOS (Só executa se passou pelas notas com sucesso)
        boletos_gerados = []
        if item["boleto_cada"] or item["unificado"]:
          time.sleep(1)  # Simula tempo de envio para API do banco

          tipo_gerado = (
              "BOLETO UNIFICADO" if item["unificado"] else "BOLETO P/ CADA NOTA"
          )

          # Exemplo simulando que gerou boletos
          boletos_gerados.append({
              "tipo": tipo_gerado,
              "numero": "908123-1",
              "vencimento": "20/10/2026",
              "valor": "R$ 750,00",
          })

        # SUCESSO NESTE PEDIDO: Acumula no relatório parcial
        relatorio_sucesso.append({
            "pedido": pedido,
            "nfe": num_nfe_gerada,
            "nfs": num_nfs_gerada,
            "boletos": boletos_gerados,
        })

      # Se o loop terminar sem exceções, exibe o relatório 100% concluído
      self.exibir_relatorio(
          relatorio_sucesso, "RELATÓRIO FINAL - 100% CONCLUÍDO COM SUCESSO"
      )

    except Exception as e:
      # PARADA TOTAL IMEDIATA + EXIBIÇÃO DO ERRO E DO RELATÓRIO PARCIAL
      mensagem_falha = (
          f"O robô interrompeu a esteira devido a um erro:\n\n{str(e)}\n\n"
          "--- ATENÇÃO ---\nO lote parou. Veja abaixo o relatório dos pedidos"
          " que foram processados com sucesso antes da falha:"
      )
      messagebox.showerror("ERRO CRÍTICO - LOTE INTERROMPIDO", mensagem_falha)

      if relatorio_sucesso:
        self.exibir_relatorio(
            relatorio_sucesso,
            "RELATÓRIO PARCIAL (Processado antes da falha)",
        )
      else:
        messagebox.showinfo(
            "Aviso", "Nenhum pedido foi concluído, a falha ocorreu no início."
        )

  def exibir_relatorio(self, dados, titulo_janela):
    texto_relatorio = f"=== {titulo_janela} ===\n\n"
    for item in dados:
      linha_resumo = f"PEDIDO {item['pedido']}"
      if item["nfe"]:
        linha_resumo += f" | NFE: {item['nfe']}"
      if item["nfs"]:
        linha_resumo += f" | NFS: {item['nfs']}"
      texto_relatorio += linha_resumo + "\n"

      if item["boletos"]:
        for idx, bol in enumerate(item["boletos"], 1):
          texto_relatorio += (
              f"   -> [{bol['tipo']}] Boleto {idx:02d} | Num: {bol['numero']}"
              f" | Venc: {bol['vencimento']} | Val: {bol['valor']}\n"
          )
      texto_relatorio += "-" * 70 + "\n"

    # Cria janela pop-up customizada para exibir o relatório formatado
    top = tk.Toplevel(self.root)
    top.title(titulo_janela)
    top.geometry("700x450")

    txt_box = tk.Text(top, wrap=tk.WORD, font=("Courier", 10))
    txt_box.pack(expand=True, fill="both", padx=10, pady=10)
    txt_box.insert(tk.END, texto_relatorio)
    txt_box.config(state=tk.DISABLED)


if __name__ == "__main__":
  root = tk.Tk()
  app = AppAutomacaoERP(root)
  root.mainloop()