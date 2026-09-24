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
  - PARCELAS (lista detalhada dos lançamentos na FLAN)
  """
  con = conectar_banco()
  if not con:
    return None

  cursor = con.cursor()
  num_formatado = formatar_7_digitos(numero_input)
  num_limpo = limpar_zeros(numero_input)

  try:
    # 1. Busca o movimento principal na TMOV (Séries EV ou OS)
    query_mov = """
            SELECT IDMOV, NUMEROMOV, SERIE, IDMOVRELAC 
            FROM TMOV 
            WHERE NUMEROMOV = ? 
              AND UPPER(TRIM(SERIE)) IN ('EV', 'OS')
        """
    cursor.execute(query_mov, (num_formatado,))
    mov_principal = cursor.fetchone()

    if not mov_principal:
      print(f"Movimento de venda {num_formatado} (Séries EV/OS) não encontrado na tabela TMOV.")
      return None

    id_mov, num_mov, serie, id_mov_relac = mov_principal
    eh_os = id_mov_relac is not None

    dados = {
        "NUMERO_PEDIDO": num_limpo,
        "OS": None,
        "NFE": None,
        "NFS": None,
        "RPS": None,
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

    # Tratamento de consolidação para a GUI e Robô
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


def consultar_detalhes_boletos(numero_input, tipo_rotina, nfe=None, rps=None):
  """Consulta detalhada na FLAN retornando para cada parcela o seu BOL_NUMERO, vencimento e valor."""
  con = conectar_banco()
  if not con:
    return []

  cursor = con.cursor()
  num_formatado = formatar_7_digitos(numero_input)

  def buscar_detalhes_por_doc(doc_str):
    if not doc_str:
      return []
    doc_str_clean = str(doc_str).strip()
    
    if "/" not in doc_str_clean and len(doc_str_clean) <= 7:
      doc_7 = formatar_7_digitos(doc_str_clean)
      # Usa estritamente PARCELA (conforme sua estrutura da FLAN)
      q = """
                SELECT PARCELA, NUMERODOCUMENTO, DATAVENCIMENTO, VALORORIGINAL, BOL_NUMERO 
                FROM FLAN 
                WHERE (TRIM(NUMERODOCUMENTO) = ? OR TRIM(NUMERODOCUMENTO) = ?) 
                  AND BOL_NUMERO IS NOT NULL
                ORDER BY PARCELA
            """
      try:
        cursor.execute(q, (doc_7, doc_str_clean))
        res = cursor.fetchall()
        if res:
          return res
      except Exception:
        q_alt = """
                    SELECT PARCELA, NUMERODOCUMENTO, DATAVENCIMENTO, VALORORIGINAL, BOL_NUMERO 
                    FROM FLAN 
                    WHERE (TRIM(NUMERODOCUMENTO) = ? OR TRIM(NUMERODOCUMENTO) = ?) 
                      AND BOL_NUMERO IS NOT NULL
                    ORDER BY PARCELA
                """
        cursor.execute(q_alt, (doc_7, doc_str_clean))
        res = cursor.fetchall()
        if res:
          return res
    else:
      q = """
                SELECT PARCELA, NUMERODOCUMENTO, DATAVENCIMENTO, VALORORIGINAL, BOL_NUMERO 
                FROM FLAN 
                WHERE TRIM(NUMERODOCUMENTO) = ? 
                  AND BOL_NUMERO IS NOT NULL
                ORDER BY PARCELA
            """
      try:
        cursor.execute(q, (doc_str_clean,))
        res = cursor.fetchall()
        if res:
          return res
      except Exception:
        q_alt = """
                    SELECT PARCELA, NUMERODOCUMENTO, DATAVENCIMENTO, VALORORIGINAL, BOL_NUMERO 
                    FROM FLAN 
                    WHERE TRIM(NUMERODOCUMENTO) = ? 
                      AND BOL_NUMERO IS NOT NULL
                    ORDER BY PARCELA
                """
        cursor.execute(q_alt, (doc_str_clean,))
        res = cursor.fetchall()
        if res:
          return res
          
    return []

  resultados = []

  if tipo_rotina == "nota_unica":
    doc_alvo = nfe if nfe else rps
    resultados = buscar_detalhes_por_doc(doc_alvo)

  elif tipo_rotina == "individual":
    if nfe:
      resultados.extend(buscar_detalhes_por_doc(nfe))
    if rps:
      resultados.extend(buscar_detalhes_por_doc(rps))

  elif tipo_rotina == "sem_nota":
    resultados = buscar_detalhes_por_doc(num_formatado)

  elif tipo_rotina == "unificado":
    nfe_7 = formatar_7_digitos(nfe) if nfe else ""
    rps_7 = formatar_7_digitos(rps) if rps else ""
    doc_combinado_7 = f"{nfe_7}/{rps_7}" if (nfe_7 and rps_7) else ""
    doc_combinado_limpo = f"{nfe}/{rps}" if (nfe and rps) else ""

    resultados = buscar_detalhes_por_doc(doc_combinado_7)
    if not resultados and doc_combinado_limpo:
      resultados = buscar_detalhes_por_doc(doc_combinado_limpo)

  con.close()

  lista_boletos_formatada = []
  for row in resultados:
    parc, num_doc, dt_venc, val_orig, bol_num = row
    if bol_num:
      venc_str = str(dt_venc) if dt_venc else ""
      if len(venc_str) >= 10:
        venc_formatado = f"{venc_str[8:10]}/{venc_str[5:7]}/{venc_str[0:4]}"
      else:
        venc_formatado = venc_str or "A definir"

      lista_boletos_formatada.append({
          "parcela": parc,
          "documento_origem": num_doc.strip() if num_doc else "",
          "numero_boleto": str(bol_num).strip(),
          "vencimento": venc_formatado,
          "valor": float(val_orig) if val_orig else 0.0
      })

  return lista_boletos_formatada


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