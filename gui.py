import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

# Pega o caminho exato da pasta raiz do projeto e adiciona os módulos ao path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "modulos"))

# Importações de todos os módulos reais
from modulos.bd import consultar_dados_pedido, consultar_detalhes_boletos
from modulos.nfe import emitir_nfe
from modulos.envio_nfe import enviar_nfe
from modulos.nfs import emitir_nfs
from modulos.envio_nfs import enviar_nfs
from modulos.boleto_sem_nota import emitir_boleto_sem_nota
from modulos.boleto_com_nota_unica import emitir_boletos_com_nota_unica
from modulos.boleto_individual_com_notas import emitir_boletos_individuais_com_notas
from modulos.boleto_unificado_com_notas import emitir_boleto_unificado_com_notas


class AppAutomacaoERP:

  def __init__(self, root):
    self.root = root
    self.root.title("Robô de Faturamento ERP - Lote de Pedidos")
    self.root.geometry("820x660")
    self.root.resizable(False, False)

    self.linhas_gui = []
    self.historico_logs = []
    self.criar_interface()

  def log(self, mensagem):
    timestamp = time.strftime("%H:%M:%S")
    texto_formatado = f"[{timestamp}] {mensagem}"
    self.historico_logs.append(texto_formatado)
    print(texto_formatado)

  def criar_interface(self):
    tk.Label(
        self.root, text="Nº do Pedido", font=("Arial", 10, "bold")
    ).place(x=30, y=15)
    tk.Label(
        self.root, text="Opções de Execução por Pedido", font=("Arial", 10, "bold")
    ).place(x=180, y=15)

    y_inicial = 45
    for i in range(20):
      txt_pedido = tk.Entry(self.root, width=12, font=("Arial", 10))
      txt_pedido.place(x=30, y=y_inicial)

      var_nfe = tk.BooleanVar()
      var_nfs = tk.BooleanVar()
      var_boleto_cada = tk.BooleanVar()
      var_unificado = tk.BooleanVar()

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

      self.linhas_gui.append({
          "pedido": txt_pedido,
          "nfe": var_nfe,
          "nfs": var_nfs,
          "boleto_cada": var_boleto_cada,
          "unificado": var_unificado,
      })

      y_inicial += 26

    btn_executar = tk.Button(
        self.root,
        text="EXECUTAR LOTE NO ERP",
        bg="#28a745",
        fg="white",
        font=("Arial", 11, "bold"),
        command=self.iniciar_processamento,
    )
    btn_executar.place(x=30, y=575, width=660, height=40)

    btn_log = tk.Button(
        self.root,
        text="LOG",
        bg="#6c757d",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.exibir_janela_log,
    )
    btn_log.place(x=705, y=575, width=80, height=40)

  def exibir_janela_log(self):
    top = tk.Toplevel(self.root)
    top.title("Histórico de Logs - Bastidores do Robô")
    top.geometry("750x500")

    txt_log = tk.Text(
        top, wrap=tk.WORD, font=("Courier", 9), bg="#1e1e1e", fg="#00ff00"
    )
    txt_log.pack(expand=True, fill="both", padx=10, pady=10)

    if not self.historico_logs:
      txt_log.insert(tk.END, "Nenhum log registrado ainda.")
    else:
      for log_msg in self.historico_logs:
        txt_log.insert(tk.END, log_msg + "\n")

    txt_log.config(state=tk.DISABLED)

  def iniciar_processamento(self):
    fila_tarefas = []
    self.log("=== INÍCIO DA VARREDURA DA INTERFACE ===")

    for idx, linha in enumerate(self.linhas_gui):
      num_pedido = linha["pedido"].get().strip()
      if num_pedido:
        nfe = linha["nfe"].get()
        nfs = linha["nfs"].get()
        boleto_cada = linha["boleto_cada"].get()
        unificado = linha["unificado"].get()

        if not nfe and not nfs and not boleto_cada and not unificado:
          erro_msg = (
              f"Validação Falhou na Linha {idx + 1} (Pedido {num_pedido}):"
              " Nenhuma opção selecionada."
          )
          self.log(f"[ERRO] {erro_msg}")
          messagebox.showerror("Erro de Validação", erro_msg)
          return

        if boleto_cada and unificado:
          erro_msg = (
              f"Validação Falhou na Linha {idx + 1} (Pedido {num_pedido}):"
              " Conflito de boletos marcados simultaneamente."
          )
          self.log(f"[ERRO] {erro_msg}")
          messagebox.showerror("Erro de Validação", erro_msg)
          return

        self.log(
            f"Pedido {num_pedido} (Linha {idx + 1}) adicionado à fila | NFE:"
            f" {nfe} | NFS: {nfs} | Boleto Cada: {boleto_cada} | Unificado:"
            f" {unificado}"
        )
        fila_tarefas.append({
            "linha": idx + 1,
            "pedido": num_pedido,
            "nfe": nfe,
            "nfs": nfs,
            "boleto_cada": boleto_cada,
            "unificado": unificado,
        })

    if not fila_tarefas:
      self.log("[AVISO] Nenhum pedido preenchido na interface.")
      messagebox.showwarning(
          "Aviso", "Preencha pelo menos um pedido na interface!"
      )
      return

    self.log(f"Total de pedidos na fila de execução: {len(fila_tarefas)}")
    self.executar_automacao_erp(fila_tarefas)

  def executar_automacao_erp(self, fila):
    relatorio_sucesso = []
    self.log("=== INICIANDO ESTEIRA DE AUTOMAÇÃO REAL NO ERP ===")

    try:
      for item in fila:
        pedido = item["pedido"]
        self.log(f"--- Processando Pedido: {pedido} ---")

        num_nfe_gerada = None
        num_nfs_gerada = None
        boletos_gerados = []

        # =========================================================================
        # ETAPA 1: GERAÇÃO E ENVIO DE NOTAS FISCAIS
        # =========================================================================
        if item["nfe"]:
          self.log(f"[{pedido}] [1/4] Gerando NFE (nfe.py)...")
          emitir_nfe(pedido)
          time.sleep(1.0)

          self.log(f"[{pedido}] [2/4] Enviando NFE para a SEFAZ (envio_nfe.py)...")
          enviar_nfe(pedido)
          num_nfe_gerada = "Enviada"
          time.sleep(1.0)

        if item["nfs"]:
          self.log(f"[{pedido}] [3/4] Gerando NFS (nfs.py)...")
          emitir_nfs(pedido)
          time.sleep(1.0)

          self.log(f"[{pedido}] [4/4] Enviando NFS para a Prefeitura (envio_nfs.py)...")
          enviar_nfs(pedido)
          num_nfs_gerada = "Enviada"
          time.sleep(1.0)

        if item["nfe"] or item["nfs"]:
          self.log(f"[{pedido}] [ETAPA 1 CONCLUÍDA] Notas geradas e transmitidas.")
          time.sleep(1.5)

        # =========================================================================
        # ETAPA 2: EMISSÃO DE BOLETOS
        # =========================================================================
        if item["boleto_cada"] or item["unificado"]:
          self.log(f"[{pedido}] [ETAPA 2] Consultando dados no banco (bd.py) para o financeiro...")
          dados_bd = consultar_dados_pedido(pedido)

          if not dados_bd:
            raise Exception(
                f"Pedido {pedido} não foi encontrado no Banco de Dados (bd.py) para emissão de boleto."
            )

          nfe_bd = dados_bd.get("NFE")
          rps_bd = dados_bd.get("RPS")
          nfs_bd = dados_bd.get("NFS")
          vencimentos = dados_bd.get("VENCIMENTOS", [])

          tipo_boleto = ""
          tipo_rotina_bd = ""

          if item["unificado"]:
            self.log(f"[{pedido}] Acionando BOLETO UNIFICADO...")
            emitir_boleto_unificado_com_notas(pedido)
            tipo_boleto = "BOLETO UNIFICADO"
            tipo_rotina_bd = "unificado"
          else:
            self.log(f"[{pedido}] Analisando tipo de BOLETO P/ CADA NOTA...")
            if nfe_bd and rps_bd:
              self.log(f"[{pedido}] Pedido com múltiplas notas. Acionando individuais...")
              emitir_boletos_individuais_com_notas(pedido)
              tipo_rotina_bd = "individual"
            elif nfe_bd or rps_bd:
              self.log(f"[{pedido}] Pedido com nota única. Acionando nota única...")
              emitir_boletos_com_nota_unica(pedido)
              tipo_rotina_bd = "nota_unica"
            else:
              self.log(f"[{pedido}] Pedido sem nota. Acionando boleto sem nota...")
              emitir_boleto_sem_nota(pedido)
              tipo_rotina_bd = "sem_nota"
            tipo_boleto = "BOLETO P/ CADA NOTA"

          if nfe_bd: num_nfe_gerada = str(nfe_bd)
          if rps_bd: num_nfs_gerada = str(rps_bd)

          # =====================================================================
          # PÓS-CONSULTA: BUSCANDO DETALHES DE CADA BOLETO NA FLAN
          # =====================================================================
          self.log(f"[{pedido}] Consultando detalhes dos boletos na FLAN por parcela...")
          time.sleep(2.0)  # Pausa para consolidação no Firebird
          
          detalhes_boletos = consultar_detalhes_boletos(pedido, tipo_rotina=tipo_rotina_bd, nfe=nfe_bd, rps=rps_bd)

          # Documento de origem padrão caso fallback
          if item["unificado"]:
            partes_doc = []
            if nfe_bd: partes_doc.append(f"NFE: {nfe_bd}")
            if nfs_bd or rps_bd: partes_doc.append(f"NFS: {nfs_bd or rps_bd}")
            doc_origem_fallback = " / ".join(partes_doc) if partes_doc else f"Pedido: {pedido}"
          else:
            if nfe_bd and not (nfs_bd or rps_bd):
              doc_origem_fallback = f"NFE: {nfe_bd}"
            elif (nfs_bd or rps_bd) and not nfe_bd:
              doc_origem_fallback = f"NFS: {nfs_bd or rps_bd}"
            elif nfe_bd and (nfs_bd or rps_bd):
              doc_origem_fallback = f"NFE: {nfe_bd} / NFS: {nfs_bd or rps_bd}"
            else:
              doc_origem_fallback = f"Pedido: {pedido}"

          if detalhes_boletos:
            for bol in detalhes_boletos:
              valor_formatado = f"R$ {bol['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
              doc_origem_item = bol["documento_origem"] if bol["documento_origem"] else doc_origem_fallback

              boletos_gerados.append({
                  "tipo": tipo_boleto,
                  "numero": f"Num: {doc_origem_item} | Boleto Nº: {bol['numero_boleto']}",
                  "vencimento": bol["vencimento"],
                  "valor": valor_formatado,
              })
          else:
            # Fallback caso não retorne na pós-consulta
            boletos_gerados.append({
                "tipo": tipo_boleto,
                "numero": f"Num: {doc_origem_fallback} | Boleto Nº: Não Capturado",
                "vencimento": vencimentos[0] if vencimentos else "A definir",
                "valor": dados_bd.get("VALOR_TOTAL", "R$ 0,00"),
            })

          self.log(f"[{pedido}] [ETAPA 2 CONCLUÍDA] Boletos mapeados com sucesso no relatório.")

        # Consolida o sucesso do pedido
        relatorio_sucesso.append({
            "pedido": pedido,
            "nfe": num_nfe_gerada,
            "nfs": num_nfs_gerada,
            "boletos": boletos_gerados,
        })
        self.log(f"[{pedido}] Ciclo do pedido 100% finalizado com êxito.")

      self.log("=== LOTE CONCLUÍDO COM SUCESSO 100% ===")
      self.exibir_relatorio(
          relatorio_sucesso, "RELATÓRIO FINAL - 100% CONCLUÍDO COM SUCESSO"
      )

    except Exception as e:
      self.log(f"[FALHA CRÍTICA] O lote foi interrompido: {str(e)}")
      mensagem_falha = (
          f"O robô interrompeu a esteira devido a um erro:\n\n{str(e)}\n\n"
          "--- ATENÇÃO ---\nO lote parou. Veja abaixo o relatório dos pedidos"
          " processados com sucesso antes da falha:"
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
      linha_resumo = f"NÚMERO PEDIDO: {item['pedido']}"
      if item["nfe"]:
        linha_resumo += f" | NFE: {item['nfe']}"
      if item["nfs"]:
        linha_resumo += f" | NFS: {item['nfs']}"
      texto_relatorio += linha_resumo + "\n"

      if item["boletos"]:
        for idx, bol in enumerate(item["boletos"], 1):
          texto_relatorio += (
              f"    -> Boleto {idx:02d} | Num: {bol['numero']}"
              f" | Venc: {bol['vencimento']} | Val: {bol['valor']}\n"
          )
      else:
        texto_relatorio += "    -> Nenhum boleto emitido para este pedido.\n"

      texto_relatorio += "-" * 70 + "\n"

    top = tk.Toplevel(self.root)
    top.title(titulo_janela)
    top.geometry("720x480")

    txt_box = tk.Text(top, wrap=tk.WORD, font=("Courier", 10))
    txt_box.pack(expand=True, fill="both", padx=10, pady=10)
    txt_box.insert(tk.END, texto_relatorio)
    txt_box.config(state=tk.DISABLED)


if __name__ == "__main__":
  root = tk.Tk()
  app = AppAutomacaoERP(root)
  root.mainloop()