#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os
import numpy as np
import re
import sys
from datetime import datetime
from datetime import timedelta
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from pathlib import Path

#Função para recortar intervalos de data solicitados pelo usuário.
def crop_dates(dataset = None, first_check=False):
    
    if first_check == True:
        
        user_ans = check_y_or_n('Você gostaria de selecionar apenas os resultados dentro uma data inicial e uma data final?')
        return (user_ans)
    
    else:            
        #Sugestão de formato: %d/%m/%Y
        user_example_format = '(dia)(dia)-(mês)(mês)-(ano)(ano)(ano)(ano)  Por ex.: 01-01-2001'
        user_time_format = '%d-%m-%Y'
        
        #Gerando uma lista de nomes de colunas que possuem dados do tipo datetime
        list_date_columns = []
        for column_name in dataset.columns:
            try:
                pd.to_datetime(dataset[column_name])
                list_date_columns.append(column_name)
                    
            except TypeError:
                continue
            except ValueError:
                continue
        list_date_columns =[column_name for column_name in dataset.columns if dataset[column_name].astype(str).str.match(r'\d{4}-\d{2}-\d{2} \d{2}\:\d{2}\:\d{2}').all()]
        
        #Se essa lista não estiver vazia:
        if len(list_date_columns) > 1:

            while True:
            
                print('Existe mais de um campo contendo datas de tipos diferentes.\n\nEscolha qual coluna a ser considerada para selecionar o intervalo de dias:\n')
            
                for i in range(len(list_date_columns)):
                    print(f'{i+1} - {list_date_columns[i]}')
                
                possible_ans = [str(k) for k in range(1, len(list_date_columns) + 1)]
                ans_date_column = input("\n\nResposta:")
                
                if ans_date_column not in possible_ans:
                    print('\nA resposta selecionada é inválida, tente novamente.\n')
                    continue
                
                else:
                    date_column_name = list_date_columns[int(ans_date_column)-1]
                    break
        
        else:
            date_column_name = list_date_columns[0]

        print("Os intervalos de tempo disponíveis são:")
        valid_dates_mask = dataset[date_column_name].notnull()
        clean_date = dataset[valid_dates_mask] #Pega as datas que não são NaN
        clean_date = clean_date.sort_values(by = date_column_name, ascending = False) #Ordena na ordem descendente
        most_recent_date = clean_date.iloc[0].loc[date_column_name] #Pega a data mais recente
        most_recent_date_str = most_recent_date.strftime(user_time_format) #Retira o objeto datetime do que seria a primeira data
        most_distant_date = clean_date.iloc[-1].loc[date_column_name] #Pega a data mais antiga
        most_distant_date_str = most_distant_date.strftime(user_time_format)
        
        while True:
            print(f"A data mais recente da coleta é: {most_recent_date_str}")
            print(f"A data mais distante da coleta é: {most_distant_date_str}")
            
            print(f'Você deve seguinte este formato de data para inserir as datas desejadas: {user_example_format}')
            
            #Verificando se o usuário inseriu um formato de data válido
            try:
                beginning_interval = input('\nDigite a data de início do intervalo, ou seja, a data mais recente (utilize o formato de data especificado): ')              
                datetime.strptime(beginning_interval,user_time_format)
            except ValueError:
                print(f'\n\nErro, a data digitada {beginning_interval} é inválida. Verifique o formato da data inserida e tente novamente.\n\n')
            
            #Verificando se o usuário inseriu um formato de data válido
            try:
                end_interval = input('\nDigite a data do fim do intervalo, ou seja, a data mais distante (utilize o formato de data especificado): ')
                datetime.strptime(end_interval, user_time_format)
            except ValueError:
                print(f'\n\nErro, a data digitada {end_interval} é inválida. Verifique o formato da data inserida e tente novamente.\n\n')
                continue
            
            beginning_interval = datetime.strptime(beginning_interval, user_time_format) + timedelta(hours = 23, minutes = 59) #tem que adicionar o restante do porque o datetime gerado é para 0h
            beginning_interval = pd.to_datetime(beginning_interval, utc=True)
            end_interval = datetime.strptime(end_interval, user_time_format)
            end_interval = pd.to_datetime(end_interval, utc=True)
            if beginning_interval.date() > most_recent_date.date() or beginning_interval.date() < most_distant_date.date():
                print('\n\nErro, a data de ínicio está fora do intervalo do dataset.\n\n')
                continue
            if end_interval.date() > most_recent_date.date() or end_interval.date() < most_distant_date.date():
                print('\n\nErro, a data de fim está fora do intervalo do dataset.\n\n')
                continue
            else:
                break
            #test
        clean_sorted_date = clean_date.sort_values(by = date_column_name, ascending=False).reset_index(drop=True)
        
        #Formata a série de datas do dataframe clean_date para o tipo Timestamp correto e retira a timezone p/ a comparação dar certo
        clean_date_format_no_tz = pd.to_datetime(clean_sorted_date[date_column_name], format = '%Y-%m-%d %H:%M:%S').dt.tz_localize(None)
        
        #Comparando as datas na série clean_date com as datas dos limites escolhidos pelo usuário 
        mask_up_from_end = clean_date_format_no_tz >= end_interval.tz_localize(None)
        mask_down_from_beginning = clean_date_format_no_tz <= beginning_interval.tz_localize(None)
        
        #Fazendo a interseção das duas máscaras para obter um intervalo fechado
        mask_final_crop = mask_up_from_end & mask_down_from_beginning
        cropped_date = clean_sorted_date[mask_final_crop].reset_index(drop=True)
        
        return (cropped_date)

