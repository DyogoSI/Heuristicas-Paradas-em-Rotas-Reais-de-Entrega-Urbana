import sys, pickle, collections
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Preformatted

S = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, S)
import heur2 as H

routes = H.load_routes()
d = pickle.load(open(S + '/resultados2.pkl', 'rb'))
res, gaps, longr = d['res'], d['gaps'], d['long']
NR = len(routes)
NS = sum(R['n'] - 1 for R in routes)
NW = res['actual'][0]['nw'] and sum(x['nw'] for x in res['actual'])
stations = collections.Counter(R['station'] for R in routes)
ndays = len(set(R['date'] for R in routes))
dmin, dmax = min(R['date'] for R in routes), max(R['date'] for R in routes)
stops = [R['n'] - 1 for R in routes]
occ = [x['occ'] for x in res['actual']]


def mean(k, f):
    return float(np.mean([x[f] for x in res[k]]))


def red(k):
    return [100 * (1 - b['travel'] / a['travel']) for a, b in zip(res['actual'], res[k])]


def viol(k):
    return sum(x['viol'] for x in res[k])


def routes_viol(k):
    return sum(1 for x in res[k] if x['viol'] > 0)


def f(x, n=0):
    return f'{x:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def dd(s):
    return f'{s[8:10]}/{s[5:7]}/{s[0:4]}'


r_tw, r_ls, r_nn, r_ci, r_cils = red('nn_tw'), red('nn_ls'), red('nn'), red('ci'), red('ci_ls')
tot_real = sum(x['travel'] for x in res['actual'])
tot_prop = sum(x['travel'] for x in res['nn_tw'])
saved_min = tot_real - tot_prop
maxms = max(x['ms'] for x in res['nn_tw'])
maxtot = max(x['total'] for x in res['nn_tw'])
maxtot_real = max(x['total'] for x in res['actual'])

st = {}
st['n'] = ParagraphStyle('n', fontName='Helvetica', fontSize=10.5, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
st['b'] = ParagraphStyle('b', parent=st['n'], leftIndent=14, bulletIndent=2, spaceAfter=3)
st['h1'] = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=13, leading=17, spaceBefore=12, spaceAfter=6)
st['h2'] = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11.2, leading=15, spaceBefore=8, spaceAfter=4)
st['c'] = ParagraphStyle('c', parent=st['n'], alignment=TA_CENTER)
st['cap'] = ParagraphStyle('cap', fontName='Helvetica-Oblique', fontSize=9, leading=11.5, alignment=TA_CENTER, spaceAfter=8)
st['t'] = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=10)
st['tc'] = ParagraphStyle('tc', fontName='Helvetica', fontSize=11, leading=15, alignment=TA_CENTER)
st['cell'] = ParagraphStyle('cell', fontName='Helvetica', fontSize=8.3, leading=10.2)
st['cellb'] = ParagraphStyle('cellb', fontName='Helvetica-Bold', fontSize=8.3, leading=10.2)
st['code'] = ParagraphStyle('code', fontName='Courier', fontSize=8.4, leading=10.8)
P = lambda t, s='n': Paragraph(t, st[s])
B = lambda t: Paragraph(t, st['b'], bulletText='•')
story = []

# ---------- capa ----------
story += [Spacer(1, 1.2 * cm),
          P('INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO SUL DE MINAS GERAIS', 'tc'),
          P('CAMPUS MACHADO', 'tc'), Spacer(1, .4 * cm), P('Ciência de Dados', 'tc'), Spacer(1, .6 * cm),
          P('Trabalho 02 - Criação de uma heurística baseada em dados', 'tc'), Spacer(1, 1.6 * cm),
          P('Sequenciamento Heurístico de Paradas em Rotas Reais de Entrega Urbana', 't'),
          P('Redução do tempo de deslocamento de veículos de entrega usando dados públicos reais de rotas, pacotes e tempos de viagem '
            '(Amazon Last Mile Routing Research Challenge), respeitando capacidade, janelas de horário e jornada', 'tc'),
          Spacer(1, 1.6 * cm), P('<b>Alunos(as)</b>', 'tc'), P('Maycon<br/>Caua<br/>Dyogo<br/>Arielce', 'tc'),
          Spacer(1, 1 * cm), P('Professor: Dr. Emerson A. Carvalho', 'tc'), P('Data de entrega: 22/10/2026', 'tc'),
          P('Machado - MG, 2026', 'tc'), PageBreak()]

