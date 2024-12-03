# Imports
import pandas            as pd
import streamlit         as st
import numpy             as np

from datetime            import datetime
from PIL                 import Image
from io                  import BytesIO


@st.cache_data
def convert_to_csv(df):
    df.to_csv(index=False).encode('utf-8')


#Função para converter o df para excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


#Criando as funções de classificação
@st.cache_data
def rank_recency(x, r, q_dict):
    """Classifica o cliente quanto à recência.
        x = valor da recência com relação à linha avaliada
        r = recência
        q_dict = dicionário com os quantis a serem avaliados
    """
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'
    
@st.cache_data
def rank_valueorfrequency(x, p, q_dict):
    """Classifica o cliente quanto à frequência ou o valor gasto
        em suas atividades no decorrer do período avaliado.
        
        x = Valor da linha com relação ao parâmetro p
        p = 'frequencia' ou 'valor'
        q_dict = dicionário de quantis
    """
    if x <= q_dict[p][0.25]:
        return 'D'
    elif x <= q_dict[p][0.50]:
        return 'C'
    elif x <= q_dict[p][0.75]:
        return 'B'
    else:
        return 'D'

def main():
    # Configurando a base da página web:
    st.set_page_config(page_title = 'RFV', \
        layout="wide",
        initial_sidebar_state='expanded'
    )


    # Descrição da aplicação e sua funcionalidade:
    st.write('''O RFV é o método de classificação de clientes de empresas
            o qual leva em consideração 3 fatores para dividir os clientes
            com relação aos seus comportamentos como consumidores:
            o R representa a recência, ou seja, quanto tempo faz desde que o cliente
            comprou pela última vez. O F significa frequência, ou seja, o valor total
            que o cliente gastou no decorrer do intervalo de tempo avaliado. E o V
            representa o valor total gasto pelo cliente neste mesmo intervalo de tempo.
            Dada a definição destas 3 entidades, o que nosso algoritimo fará é classificar
            os clientes de acordo com em qual quartil eles se encontram com relação ao
            compilado de todos os clientes...''')

    st.markdown('---')

    # Vamos configurar uma barra lateral para o nosso aplicativo:
    image = Image.open("hmmm_stonks.jpg")
    st.sidebar.image(image)

    # Vamos criar o botão utilizado para subir os dados:
    st.sidebar.write('## Fazer Upload')
    datafile1 = st.sidebar.file_uploader('Bank Marketing Data', type = ['csv', 'xlsx'])

    # Verificando se o usuário gostaria de utilizar um setup de dados de teste:

    escolhas = ['Sim', 'Não']
    usararquivopadrao = st.selectbox('Gostaria de utilizar um arquivo padrão para ter uma amostra de como o app funciona?', escolhas, index=0)

    if usararquivopadrao == 'Sim':
        try:
            datafile1 = pd.read_excel('dados_input 1.xlsx')
        except FileNotFoundError:
            try:
                datafile1 = pd.read_csv('dados_input 1.csv')
            except FileNotFoundError:
                print('Ops! Nenhum dos arquivos foi carregado. Algo de errado aconteceu!')
        except Exception as e:
            print(f'Aconteceu algum erro insesperado. O erro inesperado foi: {e}')
    

    
    if datafile1 is not None and usararquivopadrao == "Sim":
        # Até aqui, sem erros

        # Calculando o RFV:
        datafile1['DiaCompra'] = pd.to_datetime(datafile1['DiaCompra'], infer_datetime_format=True)
        df_compras = datafile1


        st.write('## Recência (R)')

        dia_atual = df_compras['DiaCompra'].max()
        st.write(f'O dia mais recente da base de dados é: {dia_atual}')

        st.write('## Quantos dias fas desde a última compra do cliente?')
        df_recencia = df_compras.groupby('ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns= ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual-x).days)
        st.write(df_recencia)

        # Calculando a frequência:
        st.write('## Frequência (F)')
        st.write('## Quantas vezes o cliente comprou conosco?')
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia)

        # Calculando o valor
        st.write('## Valor (F)')
        st.write('## Qual foi o valor total que o cliente gastou conosco?')
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente')['ValorTotal'].sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor)

        # Tabela RFV final:
        tabela_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        tabela_RFV = tabela_RF.merge(df_valor, on='ID_cliente')
        st.write('Tabela com Recência, Frequência e Valor:')
        st.write(tabela_RFV)
        # st.text_area('Calculando a recência', """Para fazer a classificação RFV, normalmente utilizamos quartis. Os clientes no melhor quartil recebem a classificação 'A', os  clientes no segundo melhor 'B' e assim por diante. A seguir, faremos esta classificação"""
        #             , height=5)
        st.markdown("""Para fazer a classificação RFV, normalmente utilizamos quartis. Os clientes no melhor quartil recebem a classificação 'A', os  clientes no segundo melhor 'B' e assim por diante. A seguir, faremos esta classificação:""")

        # Quartis para o RFV:
        quartis = tabela_RFV.quantile(q=[.25,.5,.75])
        st.write(f'Os quartis para o RFV são: q = [0.25, 0.5, 0.75]')
        
        st.write('Tabela após a criação dos grupos:')
        tabela_RFV['R_Quartil'] = tabela_RFV['Recencia'].apply(rank_recency, args = ('Recencia', quartis))
        tabela_RFV['F_Quartil'] = tabela_RFV['Frequencia'].apply(rank_valueorfrequency, args = ('Frequencia', quartis))
        tabela_RFV['V_Quartil'] = tabela_RFV['Valor'].apply(rank_valueorfrequency, args = ('Valor', quartis))
        tabela_RFV['RFV_SCORE'] = (tabela_RFV.R_Quartil + tabela_RFV.F_Quartil + tabela_RFV.V_Quartil)
        st.write(tabela_RFV.head(10))

        st.write('Quantidade de clientes em cada grupo:')
        st.write(tabela_RFV['RFV_SCORE'].value_counts())

        st.write('Melhores clientes (Menor Recência, Maior Frequência, e Maior Valor Gasto)')
        st.write(tabela_RFV[tabela_RFV['RFV_SCORE']=='BBB'].sort_values('Valor', ascending=False))


        st.write('### Ações de Marketing/CRM')

        dict_acoes = {'DDD': 'Cliente pouco promissor em todos os critérios. Não fazer nada.',
                    'ABB': 'Cliente que comprou recentemente, e gasta uma quantia moderada e com frequencia moderada. Enviar cupons de desconto, e coletar feedbacks de melhoria',
                    'BBB': 'Cliente mediano que não compra a um pouco de tempo, mas é bom nos outros dois quesitos. Alvo prioritário para campanhas de recuperação. Oferecer cupons, ofertas, alvo prioritário para anúncios.',
                    }

        tabela_RFV['AçõesMarketing&CRM'] = tabela_RFV['RFV_SCORE'].map(dict_acoes)
        
        st.write('Tabela com as ações propostas:')
        st.write(tabela_RFV)
        st.write('Quantidade de clientes por cada tipo de ação:')
        st.write(tabela_RFV['AçõesMarketing&CRM'].value_counts())

        ## Como diria o grande filósofo brasileiro Davy Jones: por enquanto tá tudo tranquilo

    elif datafile1 is not None and usararquivopadrao == "Não":
        df_compras = pd.read_csv(datafile1, infer_datetime_format=True, parse_dates=['DiaCompra'])
        st.write(df_compras)
        
        st.write('## Recência (R)')

        dia_atual = df_compras['DiaCompra'].max()
        st.write(f'O dia mais recente da base de dados é: {dia_atual}')

        st.write('## Quantos dias fas desde a última compra do cliente?')
        df_recencia = df_compras.groupby('ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns= ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual-x).days)
        st.write(df_recencia)

        # Calculando a frequência:
        st.write('## Frequência (F)')
        st.write('## Quantas vezes o cliente comprou conosco?')
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia)

        # Calculando o valor
        st.write('## Valor (F)')
        st.write('## Qual foi o valor total que o cliente gastou conosco?')
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente')['ValorTotal'].sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor)

        # Tabela RFV final:
        tabela_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        tabela_RFV = tabela_RF.merge(df_valor, on='ID_cliente')
        st.write('Tabela com Recência, Frequência e Valor:')
        st.write(tabela_RFV)
        # st.text_area('Calculando a recência', """Para fazer a classificação RFV, normalmente utilizamos quartis. Os clientes no melhor quartil recebem a classificação 'A', os  clientes no segundo melhor 'B' e assim por diante. A seguir, faremos esta classificação"""
        #             , height=5)
        st.markdown("""Para fazer a classificação RFV, normalmente utilizamos quartis. Os clientes no melhor quartil recebem a classificação 'A', os  clientes no segundo melhor 'B' e assim por diante. A seguir, faremos esta classificação:""")

        # Quartis para o RFV:
        quartis = tabela_RFV.quantile(q=[.25,.5,.75])
        st.write(f'Os quartis para o RFV são: q = [0.25, 0.5, 0.75]')
        
        st.write('Tabela após a criação dos grupos:')
        tabela_RFV['R_Quartil'] = tabela_RFV['Recencia'].apply(rank_recency, args = ('Recencia', quartis))
        tabela_RFV['F_Quartil'] = tabela_RFV['Frequencia'].apply(rank_valueorfrequency, args = ('Frequencia', quartis))
        tabela_RFV['V_Quartil'] = tabela_RFV['Valor'].apply(rank_valueorfrequency, args = ('Valor', quartis))
        tabela_RFV['RFV_SCORE'] = (tabela_RFV.R_Quartil + tabela_RFV.F_Quartil + tabela_RFV.V_Quartil)
        st.write(tabela_RFV.head(10))

        st.write('Quantidade de clientes em cada grupo:')
        st.write(tabela_RFV['RFV_SCORE'].value_counts())

        st.write('Melhores clientes (Menor Recência, Maior Frequência, e Maior Valor Gasto)')
        st.write(tabela_RFV[tabela_RFV['RFV_SCORE']=='BBB'].sort_values('Valor', ascending=False))


        st.write('### Ações de Marketing/CRM')

        dict_acoes = {'DDD': 'Cliente pouco promissor em todos os critérios. Não fazer nada.',
                    'ABB': 'Cliente que comprou recentemente, e gasta uma quantia moderada e com frequencia moderada. Enviar cupons de desconto, e coletar feedbacks de melhoria',
                    'BBB': 'Cliente mediano que não compra a um pouco de tempo, mas é bom nos outros dois quesitos. Alvo prioritário para campanhas de recuperação. Oferecer cupons, ofertas, alvo prioritário para anúncios.',
                    }

        tabela_RFV['AçõesMarketing&CRM'] = tabela_RFV['RFV_SCORE'].map(dict_acoes)
        
        st.write('Tabela com as ações propostas:')
        st.write(tabela_RFV)
        st.write('Quantidade de clientes por cada tipo de ação:')
        st.write(tabela_RFV['AçõesMarketing&CRM'].value_counts())

    
if __name__ == '__main__':
    main()