#IMPLEMENTAÇÃO DA FUNÇÃO PARA INTERAÇÕES SIM/NÃO COM O USUÁRIO            
def check_y_or_n(question):  # Função para perguntas sim/não

    while True:
        print(f"\n\n{question}")
        ans = input(
            "\n\nDigite 'S' ou pressione 'ENTER' para sim, ou 'N' para não: ")

        if (ans == '') or (ans.upper() == 'S'):
            ans = True
            break

        elif (ans.upper() == 'N'):
            ans = False
            break

        else:
            print(
                "Resposta inválida, verifique se você digitou a opção corretamente e tente de novo.")
            continue
    return(ans)


def make_dirs(dataset_type, suffix):
    files_filtered = []
    all_files = set()

    # Mapeando os diretórios
    for root, dirs, files in os.walk(".", topdown=False):

        # O nome do diretório começa com .\, então pegamos a partir do 3º caractere
        containing_dir = root[2:]

        # Criando lista contendo apenas arquivos .csv
        filenames = [file for file in files if file.endswith('.csv')]

        if filenames:  # Se existirem arquivos .csv no diretório
            # Cria uma lista com os paths completos dos arquivos
            files_filtered = [os.path.join(containing_dir, file)
                              for file in filenames]

        if files_filtered:  # Se existirem os paths dos arquivos .csv do diretório analisado
            for file_path in files_filtered:
                # Adiciona os paths dos arquivos ao set dos paths de todos os arquivos
                all_files.add(file_path)

    # Se não for encontrado nenhum arquivo csv, gera um mensagem de erro.
    if not all_files:
        print("\n\nErro. Não existem arquivos de dataset nesta pasta. Reiniciando o programa.")
        return(0)  # sai da função e retorna ao menu principal

    # Criando um dicionáario para organizar os arquivos csv
    files_dict = {}
    i = 0

    for file_path in all_files:

        # Checando se o arquivo csv é do tipo desejado, de acordo com o dataset definido
        df_check_file_type = pd.read_csv(file_path, sep=';')
        # O facepager foi configurado para gerar uma coluna extra com o nome do tipo de dataset
        if dataset_type in df_check_file_type.columns:
            i += 1
            files_dict.update({i: file_path})

    print("\n\nOs arquivos disponíveis para processamento são:\n\n")
    message: []  # A mensagem que será gerada de acordo com a localização do arquivo

    for index, file_path in files_dict.items():

        # Divide o path para obter o nome dos diretórios e arquivos
        path_parts = file_path.split('\\')
        i = 0  # Contador
        # Montando as mensagens do menu de escolhas
        for i in range(1, len(path_parts)+1):
            if i == 1:
                message = (f"{index} -- O arquivo: {path_parts[-i]}")
                if len(path_parts) == 1:
                    message = message + ", que está nesta pasta."
            if i > 1:
                message = message + (f", dentro da pasta: {path_parts[-i]}")
        # Imprimindo uma descrição verbal da localização dos arquivos
        print(message)
        print(f"\n(O path é:{file_path})\n")  # Imprimindo o path do artigo

    while True:

        chosen_n = input("\n\nEscolha o número do arquivo a ser selecionado:")

        try:
            chosen_n = int(chosen_n)
            if chosen_n not in files_dict.keys():  # Checa se é um número válido
                raise ValueError
            break

        except ValueError:
            print(
                "\nA resposta digitada não corresponde a um número ou não está entre os números listados.")
            continue

    selected_file = files_dict[chosen_n]  # Extrai o nome do arquivo de entrada

    print(f"\nO arquivo selecionado foi: {selected_file}")

    print("\n\nCriando novo diretório para salvar os datasets após o processamento...")

    # Caminho completo do arquivo de entrada
    n_dir_name = os.path.join(os.getcwd(), selected_file)
    # Caminho sem a extensão .csv ao final
    n_dir_name = re.search(r'(.+)\.csv$', n_dir_name).group(1)

    # Definindo o path final do diretório de saída
    # Adicona o sufixo definido ao nome do diretório de saída, para discernimento
    x_dir_name = n_dir_name+suffix
    i = 0

    while True:

        try:
            os.mkdir(x_dir_name)
            break

        except FileExistsError:
            i += 1
            x_dir_name = f'{n_dir_name}{suffix}({str(i)})'
            continue

    return(selected_file, x_dir_name)


def choose_function(options_dir):

    print("\n\nSelecione as opções de processamento:\n\n")
    for num, option in options_dir.items():
        print(f"{num}: {option}\n")

    while True:
        try:

            chosen_option = input("Digite o número da opção selecionada: ")

            chosen_option = int(chosen_option)

            if chosen_option not in options_dir.keys():
                raise ValueError
            break

        except ValueError:

            print("\nA resposta digitada não corresponde a um número ou não está entre os números listados. Tente novamente.")
            continue

    if chosen_option == 1:
        extract_urls()
    elif chosen_option == 2:
        clean_search()
    elif chosen_option == 3:
        clean_articles()