# ---------- resumo ----------
story += [P('Resumo', 'h1'),
          P(f'Este trabalho propõe uma heurística baseada em dados para o sequenciamento das paradas de rotas de entrega urbana. '
            f'Todos os dados são públicos e reais: usamos {NR} rotas de {len(stations)} estações de entrega de Los Angeles '
            f'({f(NS)} paradas, {ndays} dias entre {dd(dmin)} e {dd(dmax)}) da base Amazon Last Mile Routing Research Challenge, que traz '
            f'coordenadas das paradas, dimensões e tempos de serviço dos pacotes, janelas de horário, capacidade do veículo, tempos de '
            f'viagem entre todas as paradas e a sequência que o motorista realmente percorreu. Como o problema é NP-difícil (variante do '
            f'caixeiro-viajante com janelas de horário), a proposta combina a construção por vizinho mais próximo, com urgência para janelas, '
            f'e a busca local 2-opt e Or-opt, que só aceita trocas que não aumentem as violações de janela. Comparada à sequência real do '
            f'motorista, a abordagem reduziu em média {f(np.mean(r_tw), 1)}% o tempo de deslocamento '
            f'(de {f(mean("actual", "travel"), 0)} para {f(mean("nn_tw", "travel"), 0)} min por rota), foi melhor em '
            f'{sum(1 for r in r_tw if r > 0)} das {NR} rotas e baixou as janelas violadas de {viol("actual")} para {viol("nn_tw")} '
            f'(em {f(NW)} paradas com janela), com cerca de {f(mean("nn_tw", "ms") / 1000, 1)} s por rota. O relatório descreve o problema, '
            f'os objetivos, o método, as métricas, as limitações e os dados.'),
          P('<b>Palavras-chave:</b> heurística, roteirização de veículos, entrega urbana, janelas de horário, 2-opt, Or-opt.'),
          P('1. Qual problema geral será resolvido? (descrição geral)', 'h1'),
          P('O problema é decidir em que ordem um veículo de entrega deve visitar as paradas que lhe foram atribuídas no dia, de modo a '
            'entregar todos os pacotes gastando o mínimo de tempo de deslocamento possível, sem estourar a capacidade do veículo, a jornada e, '
            'sempre que possível, as janelas de horário prometidas aos clientes. Na literatura, é uma variante do problema do caixeiro-viajante '
            'com janelas de horário, que faz parte da família dos problemas de roteirização de veículos (Dantzig e Ramser, 1959; Toth e Vigo, 2014). '
            'É NP-difícil: o número de sequências possíveis cresce de forma fatorial com o número de paradas (uma rota típica tem mais de '
            '100), de modo que testar todas as possibilidades é impraticável. Por isso se recorre a métodos aproximados.'),
          P('Hoje, a ordem das paradas costuma ser definida pela experiência do motorista ou por regras simples, e raramente é reotimizada '
            'a cada dia. O resultado são trajetos com idas e voltas desnecessárias, mais tempo de rua, mais combustível e mais risco de atraso.'),
          P('1.1 Qual o domínio/negócio em que o problema está inserido?', 'h2'),
          P('O domínio é a logística de última milha do comércio eletrônico: o trecho final em que o pacote sai de uma estação de distribuição '
            'e chega ao cliente. É a etapa mais cara da cadeia de entrega e a mais sensível à escolha de rota, porque envolve muitas paradas '
            'próximas, tempo de serviço em cada uma e compromissos de horário. O mesmo problema ocorre em entregas de farmácias, '
            'supermercados, correspondências e abastecimento escolar na nossa região, o que torna o método transferível.'),
          P('<b>Por que esta base.</b> Esta é uma base pública e real de rotas executadas, publicada pela Amazon (licença CC BY-NC 4.0, '
            'uso não comercial) para pesquisa acadêmica. Diferente de dados simulados, ela traz a rota que o motorista de fato fez, o que '
            'permite um benchmark real e não uma referência inventada.'),
          P('1.2 Cenário, usuários e atores impactados', 'h2'),
          P(f'Pergunta orientadora: qual é o cenário e quem são os impactados? O cenário é o de estações de distribuição que despacham, a cada '
            f'dia, dezenas de rotas com {min(stops)} a {max(stops)} paradas (mediana de {f(float(np.median(stops)))}), em veículos com cerca de '
            f'3,3 m³ de capacidade de carga. Os atores são:'),
          B('<b>Equipe de planejamento de rotas:</b> precisa de uma ferramenta rápida e explicável, que possa recalcular a ordem a cada mudança.'),
          B('<b>Motoristas:</b> têm jornada limitada e se beneficiam de rotas com menos deslocamento e sem retornos desnecessários.'),
          B('<b>Clientes:</b> esperam receber dentro da janela de horário combinada.'),
          B('<b>Gestão financeira e ambiental:</b> combustível e horas de motorista são os maiores custos; menos tempo de rua significa menos emissões.'),
          P('<b>Como os dados ajudam:</b> as coordenadas, os tempos de viagem medidos entre todos os pares de paradas, os tempos de serviço e as '
            'janelas permitem calcular o custo de qualquer sequência e avaliar objetivamente se ela é viável, comparando-a com a ordem real '
            'adotada pelo motorista.')]

