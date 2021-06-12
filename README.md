# Facescraper

O "Facescraper" é um script criado para o uso conjunto com o software Facepager. Ele é executado após a coleta de dados de uma ou mais páginas de notícia do portal G1, utilizando a função nativa do site de busca por palavra-chave.

O script foi desenvolvido, testado e implementado no Laboratório de Estudos sobre Imagem e Cibercultura (LABIC) da Universidade Federal do Espírito Santo.

## Instalação

Para instruções de instalação do software Facepager, acessar a página do desenvolvedor no GitHub:

[Facepager](https://github.com/strohne/Facepager)

É necessária a utilização de *presets* específicos para configurar o Facepager para a página do G1. Estes presets também estão incluídos nos arquivos do projeto. 

O script já possui um *alias* implementado na máquina Windows do laboratório. **Estando aberta a janela na pasta que contém contém os datasets .csv que se deseja processar, basta clicar com o botão direito numa área vazia, selecionar *cmder* e executar o comando:**
```bash
facescraper
```
O script está configurado para uso específico em máquinas Windows. Ele deve ser executado como um script Python dentro da pasta que contém os datasets .csv a serem processados.

*Os datasets precisam estar na mesma pasta ou em diretórios internos da pasta onde o script está sendo executado, caso contrário, o programa não conseguirá identificar os datasets.*

Para a execução do script, são necessárias as bibliotecas:
* Pandas
* Numpy
* RegEx
* Sys
* Datetime
* Pathlib

## Utilização

O script pode ser utilizado para:

* Limpar e formatar os datasets extraídos pelo Facepager da página de resultados de uma busca por palavra-chave, do próprio G1.
* Limpar e formatar os datasets gerados pelo Facepager que contém as informações integrais das páginas de cada matéria G1 relacionadas a uma palavra-chave.
* Gerar um dataset com uma lista de links para todas as matérias obtidas.
* Gerar arquivos .txt individuais com os textos completos para cada matéria encontrada, ou um arquivo de texto fundindo todos os textos de todas as matérias encontradas.

As informações que podem ser extraídas pelo script são:

* Para o dataset com as informações das __páginas de resultado__ obtidas pelo mecanismo de busca de palavra-chave do G1:

     * Título da matéria.
     * Resumo.
     * Data.
     * Fonte. 

* Para o dataset com as informações de uma ou mais __páginas de matérias integrais__:

     * Título.
     * Subtítulo.
     * Conteúdo.
     * Data de publicação.
     * Data de atualização.
     * Fonte.
     * Imagens.
     * Destaques.
     * Olho do texto.
     * Links embutidos no texto da matéria.