def clean_articles():
    # Criando os diretórios e definindo o caminho de saída do arquivo:

    # Saída de make_dirs: return(selected_file, x_dir_name)
    # selected_file é o path do arquivo de entrada e x_dir_name é o path do diretório de saída
    try:
        selected_file, x_dir_name = make_dirs('artigos', '_artigo')
    except TypeError:
        #Não existem arquivos compativeis
        return()

    # Lendo o dataset resultante do preset de Artigos do Facepager

    df = pd.read_csv(selected_file, sep=';')

    # Removendo os demais dados (links, linhas em branco e offcuts)
    df_data = df.loc[df['object_type'] == 'data']

    # Removendo os dados duplicados
    df_data = df_data.drop_duplicates(subset=['object_id'])

    # Resetando o índice após manipular o dataframe
    df_data.reset_index(drop=True, inplace=True)

    #Listando as opções disponíveis ao usuário
    selectable_options = ['1', '2', '3', '4','5','6','7','8','9','10','11','12','13','14','15']
    
    while True:

        # Listando as opções para que o usuário crie um dataset customizado
        print("A seguir, serão apresentadas as opções para montar um dataset de saída customizado. O dataset resultante conterá somente os campos selecionados.\n")
        print("--------Você pode selecionar mais do que uma opção, basta separar os números com vírgula:--------\n")
        print("***********PARA SELECIONAR TODAS AS OPÇÕES ABAIXO, PRESSIONE A TECLA 'ENTER'***********\n\n")

        print(f"{selectable_options[0]} ---- Link da matéria original.")
        print(f"{selectable_options[1]} ---- Links de outras matérias que foram referenciadas no texto do artigo.")
        print(f"{selectable_options[2]} ---- Título.")
        print(f"{selectable_options[3]} ---- Subtítulo.")
        print(f"{selectable_options[4]} ---- Conteúdo do artigo, em texto.")
        print(f"{selectable_options[5]} ---- Data de publicação da matéria.")
        print(f"{selectable_options[6]} ---- Data de atualização da matéria.")
        print(f"{selectable_options[7]} ---- Fonte.")
        print(f"{selectable_options[8]} ---- Autor.")
        print(f"{selectable_options[9]} ---- Imagens.")
        print(f"{selectable_options[10]} ---- Highlights.")
        print(f"{selectable_options[11]} ---- Olho.")
        print(f"{selectable_options[12]} ---- Gerar arquivos de texto para cada matéria, este arquivo de texto conterá o texto do corpo da matéria.\nOs arquivos de texto serão salvos em uma pasta separada, o formato será do tipo .txt")
        print(f"{selectable_options[13]} ---- Gerar um arquivo de texto fundindo o texto de todas as matérias.")
        print(f"{selectable_options[14]} ---- Todas as opções acima, menos as opções '13' e '14' (não serão gerados arquivos de texto .txt).")

        sel_options = input(
            "\n\nSelecione as opções desejadas, lembre-se que, caso haja mais de uma opção, você deve separar os números por vírgula: ")

        # Checando se existe algum caractere fora de números e ","
        if re.match(r"[^0-9,]+", sel_options):
            print("\nErro, existe algum caractere inválido na resposta. Selecione novamente as opções desejadas.\n\n")
            continue

        if sel_options == '':
            print(
                "\n----Foram selecionadas todas as opções.----\n\n")
            break
        
        #Checando se os números digitados são válidos
        if not set(sel_options.split(',')).issubset(selectable_options):
            wrong_num = set(sel_options) - set(selectable_options)
            wrong_num = list(wrong_num)
            print(f'\nAs opções: {" ".join(wrong_num)} não são válidas. Tente novamente.\n')
            continue
    
        
        else:
            
            print(f'As opções selecionadas foram: {sel_options}\n\n')
            break

    # Tratando os resultados
    
    #Se foram selecionadas todas as opções:
    if sel_options == '':
        options_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10', '11', '12','13','14']
    
    #Se foram selecionadas opções específicas:
    else:
        # Pega apenas os caracteres numericos
        options_list = re.split(r'\W+', sel_options)

    # Criando dataframe de saída
    output_df = pd.DataFrame()

    # Reorganizando um novo dataframe a partir das opções selecionadas pelo usuário
    if '15' in options_list:
        # Se o usuário escolher a opção de selecionar todas as opções:
        options_list = ['1', '2', '3', '4', '5', '6', '7', '8','9','10','11','12','13','14']

    if '1' in options_list:
        # Criando uma coluna no novo dataset para o link original da matéria, armazenado no dataset original
        # adicionando nova coluna ao dataset
        output_df = pd.concat([output_df, df_data["object_id"]], axis=1)
        # renomeando a nova coluna
        output_df.rename(columns={'object_id': 'link'}, inplace=True)

    if '2' in options_list:
        # armazenando no novo dataframe
        # adicionando nova coluna ao novo dataframe
        output_df = pd.concat([output_df, df_data["embedded_links"]], axis=1)
        # renomeando a nova coluna
        output_df.rename(
            columns={'embedded_links': 'links_embutidos'}, inplace=True)

    if '3' in options_list:
        # Criando uma coluna no novo dataset para o titulo armazenado no dataset original
        output_df = pd.concat([output_df, df_data["titulo"]], axis=1)

    if '4' in options_list:
        # Criando uma coluna no novo dataset para o subtitulo armazenado no dataset original
        # adicionando nova coluna ao dataframe
        output_df = pd.concat([output_df, df_data["subtitulo"]], axis=1)

    if '5' in options_list or '13' or '14' in options_list:
        # Criando lista temporária para armazenar os textos
        st_contents = []

        # Extraindo os textos de cada página processada pelo Facepager
        for i in range(len(df_data["conteudo"])):
            # Pega o texto na coluna conteúdo, primeira linha
            texto = df_data["conteudo"].iloc[i]
            if not pd.isna(texto):    
                # Remove o ';' que aparece entre duas frases
                texto = re.sub(r'([\w]);([\W][^;])', r'\1\2', texto, re.UNICODE)
                texto = re.sub(r'([^;][\W]);([\w])', r'\1\2', texto, re.UNICODE)
                texto = re.sub(r'([.,!:"?]);([.,!:"?])', r'\1\2', texto, re.UNICODE)
                # Removendo os caracteres residuais do texto
                texto = re.sub(r"^;", r"", texto)  # Remove o ';' do começo
                # Remove o ';' que aparece em torno de nomes destacados com links
                texto = re.sub(r"(;)(\w{2,})(;)", r" \2 ", texto, re.UNICODE)
                # Remove o ';' que aparece entre os itens de uma lista
                texto = re.sub(r"(\.);([A-Z])", r"\1\n\n\2", texto)
                # Procura um ';' sozinho e substitui deixando apenas o caractere anterior e o posterior
                texto = re.sub(r"([^;]);([^;])", r"\1 \2", texto)
                # Procura um grupo de 2 a 4 ';' e substitui por duas novas linhas
                texto = re.sub(r"([^;]);{2,5}([^;])", r"\1\n\n\2", texto)
                # Remove os teasers de vídeo do final
                texto = re.sub(r"VÍDEOS\:.+;*", r"", texto)
                # Remove os teasers de podcasts do final
                texto = re.sub(r";.+podcast.+?;", r"", texto)
                texto = re.sub(r";$", r"", texto)  # Remove o ';' do começo

            else:
                texto = ''
            
            st_contents.append(texto)  # Salva numa lista de textos

    if '5' in options_list:
        # Exportando os textos armazenados previamente em uma lista para o dataframe
        # Converte a lista num dataframe
        df_contents = pd.DataFrame(st_contents, columns=["conteudo"])
        # Adicionando a nova coluna ao dataset
        output_df = pd.concat([output_df, df_contents], axis=1)

    if '6' in options_list:

        # Estabelecendo os formatos de datetime de entrada e de saída
        # formato_entrada = "%Y-%m-%d %H:%M:%S"
        # formato_saida = "%d/%m/%Y %H:%M:%S"

        # Adicionando ao dataframe
        data_pub_df = pd.to_datetime(
            df_data['data_pub'], infer_datetime_format=True)
        data_pub_df = data_pub_df - timedelta (hours=3) #Precisa consertar o offset de +3 horas 
        data_pub_df.name = 'data_publicacao'
        output_df = pd.concat([output_df, data_pub_df], axis=1)

    if '7' in options_list:

        # Estabelecendo os formatos de datetime de entrada e de saída
        #formato_entrada = "%Y-%m-%d %H:%M:%S"
        #formato_saida = "%d/%m/%Y %H:%M:%S"

        # Adicionando ao dataframe
        data_at_df = pd.to_datetime(
            df_data['data_at'], infer_datetime_format=True)
        data_at_df = data_at_df - timedelta (hours=3) #Precisa consertar o offset de +3 horas 
        data_at_df.name = 'data_atualizacao'
        output_df = pd.concat([output_df, data_at_df], axis=1)

    if '8' in options_list:

        # Criando uma lista para armazenar a coluna de fontes, a ser processada
        fontes_li = []

        # Fazendo a leitura das fontes armazenadas no dataset do facepager, processando para o formato desejado
        for i in range(len(df_data['fonte'])):
            fonte = df_data['fonte'].iloc[i]
            if not pd.isna(fonte):
                if len(fonte.split(',')) > 1:
                    fontes_li.append(fonte.split(',')[1])
                else:
                    fontes_li.append(fonte)
            else:
                fontes_li.append(fonte)

        # Salvando a lista de fontes em um dataframe temporário
        df_fontes = pd.DataFrame(fontes_li, columns=['fonte'])
        # Concatenando o dataframe temporário ao dataframe de saída
        output_df = pd.concat([output_df, df_fontes], axis=1)

    if '9' in options_list:
        # Criando uma lista para armazenar a coluna de fontes, a ser processada
        autor_li = []

        # Fazendo a leitura das fontes armazenadas no dataset do facepager, processando para o formato desejado
        for i in range(len(df_data['fonte'])):
            autor = df_data['fonte'].iloc[i]
            if not pd.isna(autor):
                if len(autor.split(',')) > 1:
                    autor = (autor.split(','))[0]
                    autor_li.append(autor)
                else:
                    autor_li.append('')
            else:
                autor_li.append('')
        # Salvando a lista de fontes em um dataframe temporário
        df_autor = pd.DataFrame(autor_li, columns=['autor'])
        # Concatenando o dataframe temporário ao dataframe de saída
        output_df = pd.concat([output_df, df_autor], axis=1)
    
    if '10' in options_list:
        # Criando uma lista para armazenar a coluna de fontes, a ser processada
        output_df = pd.concat([output_df, df_data["imagens"]], axis=1) 
        
    if '11' in options_list:
        # Criando uma lista para armazenar a coluna de fontes, a ser processada
        output_df = pd.concat([output_df, df_data["highlights"]], axis=1) 
    
    if '12' in options_list:
        # Criando uma lista para armazenar a coluna de fontes, a ser processada
        output_df = pd.concat([output_df, df_data["olho"]], axis=1) 
        
    if '13' in options_list:
        # Os arquivos de texto serão nomeados de acordo com o título da matéria
        titulo = ''

        char_especial = re.compile(r'[\\\/*?:"<>|]') #criando objeto regex pra remover caracteres especiais
        dir_text_nm = os.path.join(x_dir_name+'\\textos')
        os.mkdir(dir_text_nm)
        # Montando cada arquivo de texto novo, a partir do dataset processado pelo Facepager
        for i in range(len(df_data['titulo'])):
            # Extraindo o título da matéria cujo texto será salvo
            titulo = df_data['titulo'].iloc[i]

            if char_especial.findall(titulo):
                titulo = char_especial.sub(' ', titulo) #removendo caracteres especiais

            # Montando o PATH de saída
            path_out_txt = os.path.join(dir_text_nm, (titulo + ".txt"))
            # Criando um objeto file para escrever um arquivo txt
            with open(path_out_txt, 'w', encoding="utf-8") as txt_file:
                # st_contents.append(texto) #Salva numa lista de textos
                txt_file.write(st_contents[i])
        print(f'\nA pasta contendo os arquivos de texto para cada matéria se encontra em: "{dir_text_nm}"')
        
        
    if '14' in options_list:
        
        # Montando cada arquivo de texto novo, a partir do dataset processado pelo Facepager
        search_term = x_dir_name.split('\\')
        search_term = search_term[-1]
        
        # Montando o PATH de saída
        path_out_all_txt = os.path.join(x_dir_name, (search_term + ".txt"))
        
        # Criando um objeto file para escrever um arquivo txt
        with open(path_out_all_txt, 'w', encoding="utf-8") as txt_file:
            # st_contents.append(texto) #Salva numa lista de textos
            all_text = '\n\n'.join(st_contents)
            all_text = 'text\n' + all_text
            txt_file.write(all_text)
        print(f'\nO arquivo único contendo todos os textos {search_term+".txt"} se encontra na pasta {x_dir_name}')
            
    # Determinando os nomes dos campos que estão disponíveis para serem ordenados pelo usuário
    chsn_fields = output_df.columns.values.tolist()
    selectable_fields = []
    
    # Atribuindo os nomes correspondentes às colunas
    for i in range(len(chsn_fields)):
        if chsn_fields[i] == 'link':
            selectable_fields.append('Link da matéria')

        elif chsn_fields[i] == 'links_embutidos':
            selectable_fields.append('Links embutidos no texto')

        elif chsn_fields[i] == 'titulo':
            selectable_fields.append('Título da matéria')

        elif chsn_fields[i] == 'subtitulo':
            selectable_fields.append('Subtítulo da matéria')

        elif chsn_fields[i] == 'conteudo':
            selectable_fields.append('Conteúdo (texto completo) da matéria')

        elif chsn_fields[i] == 'data_publicacao':
            selectable_fields.append('Data de publicação da matéria')

        elif chsn_fields[i] == 'data_atualizacao':
            selectable_fields.append('Data de atualização da matéria')

        elif chsn_fields[i] == 'autor':
            selectable_fields.append('Autor da matéria')

        elif chsn_fields[i] == 'fonte':
            selectable_fields.append('Fonte')
        
        elif chsn_fields[i] == 'imagens':
            selectable_fields.append('Links das imagens na matéria')
        
        elif chsn_fields[i] == 'highlights':
            selectable_fields.append('Highlights do texto da matéria')

        elif chsn_fields[i] == 'olho':
            selectable_fields.append('Olho da matéria')
    
    # Perguntando ao usuário se ele deseja recortar um intervalo de datas:
    if 'data_atualizacao' in output_df.columns or 'data_publicacao' in output_df.columns:
        if crop_dates(first_check = True):
            output_df = crop_dates(output_df)
    
    if not chsn_fields:
        return()
    
    ans_sort_yn = check_y_or_n(
        "Você deseja ordenar o dataset de acordo com algum campo ou tipo de dado?")

    # Caso exista alguma data, o padrão seria ordenar pela data primeiro, mesmo sem a escolha específica do usuário
    if not ans_sort_yn:
        if 'data_atualizacao' in output_df.columns and 'data_publicacao' in output_df.columns:
            # ordena pelo parametro data
            output_df.sort_values(by='data_publicacao',
                                  inplace=True, ascending=False)
            # formata o valor datetime na coluna para uma string com o padrão especificado
            output_df['data_publicacao'] = output_df['data_publicacao'].dt.strftime(
                '%d/%m/%Y %H:%M:%S')
            output_df['data_atualizacao'] = output_df['data_atualizacao'].dt.strftime(
                '%d/%m/%Y %H:%M:%S')

        elif 'data_atualizacao' in output_df.columns and 'data_publicacao' not in output_df.columns:
            output_df.sort_values(by='data_atualizacao',
                                  inplace=True, ascending=False)
            output_df['data_atualizacao'] = output_df['data_atualizacao'].dt.strftime(
                '%d/%m/%Y %H:%M:%S')

        elif 'data_publicacao' in output_df.columns and 'data_atualizacao' not in output_df.columns:
            output_df.sort_values(by='data_publicacao',
                                  inplace=True, ascending=False)
            output_df['data_publicacao'] = output_df['data_publicacao'].dt.strftime(
                '%d/%m/%Y %H:%M:%S')

    else:
        while True:
            # Listando as possíveis opções de seleção da ordenação
            print("\n\nObservações:\n")
            print("-> Quando selecionada a ordenação por algum elemento de texto, essa ordenação será por ordem alfabética.")
            print("-> Quando selecionada a ordenação por um elemento de data, essa ordenação será por mais recente ou mais antigo.")
            print("-> Quando selecionada a ordenação por um elemento numérico, essa ordenação será do menor para o menor ou do menor para o maior.")

            list_available_opt = list(range(1, len(chsn_fields) + 1))
            list_available_opt = [str(option) for option in list_available_opt]

            print("\n\nEscolha qual será a categoria para ordenar o dataset:\n")

            for i in range(len(chsn_fields)):
                print(f'{i+1}- Por {selectable_fields[i]}')

            ans_sort_id = input('Resposta: ')

            if ans_sort_id not in list_available_opt:
                print("Escolha inválida, tente novamente.")
                continue
            else:
                break

        ans_sort_id = int(ans_sort_id)
        print(
            f'\nA opção escolhida foi: {selectable_fields[ans_sort_id - 1]}\n')

        while True:
            print("Escolha qual será o tipo de ordenação:\n\n")
            print('1 - Ascendente.')
            print('2 - Descendente.')
            ans_asc_desc = input('Resposta: ')

            if ans_asc_desc not in ['1', '2']:
                print("Escolha inválida, tente novamente.")
                continue
            else:
                ans_asc_desc = int(ans_asc_desc)
                break

        # OBS:
        # chsn_fields tem o nome original da coluna do dado dentro do dataset
        # selectable_fields tem o nome do que significa, mostrado pro usuário
        # os dois possuem a mesma ordenação de (0,len - 1)

        # Determinando os valores para realizar a ordenação

        # Se é ascendente ou descendente:
        if ans_asc_desc == 1:
            asc_desc = True
        elif ans_asc_desc == 2:
            asc_desc = False
        else:
            print('Erro na escolha de ascendente/descendente!')
            sys.exit()

        # Qual o nome da coluna
        nome_coluna = chsn_fields[ans_sort_id - 1]

        # Aplicando a ordenação
        output_df.sort_values(by=nome_coluna, inplace=True, ascending=asc_desc)
        if 'data_atualizacao' in output_df.columns:
            output_df['data_atualizacao'] = output_df['data_atualizacao'].dt.strftime(
            '%d/%m/%Y %H:%M:%S')
        if 'data_publicacao' in output_df.columns:
            output_df['data_publicacao'] = output_df['data_publicacao'].dt.strftime(
            '%d/%m/%Y %H:%M:%S')

    # Estabelecendo caminho de saída
    
    # O nome do arquivo será baseado no nome do diretório onde este será salvo
    folder_name = re.search(r".+[.\\](.+)$", x_dir_name).group(1)

    path_out = os.path.join(x_dir_name, (f"{folder_name}.csv"))
    
    #Excluindo as duplicatas:
    output_df = output_df.drop_duplicates(ignore_index = True)
    
    # Exportando o dataset processado em um arquivo csv:
    output_df.to_csv(path_or_buf=path_out, quotechar='"',
                     sep=';', encoding='utf-8-sig',
                     index=False, header=True)

    print("\n\nO arquivo de saída gerado se encontra em:\n\n", path_out, "\n\n")

    return()


