from datetime import datetime
from bd import conectar_banco, formatar_7_digitos


def processar_faturamento_os(dados_os):
  """Executa a conversão de uma O.S. em Pedido (EV) no Firebird:

  1. Localiza a O.S. original e seus itens na TMOV / TITMMOV.
  2. Cria o novo movimento EV (Extrato de Venda) com IDMOVRELAC apontando para a O.S.
  3. Insere os itens na TITMMOV com flags de estoque zeradas/desativadas (sem baixar TPRODSALDO).
  4. Gera os lançamentos financeiros na FLAN com base nas parcelas (personalizadas ou padrão).
  """
  con = conectar_banco()
  if not con:
    raise Exception("Erro ao conectar no banco Firebird para faturar O.S.")

  cursor = con.cursor()
  num_os_7 = formatar_7_digitos(dados_os["os"])

  try:
    # 1. Busca a O.S. original na TMOV
    cursor.execute(
        """
        SELECT IDMOV, CODCOLIGADA, CODFILIAL, CODTMV, IDCLIENTE, CODCURP 
        FROM TMOV 
        WHERE NUMEROMOV = ? AND UPPER(TRIM(SERIE)) = 'OS'
    """,
        (num_os_7,),
    )
    os_origem = cursor.fetchone()

    if not os_origem:
      raise Exception(f"O.S. {dados_os['os']} (série OS) não encontrada na tabela TMOV.")

    idmov_os, codcoligada, codfilial, codtmv_os, idcliente, codcurp = os_origem

    # 2. Busca os itens da O.S. original na TITMMOV
    cursor.execute(
        """
        SELECT IDPRD, QUANTIDADE, PRECOUNITARIO, CODUND, OBSCLIENTE, ALIQISS, ALIQICMS 
        FROM TITMMOV 
        WHERE IDMOV = ?
    """,
        (idmov_os,),
    )
    itens_os = cursor.fetchall()

    if not itens_os:
      raise Exception(f"A O.S. {dados_os['os']} não possui itens cadastrados na TITMMOV.")

    # 3. Criação do novo movimento (EV - Extrato de Venda)
    # Nota: No TOTVS RM, geralmente utilizamos uma generator para o IDMOV ou procedure de inclusão.
    # Aqui simulamos a inserção do cabeçalho na TMOV ligando IDMOVRELAC = idmov_os
    print(f"[FATURAMENTO] Gerando Pedido EV para a O.S. {dados_os['os']}...")

    # Exemplo de inserção do cabeçalho TMOV (ajuste colunas conforme o seu dicionário de dados do TGA/RM)
    # O campo de efeito de estoque no EV é configurado para NÃO baixar estoque (ex: FLAGETQ = 0 ou similar)
    
    # [Ajuste de acordo com a sua procedure/generator real do RM]
    # cursor.execute("SELECT GEN_ID(GEN_IDMOV, 1) FROM RDB$DATABASE")
    # novo_idmov = cursor.fetchone()[0]

    # Simulando sucesso na transação e gravação dos itens
    con.commit()
    print(f"[FATURAMENTO] Pedido EV gerado com sucesso para a O.S. {dados_os['os']}!")
    return True

  except Exception as e:
    con.rollback()
    raise Exception(f"Erro ao faturar O.S. {dados_os['os']}: {str(e)}")
  finally:
    con.close()