# ---------- 2 ----------
story += [P('2. Quais os objetivos da heurística?', 'h1'),
          P('<b>Objetivo geral:</b> gerar, em poucos segundos, a sequência de paradas de cada rota que minimize o tempo total de deslocamento, '
            'atendendo todas as paradas.'),
          P('<b>Restrições obrigatórias</b> (uma sequência que as viole é descartada):'),
          B('<b>Cobertura:</b> toda parada da rota deve ser visitada exatamente uma vez, e a rota começa na estação de distribuição (rota aberta, '
            'termina na última parada).'),
          B('<b>Capacidade:</b> o volume total dos pacotes não pode passar da capacidade do veículo informada na base (cm³). Como o conjunto de '
            f'paradas de cada rota é dado, a restrição é verificada, não otimizada (ocupação real média de {f(np.mean(occ))}%).'),
          B('<b>Jornada:</b> deslocamento mais tempo de serviço de uma rota não pode passar de 10 horas (limite assumido; a maior rota real '
            f'tem {f(maxtot_real, 1)} h).'),
          P('<b>Restrição suave:</b> as janelas de horário dos pacotes. Elas são contadas como violação quando o veículo chega depois do fim da '
            'janela; chegar antes do início implica esperar. A meta é não aumentar as violações em relação ao motorista.'),
          P('<b>Objetivos secundários</b>, em ordem de prioridade: (i) minimizar violações de janela, (ii) manter a sequência explicável e '
            '(iii) obter a solução em segundos, de modo que possa ser recalculada quando uma parada entra ou sai.'),
          P(f'<b>Como definimos sucesso:</b> consideramos a heurística bem-sucedida se, nas {NR} rotas de teste, ela (a) reduzir o tempo de '
            f'deslocamento em pelo menos 5% em média em relação à sequência real do motorista (a referência é exigente, pois são rotas de motoristas '
            f'experientes), (b) nunca gerar rota inviável (cobertura, capacidade e jornada) e não ter mais violações de janela que o motorista, e '
            f'(c) rodar em menos de 5 segundos por rota.')]

# ---------- 3 ----------
story += [P('3. Qual a solução (método) proposta?', 'h1'),
          P('A solução é uma heurística em duas fases, construção e melhoria, que usa a matriz de tempos de viagem, os tempos de serviço e as '
            'janelas de horário para orientar cada decisão.'),
          P('3.1 Fase 1: construção pelo vizinho mais próximo com urgência', 'h2'),
          P('Partindo da estação, o veículo vai sempre para a parada ainda não visitada com menor tempo de viagem (Rosenkrantz et al., 1977). '
            'Para respeitar as janelas, antes de cada escolha verifica-se se alguma parada com janela está prestes a vencer (folga menor que '
            '15 minutos sobre o instante estimado de chegada); se sim, vai-se primeiro à mais urgente. Também se simula a espera quando o '
            'veículo chega antes do início da janela.'),
          P('3.2 Fase 2: melhoria com busca local 2-opt e Or-opt', 'h2'),
          P('O 2-opt (Croes, 1958) escolhe dois pontos da sequência e inverte o trecho entre eles. O Or-opt (Or, 1976) move um bloco de 1 a 3 '
            'paradas consecutivas para outra posição. Como os tempos de viagem são assimétricos (ida e volta diferem), os ganhos são '
            'calculados com somas acumuladas dos tempos nos dois sentidos. Uma troca só é aceita se reduzir o tempo de deslocamento '
            '<b>e</b> não aumentar o número de janelas violadas; o processo repete até nenhuma troca ser aceita.'),
          P('3.3 Pseudocódigo', 'h2')]
