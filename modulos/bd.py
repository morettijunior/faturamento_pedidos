from datetime import datetime
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
  con = conectar_banco()
  if not con:
    return None

  cursor = con.cursor()
  num_formatado = formatar_7_digitos(numero_input)
  num_limpo = limpar_zeros(numero_input)

  try:
    query_mov = """
            SELECT IDMOV, NUMEROMOV, SERIE, IDMOVRELAC 
            FROM TMOV 
            WHERE NUMEROMOV = ? 
              AND UPPER(TRIM(SERIE)) IN ('EV', 'OS')
        """
    cursor.execute(query_mov, (num_formatado,))
    mov_principal = cursor.fetchone()

    if not mov_principal:
      print(f"Movimento de venda {num_formatado} não encontrado na TMOV.")
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

    if eh_os:
      query_os = "SELECT NUMEROMOV, SERIE FROM TMOV WHERE IDMOV = ?"
      cursor.execute(query_os, (id_mov_relac,))
      os_relacionada = cursor.fetchone()
      if os_relacionada and os_relacionada[1].strip().upper() == "OS":
        dados["OS"] = limpar_zeros(os_relacionada[0])

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
        dados["RPS"] = rps_encontrado
        query_nfse = "SELECT NUMERONFSE FROM TNFEMUNICIPAL WHERE IDMOV = ?"
        cursor.execute(query_nfse, (f_id,))
        nfse_res = cursor.fetchone()
        if nfse_res:
          dados["NFS"] = str(nfse_res[0]).strip()

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


def verificar_nfe_transmitida(numero_input):
  con = conectar_banco()
  if not con:
    return False
  
  cursor = con.cursor()
  num_7 = formatar_7_digitos(numero_input)
  
  try:
    q = """
        SELECT FIRST 1 T.CHAVEACESSO 
        FROM TMOV T
        JOIN TMOV R ON T.IDMOVRELAC = R.IDMOV
        WHERE R.NUMEROMOV = ? AND T.SERIE = '1'
    """
    cursor.execute(q, (num_7,))
    res = cursor.fetchone()
    if res and res[0] and str(res[0]).strip():
      return True
  except Exception as e:
    print(f"Erro ao consultar status da NFE no BD: {e}")
  finally:
    con.close()
    
  return False


def verificar_nfs_transmitida(numero_input):
  con = conectar_banco()
  if not con:
    return False
    
  cursor = con.cursor()
  num_7 = formatar_7_digitos(numero_input)
  
  try:
    q = """
        SELECT FIRST 1 F.STATUS 
        FROM TNFEMUNICIPAL F
        JOIN TMOV T ON F.IDMOV = T.IDMOV
        JOIN TMOV R ON T.IDMOVRELAC = R.IDMOV
        WHERE R.NUMEROMOV = ? AND UPPER(T.SERIE) = 'NFS'
    """
    cursor.execute(q, (num_7,))
    res = cursor.fetchone()
    if res and res[0] and str(res[0]).strip().upper() == 'E':
      return True
  except Exception as e:
    print(f"Erro ao consultar status da NFS no BD: {e}")
  finally:
    con.close()
    
  return False


def buscar_dados_os_para_lote(os_num):
  con = conectar_banco()
  if not con:
    print("[BD] Erro: Falha na conexão com o banco Firebird.")
    return None
  
  num_formatado = formatar_7_digitos(os_num)
  num_limpo = str(os_num).strip()
  
  data_encontrada = datetime.now().strftime("%d/%m/%Y")
  valor_encontrado = "0.00"
  obs_encontrada = ""
  data_encerramento = None
  ja_faturada = False
  pedido_existente = ""

  try:
    cursor = con.cursor()
    
    q = """
      SELECT FIRST 1 DATAEMISSAO, VALORBRUTO, OBSERVACAO, DATAENCERRAMENTO, IDMOV 
      FROM TMOV 
      WHERE (NUMEROMOV = ? OR NUMEROMOV = ?) AND UPPER(TRIM(SERIE)) = 'OS'
    """
    cursor.execute(q, (num_formatado, num_limpo))
    res = cursor.fetchone()
    
    if res:
      if res[0]:
        data_encontrada = res[0].strftime("%d/%m/%Y") if hasattr(res[0], 'strftime') else str(res[0])[:10]
      if res[1]:
        valor_encontrado = str(res[1])
      if res[2]:
        obs_val = res[2]
        if isinstance(obs_val, bytes):
          obs_encontrada = obs_val.decode('iso-8859-1', errors='ignore')
        else:
          obs_encontrada = str(obs_val)
      if res[3]:
        data_encerramento = res[3]
      
      idmov_os = res[4]
      
      # Busca se já virou EV e traz o NUMEROMOV do pedido gerado
      q_ev = "SELECT FIRST 1 NUMEROMOV FROM TMOV WHERE IDMOVRELAC = ? AND UPPER(TRIM(SERIE)) = 'EV'"
      cursor.execute(q_ev, (idmov_os,))
      res_ev = cursor.fetchone()
      if res_ev:
        ja_faturada = True
        pedido_existente = limpar_zeros(res_ev[0]) or str(res_ev[0]).strip()

    else:
      print(f"[BD] O.S. '{os_num}' não encontrada na TMOV.")
      return None

    return {
        "data": data_encontrada,
        "valor": valor_encontrado,
        "obs": obs_encontrada,
        "encerrada": data_encerramento is not None,
        "ja_faturada": ja_faturada,
        "pedido_ev": pedido_existente
    }

  except Exception as ex:
    print(f"[BD ERRO] Falha ao consultar O.S. {os_num}: {ex}")
    return None
  finally:
    con.close()


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

def verificar_os_ja_faturada(os_num):
  """Verifica se a O.S. informada já foi convertida em um Pedido (EV).
  Retorna True se já existir um EV relacionado a esta O.S., caso contrário False.
  """
  con = conectar_banco()
  if not con:
    return False
  
  num_formatado = formatar_7_digitos(os_num)
  num_limpo = str(os_num).strip()
  
  cursor = con.cursor()
  try:
    # 1. Busca o IDMOV da O.S. original
    q_os = "SELECT IDMOV FROM TMOV WHERE (NUMEROMOV = ? OR NUMEROMOV = ?) AND UPPER(TRIM(SERIE)) = 'OS'"
    cursor.execute(q_os, (num_formatado, num_limpo))
    res_os = cursor.fetchone()
    
    if not res_os:
      return False  # Se não achar a OS aqui, a validação de existência tratará
    
    idmov_os = res_os[0]
    
    # 2. Verifica se já existe um movimento filho (EV) vinculado a este IDMOV
    q_ev = "SELECT FIRST 1 IDMOV FROM TMOV WHERE IDMOVRELAC = ? AND UPPER(TRIM(SERIE)) = 'EV'"
    cursor.execute(q_ev, (idmov_os,))
    res_ev = cursor.fetchone()
    
    return res_ev is not None
  except Exception as e:
    print(f"Erro ao verificar se O.S. já foi faturada: {e}")
    return False
  finally:
    con.close()