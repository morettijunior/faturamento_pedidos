import fdb

# --- CONFIGURAÇÕES DO BANCO FIREBIRD (TGA) ---
DB_HOST = "SERVIDOR"
DB_PORT = 3050
DB_PATH = r"c:\tga\dados\tga.fdb"
DB_USER = "SYSDBA"
DB_PASSWORD = "masterkey"


def conectar_banco():
  try:
    return fdb.connect(
        dsn=f"{DB_HOST}/{DB_PORT}:{DB_PATH}",
        user=DB_USER,
        password=DB_PASSWORD,
        charset="ISO8859_1",
    )
  except Exception as e:
    print(f"Erro ao conectar no Firebird: {e}")
    return None


def formatar_7_digitos(numero):
  """Garante o formato de 7 dígitos para busca no banco (ex: 32257 -> 0032257)"""
  if not numero:
    return ""
  return str(numero).strip().zfill(7)


def limpar_zeros(numero):
  """Remove os zeros à esquerda para nome de arquivos/exibição (ex: 0032257 -> 32257)"""
  if not numero:
    return ""
  return str(numero).strip().lstrip("0")


def consultar_dados_pedido(numero_input):
  """Consulta o banco Firebird do TGA e retorna um dicionário contendo:

  - OS (se existir)
  - NFE (se existir)
  - NFS (número da NFS-e, se existir)
  - RPS (número do RPS, se existir - usado para filtro financeiro)
  - CLIENTE (código do cliente CODCFO)
  - PARCELAS (lista detalhada dos lançamentos na FLAN)
  """
  con = conectar_banco()
  if not con:
    return None

  cursor = con.cursor()
  num_formatado = formatar_7_digitos(numero_input)
  num_limpo = limpar_zeros(numero_input)

  try:
    # 1. Busca o movimento principal na TMOV (Séries EV ou OS) incluindo CODCFO
    query_mov = """
            SELECT IDMOV, NUMEROMOV, SERIE, IDMOVRELAC, CODCFO 
            FROM TMOV 
            WHERE NUMEROMOV = ? 
              AND UPPER(TRIM(SERIE)) IN ('EV', 'OS')
        """
    cursor.execute(query_mov, (num_formatado,))
    mov_principal = cursor.fetchone()

    if not mov_principal:
      print(f"Movimento de venda {num_formatado} (Séries EV/OS) não encontrado na tabela TMOV.")
      return None

    id_mov, num_mov, serie, id_mov_relac, cod_cfo = mov_principal
    eh_os = id_mov_relac is not None

    dados = {
        "NUMERO_PEDIDO": num_limpo,
        "OS": None,
        "NFE": None,
        "NFS": None,
        "RPS": None,
        "CLIENTE": str(cod_cfo).strip() if cod_cfo else "",
        "PARCELAS": [],
    }

    # Se for O.S., busca o movimento pai/relacionado
    if eh_os:
      query_os = "SELECT NUMEROMOV, SERIE FROM TMOV WHERE IDMOV = ?"
      cursor.execute(query_os, (id_mov_relac,))
      os_relacionada = cursor.fetchone()
      if os_relacionada and os_relacionada[1].strip().upper() == "OS":
        dados["OS"] = limpar_zeros(os_relacionada[0])

    # 2. Varredura de Notas Filhas (NFE e NFS/RPS)
    query_filhos = """
            SELECT IDMOV, SERIE, NUMEROMOV 
            FROM TMOV 
            WHERE IDMOVRELAC = ?
        """
    cursor.execute(query_filhos, (id_mov,))
    filhos = cursor.fetchall()

    nfe_encontrada = None
    rps_encontrado = None

    for filho in filhos:
      f_id, f_serie, f_num = filho
      f_serie_limpa = f_serie.strip()

      if f_serie_limpa == "1":
        nfe_encontrada = f_num.strip()
        dados["NFE"] = limpar_zeros(nfe_encontrada)

      elif f_serie_limpa.upper() == "NFS":
        rps_encontrado = f_num.strip()
        dados["RPS"] = rps_encontrado  # Salva o RPS para o filtro financeiro
        query_nfse = "SELECT NUMERONFSE FROM TNFEMUNICIPAL WHERE IDMOV = ?"
        cursor.execute(query_nfse, (f_id,))
        nfse_res = cursor.fetchone()
        if nfse_res:
          dados["NFS"] = str(nfse_res[0]).strip()

    # 3. Busca das Parcelas / Boletos na FLAN
    doc_pedido = num_formatado
    nfe_com_zeros = formatar_7_digitos(nfe_encontrada) if nfe_encontrada else ""
    rps_com_zeros = formatar_7_digitos(rps_encontrado) if rps_encontrado else ""

    nfe_limpa_str = limpar_zeros(nfe_encontrada) if nfe_encontrada else ""
    rps_limpo_str = str(dados["RPS"]).strip() if dados.get("RPS") else ""
    doc_manual_unificado = (
        f"{nfe_limpa_str}/{rps_limpo_str}" if (nfe_limpa_str and rps_limpo_str) else ""
    )

    def consultar_flan(doc):
      if not doc:
        return []
      q = """
                SELECT PARCELA, NUMERODOCUMENTO, DATAVENCIMENTO, VALORORIGINAL 
                FROM FLAN 
                WHERE TRIM(NUMERODOCUMENTO) = ? 
                ORDER BY PARCELA
            """
      cursor.execute(q, (str(doc).strip(),))
      return cursor.fetchall()

    lancamentos_flan = consultar_flan(doc_pedido)
    if not lancamentos_flan:
      lancamentos_flan = consultar_flan(nfe_com_zeros)
    if not lancamentos_flan:
      lancamentos_flan = consultar_flan(rps_com_zeros)
    if not lancamentos_flan:
      lancamentos_flan = consultar_flan(doc_manual_unificado)

    vistos = set()
    for flan in lancamentos_flan:
      parcela, num_doc, dt_venc, val_orig = flan
      num_doc_limpo = num_doc.strip() if num_doc else ""
      chave_unica = (parcela, num_doc_limpo)

      if chave_unica not in vistos:
        vistos.add(chave_unica)
        dados["PARCELAS"].append({
            "PARCELA": parcela,
            "NUMERO_DOCUMENTO": num_doc_limpo,
            "VENCIMENTO": str(dt_venc) if dt_venc else None,
            "VALOR": float(val_orig) if val_orig else 0.0,
        })

    # ========================================================
    # Tratamento de consolidação para a GUI e Robô
    # ========================================================
    dados["QTDE_PARCELAS"] = len(dados["PARCELAS"])
    
    vencimentos_limpos = []
    valor_soma = 0.0

    for p in dados["PARCELAS"]:
        valor_soma += p["VALOR"]
        venc_raw = p["VENCIMENTO"]
        if venc_raw:
            try:
                dt_formatada = f"{venc_raw[8:10]}{venc_raw[5:7]}{venc_raw[0:4]}"
                vencimentos_limpos.append(dt_formatada)
            except:
                vencimentos_limpos.append(venc_raw.replace("-", "").replace("/", ""))

    dados["VENCIMENTOS"] = vencimentos_limpos
    
    dados["VALOR_TOTAL"] = f"R$ {valor_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return dados

  except Exception as e:
    print(f"Erro ao processar consulta no BD para o pedido {numero_input}: {e}")
    return None
  finally:
    con.close()


# --- BLOCO DE TESTE ISOLADO ---
if __name__ == "__main__":
  print("=== TESTE ISOLADO: CONSULTA BD TGA ===")
  pedido_teste = input("Digite o número do pedido para consultar: ")
  resultado = consultar_dados_pedido(pedido_teste)
  if resultado:
    print("\n[SUCESSO] Dados coletados:")
    for chave, valor in resultado.items():
      print(f"  {chave}: {valor}")
  else:
    print("\n[ERRO] Não foi possível recuperar os dados.")