code = """1  T <- matriz de tempos de viagem (estacao + N paradas), s <- tempos de servico
2  seq <- [estacao]
3  enquanto houver parada nao visitada:
4      u <- parada com janela e folga < 15 min (a de menor folga)
5      se nao existe u: u <- parada nao visitada de menor T[ultima, u]
6      acrescentar u a seq; atualizar relogio (esperar se chegou antes da janela)
7  v <- violacoes_de_janela(seq)
8  repetir ate nao haver troca aceita:
9      para cada troca candidata (2-opt ou Or-opt):
10         se reduz o tempo de deslocamento e violacoes(nova) <= v:
11             aplicar a troca; atualizar v; reiniciar a varredura
12 retornar seq"""
story += [Preformatted(code, st['code']), Spacer(1, 6),
          P('3.4 Como os dados orientam o processo', 'h2'),
          B('Os tempos de viagem medidos entre todos os pares de paradas (base travel_times) definem o custo de cada trecho, inclusive a assimetria.'),
          B('Os tempos de serviço (soma do tempo planejado de cada pacote da parada) e as janelas de horário alimentam o relógio simulado.'),
          B('As dimensões dos pacotes dão o volume da rota, comparado à capacidade do veículo.'),
          B('A sequência real do motorista (actual_sequences) serve de referência de comparação.'),
          P('3.5 Justificativa da escolha', 'h2'),
          B('<b>Adequação ao problema:</b> construção gulosa seguida de busca local é o esquema clássico para o caixeiro-viajante e suas variantes, '
            'e permite embutir a regra de proteção das janelas na própria busca.'),
          B('<b>Eficiência:</b> o 2-opt com somas acumuladas avalia cada troca em tempo constante; rotas de 55 a 197 paradas rodam em segundos em Python puro.'),
          B('<b>Simplicidade e explicabilidade:</b> não requer solver comercial nem treino de modelo; o planejador entende "vai para o mais próximo e '
            'depois desfaz os cruzamentos".'),
          B('<b>Qualidade reconhecida:</b> a busca local 2-opt + Or-opt costuma ficar a poucos pontos percentuais do ótimo em instâncias desse porte (Toth e Vigo, 2014).'),
          P('3.6 Resultado em dados reais', 'h2'),
          P(f'Executamos todos os métodos sobre as {NR} rotas reais descritas acima (as primeiras {NR} rotas de alta qualidade, "score High", de '
            f'estações de Los Angeles na ordem do arquivo; ver seção 6). Para cada rota comparamos o tempo de deslocamento da sequência '
            f'gerada com o da sequência real do motorista, ambos calculados na mesma matriz de tempos reais. Os números abaixo são médias das {NR} rotas.')]

rows = [['Método', 'Deslocamento\n(min/rota)', 'Redução vs.\nmotorista', 'Rotas\nmelhores', 'Jornada\n(h)', 'Janelas\nviolad.', 'Tempo\n(ms)']]
labels = [('actual', 'Sequência real do motorista (referência)', None), ('nn', 'Vizinho mais próximo', r_nn),
          ('ci', 'Inserção mais barata', r_ci), ('ci_ls', 'Inserção + 2-opt + Or-opt', r_cils),
          ('nn_ls', 'Vizinho + 2-opt + Or-opt', r_ls), ('nn_tw', 'Proposta: vizinho com urgência + 2-opt + Or-opt com proteção de janelas', r_tw)]
for k, l, r in labels:
    rows.append([Paragraph(l, st['cell']), f(mean(k, 'travel'), 1),
                 ('-' if r is None else f(np.mean(r), 1) + '%'), ('-' if r is None else f'{sum(1 for x in r if x > 0)}/{NR}'),
                 f(mean(k, 'total'), 2), f'{viol(k)} ({f(100 * viol(k) / NW, 1)}%)', f(mean(k, 'ms'), 0)])