def extract_urls():
    # Criando os diretórios e definindo o caminho de saída do arquivo:

    # Saída de make_dirs: return(selected_file, x_dir_name)
    # selected_file é o path do arquivo de entrada e x_dir_name é o path do diretório de saída
    try:
        selected_file, x_dir_name = make_dirs('busca_noticias', '_busca_url')
    except TypeError:
        #Não existem arquivos compativeis
        return()
    
    # Lendo o dataset resultante do preset de Busca do Facepager
    df = pd.read_csv(selected_file, sep=';')

    # O nome do arquivo será baseado no nome do diretório criado para salvá-lo
    folder_name = re.search(r".+[.\\](.+)$", x_dir_name).group(1)

    pat_valid_url = r'//g1.globo.com/'  # cria uma regex para encontrar o padrão nas strings
    pat_podcasts = r'//g1.globo.com/podcast/' # cria um regex a ser usado para filtrar as URLs de podcast

    # cria uma mascara para filtrar o dataframe
    mask_urls = df.object_id.str.contains(pat_valid_url)
    mask_no_podcasts = np.invert(df.object_id.str.contains(pat_podcasts))

    df_filtered = df[mask_urls & mask_no_podcasts]

    # Reseta os índices após manipulação do dataframe
    df_filtered.reset_index(drop=True, inplace=True)

    for i, row in (df_filtered).iterrows():

        # Extrai a URL original a partir do padrão do website
        link = re.search('&u=(.+?)&syn', row['object_id']).group(1)
        link = link.replace('%3A', ':').replace('%2F', '/')
        # Substitui a URL modificada no Dataframe
        df_filtered.at[i, 'object_id'] = link

    # Isolando as URLs do restante do dataframe
    df_filtered = df_filtered['object_id']

    # Removendo as URLs duplicadas
    df_filtered = df_filtered.drop_duplicates()

    # Reseta os índices após manipulação do dataframe
    df_filtered.reset_index(drop=True, inplace=True)

    #df_filtered = crop_dates(df_filtered)

    # Exportando o dataframe
    print("\n\nGerando dataset com links para as matérias da busca...\n\n")
    path_out = os.path.join(x_dir_name, (folder_name+"_list.csv"))
    df_filtered.to_csv(
        path_or_buf=path_out, quotechar='"', sep=';', encoding='utf-8-sig', index=False, header=False)

    print("\n\nO arquivo de saída gerado se encontra em:\n\n", path_out, "\n\n")

    return()


