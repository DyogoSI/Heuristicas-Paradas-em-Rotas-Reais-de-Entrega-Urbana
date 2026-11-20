# Heurísticas: sequenciamento de paradas em rotas reais de entrega urbana

Trabalho 02 de Ciência de Dados (IFSULDEMINAS, Campus Machado): criação de uma heurística baseada em dados.
Relatório completo em [`trabalho_heuristica_entregas_reais.pdf`](trabalho_heuristica_entregas_reais.pdf).

## Resumo

Heurística em duas fases para ordenar as paradas de rotas de entrega: construção por vizinho mais próximo (com urgência para
janelas de horário) e melhoria por busca local 2-opt + Or-opt, que só aceita trocas que não aumentem as janelas violadas.

Resultado em 100 rotas reais (13.723 paradas), comparado à sequência que o motorista realmente percorreu:

| Medida | Motorista | Proposta |
|---|---|---|
| Deslocamento médio por rota | 154 min | 141 min (-9,2%) |
| Rotas em que a proposta é melhor | | 99 de 100 |
| Janelas de horário violadas (de 1.006) | 16 | 1 |
| Tempo de execução | | 0,9 s por rota |

## Dados (públicos e reais)

[Amazon Last Mile Routing Research Challenge](https://registry.opendata.aws/amazon-last-mile-challenges/), licença CC BY-NC 4.0
(uso acadêmico, não comercial). Os dados **não** estão neste repositório. Bucket público:
`https://amazon-last-mile-challenges.s3.amazonaws.com/almrrc2021/almrrc2021-data-training/model_build_inputs/`

Arquivos usados: `route_data.json`, `package_data.json`, `travel_times.json`, `actual_sequences.json`.

## Como reproduzir

Requer Python 3 com `numpy`, `matplotlib` e `reportlab`.

1. Baixe `route_data.json` e `actual_sequences.json` para uma pasta `dados/` na raiz do repositório.
2. Em `dados/`, execute `python ../codigo/pick.py` para escolher as 100 primeiras rotas "High" das estações DLA*; ele gera `ids.json` e `route_sel.json`.
3. Extraia só essas rotas dos arquivos grandes (leitura em streaming):
   `python codigo/extract.py <URL do package_data.json> dados/ids.json dados/pkg_sel.json` e o mesmo para `travel_times.json` (saída `tt_sel.json`).
4. `python codigo/run2.py <pasta_de_saida>` roda os métodos e grava `resultados2.pkl`.
5. `python codigo/figs2.py <pasta_de_saida>` gera as figuras; `python codigo/report2.py <pasta_de_saida> relatorio.pdf` monta o relatório.

Se os dados estiverem em outro lugar, defina a variável de ambiente `DADOS_AMAZON`.

## Conteúdo

- `codigo/heur2.py`: carga dos dados, construção (vizinho mais próximo, inserção mais barata), 2-opt, Or-opt, ILS e métricas.
- `codigo/run2.py`: experimento sobre as 100 rotas. `codigo/run2.log`: saída da execução usada no relatório.
- `codigo/figs2.py`, `codigo/report2.py`: figuras e relatório em PDF.
- `codigo/extract.py`, `codigo/pick.py`: seleção e extração das rotas.

## Limitações

Só sequencia paradas (não redistribui entre rotas), a capacidade do veículo nunca é restritiva (ocupação média de 78%),
a amostra são rotas de alta qualidade de Los Angeles em 2018 e o motorista pode ter razões que a base não registra.
Detalhes na seção 5 do relatório.

## Autores

Maycon, Caua, Dyogo e Arielce. Professor: Dr. Emerson A. Carvalho.