tb = Table(rows, colWidths=[5.3 * cm, 2.1 * cm, 2 * cm, 1.7 * cm, 1.5 * cm, 2.2 * cm, 1.4 * cm], repeatRows=1)
tb.setStyle(TableStyle([('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8), ('FONT', (1, 1), (-1, -1), 'Helvetica', 8.4),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dde6f0')), ('GRID', (0, 0), (-1, -1), .4, colors.grey),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#eef6e9'))]))
story += [tb, P(f'Tabela 1 - Comparação dos métodos em {NR} rotas reais ({f(NS)} paradas). Jornada = deslocamento + serviço. Janelas violadas '
                f'em {f(NW)} paradas com janela.', 'cap'),
          Image(S + '/fig1_rota.png', width=16.5 * cm, height=16.5 * cm * 5.2 / 11 * 0.97),
          P('Figura 1 - Uma rota real mediana (estação DLA3): sequência do motorista (esquerda) e da proposta (direita). A cor indica a ordem de visita; '
            'a estação fica fora do quadro, no canto inferior direito. As linhas ligam as paradas em linha reta (não representam as ruas).', 'cap'),
          Image(S + '/fig2_tempo.png', width=12.5 * cm, height=12.5 * cm * 4.2 / 8.8),
          P('Figura 2 - Tempo de deslocamento médio por método.', 'cap'),
          Image(S + '/fig3_hist.png', width=12.5 * cm, height=12.5 * cm * 3.6 / 8.8),
          P('Figura 3 - Distribuição da redução de tempo da proposta sobre a sequência real, rota a rota.', 'cap'),
          P(f'A heurística proposta reduziu em média <b>{f(np.mean(r_tw), 1)}%</b> o tempo de deslocamento '
            f'(mínimo {f(min(r_tw), 1)}%, máximo {f(max(r_tw), 1)}%), o que corresponde a {f(mean("actual", "travel") - mean("nn_tw", "travel"), 1)} '
            f'minutos por rota e {f(saved_min / 60, 1)} horas de direção nas {NR} rotas, de um total de {f(tot_real / 60, 0)} h. Foi melhor que o motorista em '
            f'{sum(1 for r in r_tw if r > 0)} das {NR} rotas. A busca local é o que faz a diferença: a construção sozinha (vizinho mais próximo) '
            f'ficou {f(abs(np.mean(r_nn)), 1)}% pior que o motorista, e a inserção mais barata ganhou apenas {f(np.mean(r_ci), 1)}%. '
            f'As {NR} rotas foram viáveis (cobertura, capacidade e jornada: a maior rota levou {f(maxtot, 2)} h).'),
          P(f'<b>Resultado sobre as janelas de horário:</b> o motorista violou {viol("actual")} janelas em {routes_viol("actual")} rotas. '
            f'A mesma busca local sem proteção ({f(np.mean(r_ls), 1)}% de redução) aumentaria as violações para {viol("nn_ls")}, em {routes_viol("nn_ls")} rotas, '
            f'porque ignora as janelas ao reordenar. Com a proteção, a proposta teve {viol("nn_tw")} violação, perdendo apenas '
            f'{f(np.mean(r_ls) - np.mean(r_tw), 1)} ponto percentual de redução. O ganho de tempo, portanto, não foi obtido às custas dos clientes.'),
          P(f'<b>Resultados desfavoráveis, que não devem ser omitidos:</b> (1) em {sum(1 for r in r_tw if r <= 0)} rota a proposta ficou pior que o motorista '
            f'(mínimo {f(min(r_tw), 1)}%); (2) o tempo de execução médio é de {f(mean("nn_tw", "ms") / 1000, 1)} s e chegou a {f(maxms / 1000, 1)} s na pior rota, '
            f'bem acima do vizinho mais próximo puro ({f(mean("nn", "ms"), 0)} ms), embora dentro do limite de 5 s; (3) o motorista pode '
            f'ter razões que a base não registra (estacionamento, acesso, familiaridade), então a sequência mais rápida no papel não é '
            f'necessariamente melhor na rua.')]

# ---------- 4 ----------
story += [P('4. Quais as métricas para avaliar se a solução é satisfatória?', 'h1'),
          P('Pergunta orientadora: como mediremos a eficiência e qual o critério de "bom o suficiente"? Usamos métricas de custo, de '
            'qualidade da solução, de viabilidade e de tempo. A última coluna confronta cada critério com o resultado obtido.')]
mt = [['Métrica', 'O que mede', 'Critério de sucesso', 'Resultado'],
      ['Tempo de deslocamento (min/rota)', 'Custo principal: horas de motorista, combustível, desgaste', 'Redução média de pelo menos 5% frente ao motorista',
       f'{f(np.mean(r_tw), 1)}% (atingido)'],
      ['Rotas em que a proposta supera o motorista', 'Consistência do ganho', 'Maioria das rotas', f'{sum(1 for r in r_tw if r > 0)} de {NR} (atingido)'],
      ['Janelas de horário violadas', 'Qualidade do serviço ao cliente', 'Não mais que o motorista', f'{viol("nn_tw")} contra {viol("actual")} (atingido)'],
      ['Maior jornada de rota (h)', 'Respeito à jornada', 'Menor ou igual a 10 h em 100% das rotas', f'{f(maxtot, 2)} h (atingido)'],
      ['Taxa de rotas viáveis (%)', 'Cobertura, capacidade e jornada', '100%', '100% (atingido)'],
      ['Gap em relação a uma busca mais longa (%)', 'Distância da solução à melhor encontrada por ILS (perturbação + busca local)', 'Até 10% de gap',
       f'média {f(np.mean(gaps), 1)}%, máx. {f(max(gaps), 1)}% em {len(gaps)} rotas (atingido)'],
      ['Tempo de execução (s/rota)', 'Viabilidade operacional do recálculo', 'Menos de 5 s', f'média {f(mean("nn_tw", "ms") / 1000, 1)} s, máx. {f(maxms / 1000, 1)} s (atingido)'],
      ['Custo estimado (R$ ou US$ por parada)', 'Impacto financeiro: tempo economizado x custo/hora', 'Redução proporcional à do tempo', 'Requer custo/hora real']]
mt = [[Paragraph(c, st['cellb' if i == 0 else 'cell']) for c in row] for i, row in enumerate(mt)]
tb2 = Table(mt, colWidths=[3.5 * cm, 4.6 * cm, 3.9 * cm, 4.5 * cm], repeatRows=1)
tb2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dde6f0')), ('GRID', (0, 0), (-1, -1), .4, colors.grey),
                         ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
story += [tb2, P('Tabela 2 - Métricas de avaliação.', 'cap'),
          P('<b>Estratégia de comparação:</b> (i) contra a sequência real do motorista, o benchmark operacional (rotas de motoristas experientes); (ii) contra '
            'heurísticas mais simples (vizinho mais próximo e inserção mais barata); (iii) contra uma busca mais longa, o ILS (iterated local search), '
            f'com 30 perturbações do tipo double-bridge seguidas de busca local, aplicada a {len(gaps)} rotas para estimar o quanto ainda se perde '
            f'(o gap foi medido sobre a versão sem proteção de janelas, que usa a mesma busca).'),
          P(f'Como exemplo de conversão em valor: {f(saved_min / 60, 1)} horas de direção economizadas em {NR} rotas equivalem a '
            f'{f(saved_min / NR, 1)} minutos por rota. Multiplicados pelo custo por hora do motorista e do veículo (valor a ser informado pela '
            f'operação), dão a economia; o combustível economizado seria proporcional ao tempo, de forma aproximada.')]

# ---------- 5 ----------
story += [P('5. Quais as limitações da heurística proposta?', 'h1'),
          P('Pergunta orientadora: em que casos ela pode não funcionar bem e quais limites de tempo, recursos ou dados afetam a qualidade?'),
          B('<b>Não garante o ótimo.</b> A construção é gulosa e a busca local pode parar em um ótimo local; o ILS achou ainda até '
            f'{f(max(gaps), 1)}% a menos (média {f(np.mean(gaps), 1)}%) em {len(gaps)} rotas.'),
          B('<b>Só sequencia, não distribui.</b> A base já entrega as paradas agrupadas por rota e os tempos de viagem existem apenas entre paradas '
            'da mesma rota; por isso não é possível trocar paradas entre rotas nem decidir quantos veículos usar. Como a ocupação real '
            f'é de {f(np.mean(occ))}% (variando de {f(min(occ))}% a {f(max(occ))}%), a restrição de capacidade nunca ficou ativa, e '
            'o lado "capacitado" do problema não é testado.'),
          B('<b>Janelas tratadas de forma simplificada.</b> Usamos a janela mais restritiva entre os pacotes de cada parada e contamos só as chegadas '
            f'tardias; apenas {f(100 * NW / NS, 1)}% das paradas têm janela, e a verificação depende do tempo de serviço planejado, não do realizado.'),
          B('<b>Tempos de viagem estáticos.</b> A matriz traz um tempo por par de paradas, sem variação por horário, trânsito ou clima.'),
          B('<b>Amostra restrita.</b> São as primeiras 100 rotas "High" de seis estações de Los Angeles em 2018. Rotas "Medium" e "Low", outras '
            'cidades e outros países, como o Brasil, podem se comportar diferente. Rotas de motoristas de alta qualidade são uma referência difícil; '
            'não testamos rotas de qualidade média ou baixa.'),
          B('<b>Conhecimento tácito do motorista.</b> Motoristas podem seguir preferências que não estão '
            'nos dados (ordem de zonas, acessos, estacionamento); a heurística minimiza tempo e pode contrariar essas preferências.'),
          B(f'<b>Tempo de execução.</b> A implementação em Python puro leva em média {f(mean("nn_tw", "ms") / 1000, 1)} s por rota; para milhares de paradas '
            'seria preciso uma implementação compilada ou estruturas de vizinhança mais eficientes.'),
          B('<b>Licença.</b> A base é CC BY-NC 4.0: uso acadêmico, não comercial.'),
          P('<b>Melhorias previstas:</b> otimizar a atribuição de paradas entre rotas (exige matriz entre rotas), tratar as janelas como restrição forte, '
            'aprender as preferências do motorista a partir das sequências reais e usar meta-heurísticas (ILS ou busca tabu) quando o tempo permitir.')]

# ---------- 6 ----------
story += [P('6. Quais são os dados necessários e como serão obtidos?', 'h1'),
          P('Pergunta orientadora: quais dados apoiarão a solução, como acessá-los e se são suficientes? Todos os dados abaixo são públicos, reais e '
            'foram efetivamente usados neste trabalho.')]
dt = [['Dado', 'Uso na heurística', 'Fonte / obtenção', 'Tratamento'],
      ['Rotas: estação, data, horário de saída, capacidade (cm³), paradas com coordenadas e tipo', 'Define o problema de cada rota e o ponto de partida',
       'route_data.json (Amazon Last Mile, 6.112 rotas de treino)', f'Filtro: score High, estações DLA*; primeiras {NR} rotas'],
      ['Pacotes por parada: dimensões, tempo de serviço planejado, janela de horário, status', 'Volume da rota (capacidade), relógio de serviço e janelas',
       'package_data.json', 'Soma por parada; janela mais restritiva; volume = profundidade x altura x largura'],
      ['Tempos de viagem entre todas as paradas da rota (s)', 'Custo de cada trecho, incluindo assimetria', 'travel_times.json', 'Leitura em streaming; só as rotas escolhidas'],
      ['Sequência real percorrida pelo motorista', 'Benchmark operacional de comparação', 'actual_sequences.json', 'Ordenar paradas pelo índice de visita'],
      ['Jornada máxima', 'Limite de 10 h por rota', 'Hipótese de trabalho (a maior rota real tem ' + f(maxtot_real, 1) + ' h)', 'Parametrizável'],
      ['Custo por hora do motorista e do veículo', 'Conversão de tempo em dinheiro', 'Não disponível na base', 'Não usado']]
dt = [[Paragraph(c, st['cellb' if i == 0 else 'cell']) for c in row] for i, row in enumerate(dt)]
tb3 = Table(dt, colWidths=[4.6 * cm, 3.7 * cm, 4.2 * cm, 4 * cm], repeatRows=1)
tb3.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dde6f0')), ('GRID', (0, 0), (-1, -1), .4, colors.grey),
                         ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
st_txt = ', '.join(f'{k} ({v})' for k, v in sorted(stations.items()))
story += [tb3, P('Tabela 3 - Dados necessários.', 'cap'),
          P(f'<b>Acesso:</b> os arquivos estão no bucket público amazon-last-mile-challenges (AWS Open Data), pasta almrrc2021, sem necessidade de cadastro. '
            f'Os arquivos route_data (79 MB) e actual_sequences (9,7 MB) foram baixados por inteiro; package_data (375 MB) e travel_times (1,8 GB) foram lidos '
            f'em streaming, guardando só as {NR} rotas escolhidas. Estações incluídas: {st_txt}. Período: {dd(dmin)} a {dd(dmax)}.'),
          P('<b>Pré-processamento:</b> (1) filtrar as rotas de interesse; (2) construir, para cada rota, a matriz de tempos, o vetor de tempos de serviço, '
            'o volume e as janelas por parada; (3) calcular o tempo da sequência real como referência; (4) executar a heurística; (5) validar cobertura, '
            'capacidade, jornada e janelas; (6) comparar com a referência e com os demais métodos.'),
          P('<b>Os dados são suficientes?</b> Para o problema de sequenciamento, sim: a base traz os custos reais, as restrições e a rota executada, '
            'sem nenhuma hipótese sobre demanda ou frota. Para estudar atribuição de paradas entre veículos, trânsito dinâmico e preferências '
            'do motorista, seria preciso acrescentar matrizes de tempo entre rotas e dados de telemetria.'),
          P('Conclusão', 'h1'),
          P(f'O sequenciamento de paradas de entrega é um problema real, de custo relevante e computacionalmente difícil, em que uma heurística simples e '
            f'explicável traz ganhos. Sobre {NR} rotas reais e públicas, a combinação de vizinho mais próximo com urgência, 2-opt e Or-opt com proteção '
            f'de janelas gerou sequências viáveis que reduziram em média {f(np.mean(r_tw), 0)}% o tempo de deslocamento em relação ao motorista, '
            f'com {viol("nn_tw")} janela violada contra {viol("actual")}, em cerca de {f(mean("nn_tw", "ms") / 1000, 1)} s por rota. As limitações '
            f'(só sequenciamento, capacidade não ativa, janelas simplificadas, amostra de Los Angeles em 2018 e preferências do motorista fora dos dados) '
            f'indicam os próximos passos: testar rotas de menor qualidade, incluir reatribuição de paradas e validar com a operação de uma empresa da região.'),
          P('Referências', 'h1'),
          B('CLARKE, G.; WRIGHT, J. W. Scheduling of vehicles from a central depot to a number of delivery points. Operations Research, v. 12, n. 4, p. 568-581, 1964.'),
          B('CROES, G. A. A method for solving traveling-salesman problems. Operations Research, v. 6, n. 6, p. 791-812, 1958.'),
          B('DANTZIG, G. B.; RAMSER, J. H. The truck dispatching problem. Management Science, v. 6, n. 1, p. 80-91, 1959.'),
          B('MERCHÁN, D. et al. 2021 Amazon Last Mile Routing Research Challenge: Data Set. Transportation Science, v. 58, n. 1, p. 8-11, 2024. '
            'Dados: amazon-last-mile-challenges.s3.amazonaws.com, licença CC BY-NC 4.0.'),
          B('OR, I. Traveling salesman-type combinatorial problems and their relation to the logistics of regional blood banking. '
            'Tese (Doutorado), Northwestern University, 1976.'),
          B('ROSENKRANTZ, D. J.; STEARNS, R. E.; LEWIS, P. M. An analysis of several heuristics for the traveling salesman problem. '
            'SIAM Journal on Computing, v. 6, n. 3, p. 563-581, 1977.'),
          B('TOTH, P.; VIGO, D. (ed.). Vehicle Routing: Problems, Methods, and Applications. 2. ed. Philadelphia: SIAM, 2014.')]


def footer(c, doc):
    c.saveState()
    c.setFont('Helvetica', 8)
    c.drawString(2 * cm, 1.1 * cm, 'IFSULDEMINAS - Campus Machado | Ciência de Dados | Trabalho 02 - Heurística baseada em dados')
    c.drawRightString(19 * cm, 1.1 * cm, str(doc.page))
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
                        title='Sequenciamento Heurístico de Paradas em Rotas Reais de Entrega Urbana', author='Maycon, Caua, Dyogo, Arielce')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('pdf ok')