def clean_search():

    # Criando os diretórios e definindo o caminho de saída do arquivo:

    # Saída de make_dirs: return(selected_file, x_dir_name)
    # selected_file é o path do arquivo de entrada e x_dir_name é o path do diretório de saída
    
    try:
        selected_file, x_dir_name = make_dirs('busca_noticias', '_busca')
    except TypeError:
        #Não existem arquivos compativeis
        return()

    # Lendo o dataset resultante do preset de Busca do Facepager
    df = pd.read_csv(selected_file, sep=';')

    folder_name = re.search(r".+[.\\](.+)$", x_dir_name).group(1)

    pat_valid_url = r'//g1.globo.com/'  # cria uma regex para encontrar o padrão nas strings
    pat_podcasts = r'//g1.globo.com/podcast/' # cria um regex a ser usado para filtrar as URLs de podcast

    # cria uma mascara para filtrar o dataframe
    mask_valid_urls = df.object_id.str.contains(pat_valid_url)
    mask_no_podcasts = np.invert(df.object_id.str.contains(pat_podcasts))

    df_filtered = df[mask_valid_urls & mask_no_podcasts]

    # Reseta os índices após manipulação do dataframe
    df_filtered.reset_index(drop=True, inplace=True)

    #Criando um novo dataframe para evitar chained indexing
    df_filtered = df_filtered.copy()

    # Requisitando a permissão do usuário para padronizar as datas temporais do dataset

    ans_recent_date = check_y_or_n("O dataset de busca que será processado foi coletado há menos de 1h no Facepager?\n\n")
   
    if ans_recent_date:

        for i, row in (df_filtered).iterrows():
            # Normalizando os links
            # Extrai a URL original a partir do padrão do website
            link = re.search('&u=(.+?)&syn', row['object_id']).group(1)
            link = link.replace('%3A', ':').replace('%2F', '/')

            # Substitui a URL modificada no Dataframe
            df_filtered.at[i, 'object_id'] = link

            # Normalizando as escalas de tempo:
            if re.search(r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']):
                
                # value é o valor numérico
                value = int(
                    re.search(r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']).group(1))

                # scale corresponde a dias/dia/horas/hora
                scale = re.search(
                    r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']).group(2)
                if (scale == 'hora') or (scale == 'horas'):
                    delta = timedelta(hours=value)  # há 'x' horas?
                    true_time = datetime.now() - delta
                    #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")
                elif (scale == 'dias') or (scale == 'dia'):
                    delta = timedelta(days=value)  # há 'x' dias?
                    true_time = datetime.now() - delta
                    #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")
                elif (scale == 'minutos') or (scale == 'minuto'):
                    delta = timedelta(minutes=value)  # há 'x' minutos?
                    true_time = datetime.now() - delta
                    #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")
                
                # Substitui o dado temporal reformatado no dataset
                df_filtered.at[i, 'data'] = true_time

            elif row['data'] == 'há poucos instantes':
                df_filtered.at[i, 'data'] = datetime.now()
            
            else:
                df_filtered.at[i, 'data'] = datetime.strptime(row['data'], '%d/%m/%Y %Hh%M')

    #Caso o usuário não tenha realizado a coleta recentemente:
    if not ans_recent_date:

        #Verifica se o usuário gostaria de aproximar as datas
        ans_approx_dates = check_y_or_n('Você gostaria de aproximar as datas relativas? (ex.:"há 1 hora", "há 2 dias")\n\n')


        #O usuário escolheu aproximar as datas relativas:
        if ans_approx_dates:
            #É preciso retirar a possibilidade de manter um falso positivo de uma execução anterior
            ans_keep_bad_dates = False
            
            # #Uniformizando as datas precisas do dataframe principal 
            # df_filtered['data'] = pd.to_datetime(df_filtered['data'], infer_datetime_format= True, errors= 'ignore')

            #Obtendo um dataframe somente com as datas precisas
            df_full_only = pd.to_datetime(df_filtered['data'], format= '%d/%m/%Y %Hh%M' , errors='coerce')

            #Determinando a data mais recente presente no dataset original
            df_full_only.sort_values(axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last', ignore_index=True, key=None)
            
            #Estima-se que a data mais recente real seja a data mais recente do dataset mais uma semana
            date_offset = timedelta(days=7)
            most_recent_date = df_full_only.iloc[0]
            most_recent_date = most_recent_date + date_offset

            #Substituindo as datas relativas pela aproximação
            for i, row in (df_filtered).iterrows():

                # Normalizando os links
                # Extrai a URL original a partir do padrão do website
                link = re.search('&u=(.+?)&syn', row['object_id']).group(1)
                link = link.replace('%3A', ':').replace('%2F', '/')

                # Substitui a URL modificada no Dataframe
                df_filtered.at[i, 'object_id'] = link


                # Normalizando as escalas de tempo:
                if re.search(r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']):
                        
                        # value é o valor numérico
                        value = int(
                            re.search(r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']).group(1))

                        # scale corresponde a dias/dia/horas/hora
                        scale = re.search(
                            r'há\s(\d+)\s(horas?|dias?|minutos?)', row['data']).group(2)
                        if (scale == 'hora') or (scale == 'horas'):
                            delta = timedelta(hours=value)  # há 'x' horas?
                            true_time = most_recent_date - delta
                            #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")
                        elif (scale == 'dias') or (scale == 'dia'):
                            delta = timedelta(days=value)  # há 'x' dias?
                            true_time = most_recent_date - delta
                            #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")
                        elif (scale == 'minutos') or (scale == 'minuto'):
                            delta = timedelta(minutes=value)  # há 'x' minutos?
                            true_time = most_recent_date - delta
                            #true_time_str = true_time.strftime("%d/%m/%Y %Hh%M")

                        # Substitui o dado temporal reformatado no dataset
                        df_filtered.at[i, 'data'] = true_time

                elif row['data'] == 'há poucos instantes':
                    true_time = most_recent_date
                    df_filtered.at[i, 'data'] = true_time

                else:
                    true_time = datetime.strptime(row['data'], "%d/%m/%Y %Hh%M")
                    df_filtered.at[i, 'data'] = true_time
            print('oi')
        #O usuário escolheu não aproximar as datas relativas
        else:
            ans_keep_bad_dates = check_y_or_n('Você gostaria de manter as datas relativas originais? (ex.:"há 1 hora", "há 2 dias")\n\n')
            
            #O escolheu não aproximar e quer manter as datas relativas
            if ans_keep_bad_dates:
                df_filtered['data'] = pd.to_datetime(df_filtered['data'], format= '%d/%m/%Y %Hh%M', errors = 'ignore')
            
            #O escolheu não aproximar e não quer manter as datas relativas
            else:
                df_filtered['data'] = pd.to_datetime(df_filtered['data'], format= '%d/%m/%Y %Hh%M', errors = 'coerce')
    
    #Selecionando apenas as colunas úteis
    df_filtered = df_filtered.loc[:,['object_id','titulo','resumo','data','fonte']]
    
    #Recortando as datas em um intervalo de tempo a ser definido pelo usuário:
    if crop_dates(first_check = True):
        df_filtered = crop_dates(df_filtered)

    # Ordenando as datas em ordem descendente
    df_filtered.sort_values(by='data',
                            inplace=True, ascending=False)

    # Convertendo as datas do datetime para o padrão desejado
    df_filtered['data'] = pd.to_datetime(df_filtered['data'])
    df_filtered['data'] = df_filtered.data.dt.strftime('%d/%m/%Y %H:%M:%S')

    #print('\nAs datas foram reformatadas com sucesso\n')

    # Definindo o caminho de sáida do arquivo
    path_out = os.path.join(x_dir_name, (f"{folder_name}_prcs.csv"))

    # Checando se o usuário quer manter o cabeçalho
    ans = check_y_or_n(
        'Você deseja manter o cabeçalho do arquivo .csv? (A primeira linha, com o nome das opções escolhidas.)')
    
    df_filtered = df_filtered.drop_duplicates(subset = 'titulo', ignore_index = True)
    # Se o usuário pediu para manter o cabeçalho:
    if ans:
        #Renomeando a coluna dos links
        df_filtered.rename(columns={'object_id': 'link'}, inplace = True)
        df_filtered.to_csv(
            path_or_buf=path_out, quotechar='"', sep=';', encoding='utf-8-sig', index=False, header=True)

    # Se o usuário não quer manter o cabeçalho:
    else:
        df_filtered.to_csv(
            path_or_buf=path_out, quotechar='"', sep=';', encoding='utf-8-sig', index=False, header=False)

    print("\n\nO arquivo de saída gerado se encontra em:\n\n", path_out, "\n\n")


lista_sites = ["G1"]
proc_options = {
    1:
    """
    Quero utilizar um dataset (arquivo .csv) do Facepager OBTIDO PELA BUSCA DE UMA PALAVRA-CHAVE no site selecionado acima.
    Esta opção irá gerar um novo DATASET COM TODOS OS LINKS DAS MATÉRIAS que foram buscadas pelo Facepager.
    """,
    2:
    """
    Quero utilizar um dataset (arquivo .csv) do Facepager OBTIDO PELA BUSCA DE UMA PALAVRA-CHAVE no site selecionado acima.
    Esta opção irá gerar um dataset com as INFORMAÇÕES RESUMIDAS DA MATÉRIA (título, data e um pequeno resumo).
    """,
    3:
    """
    Quero utilizar um dataset (arquivo .csv) do Facepager obtido por uma lista de links de matérias.
    Nesta opção, AS INFORMAÇÕES EXTRAÍDAS DIRETAMENTE DOS ARTIGOS serão formatadas e processadas em um novo dataset.
    O usuário pode fazer a ESCOLHA DE QUAIS INFORMAÇÕES SERÃO ARMAZENADAS NO NOVO DATASET (data, subtitulo, texto integral, etc.)
    """
}

print("\n\n****ESTE SCRIPT IRÁ PROCESSAR OS DATASETS GERADOS POR SCRAPING DE WEBSITES UTILIZANDO O FACEPAGER****\n")

while True:

    print("Listando os websites suportados:\n")

    for count, website in enumerate(lista_sites):
        print(f"{count+1}: {website}\n")

    while True:
        try:

            chosen_website = input("Digite o número do website selecionado:")

            chosen_website = int(chosen_website)

            if chosen_website not in range(1, len(lista_sites)+1):
                raise ValueError
            break

        except ValueError:

            print("\nA resposta digitada não corresponde a um número ou não está entre os números listados. Tente novamente.")
            continue

    choose_function(proc_options)

    # Verificando se o usuário digitou uma resposta válida
    ans = check_y_or_n(
        "\n\nVocê gostaria de utilizar novamente o programa ou acessar outras funções?")

    # Definindo a próxima ação de acordo com a escolha do usuário
    if ans:
        continue

    else:
        break

print("****TERMINANDO O PROGRAMA****")
sys.exit()
