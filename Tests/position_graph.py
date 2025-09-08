import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg
import numpy as np
import math
import random
import networkx as nx
import numpy as np

xmax = 600
ymax = 400
maxDist =90.1456151562057

plt.ion()
plt.figure()
ax = plt.gcf().gca()
ax.add_patch(Rectangle((0, 0), xmax, ymax, fill=None, alpha=1))

#prepare show
plt.xlim([0, xmax])
plt.ylim([0, ymax])
plt.draw()
plt.show()

nodes = []
graph_file = open("graph_file.txt", "w")

class Graph():
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[0 for column in range(vertices)]
                      for row in range(vertices)]
        
    def printSolution(self, dist, src):
        print("\nNode \t Distance from GW (Node ", src, ")")
        for node in range(self.V):
            print(node, "\t\t", dist[node])

    def minDistance(self, dist, sptSet):
        min = 1e7
        for v in range(self.V):
            if dist[v] < min and sptSet[v] == False:
                min = dist[v]
                min_index = v
        return min_index
        
    def dijkstra(self, src):
        dist = [1e7] * self.V
        dist[src] = 0
        sptSet = [False] * self.V
        for cout in range(self.V):
            u = self.minDistance(dist, sptSet)
            sptSet[u] = True
            for v in range(self.V):
                if (self.graph[u][v] > 0 and 
                    sptSet[v] == False and 
                    dist[v] > dist[u] + self.graph[u][v]):
                    dist[v] = dist[u] + self.graph[u][v]
        
        self.printSolution(dist, src)
        return dist


class Node():
    def __init__(self, x, y, type):
        global nodes
        global ax
        nodes.append(self)
        self.id = len(nodes)-1
        self.x = x
        self.y = y
        self.type = type.lower() 

        self.iconSettings = {'ed':[5,'blue'], 'rl':[5,'lightgreen'], 'rp':[5,'green'], 'gw':[5,'red']}
        self.icon = plt.Circle((self.x, self.y), self.iconSettings[self.type][0], fill=True, color=self.iconSettings[self.type][1])
        self.label = plt.text(self.x+11,self.y,self.id)
        ax.add_artist(self.icon)
        ax.add_artist(self.label)

        self.neighbor_ids = []
        self.neighbor_rssi = []

    def learn_local_positions(self):
        self.neighbor_rssi = [0 for x in range(len(nodes))]
        # for i in range(self.id-2,self.id+3):
        #     if(i>=0 and i<len(nodes) and i != self.id):
        #         self.neighbor_rssi[i] = calc_rssi(nodes[i],nodes[self.id])
        for i in range(len(nodes)):
            if(i != self.id):
                d = np.sqrt((nodes[i].x-self.x)*(nodes[i].x-self.x) +(nodes[i].y-self.y)*(nodes[i].y-self.y))
                if(d<= maxDist):
                    self.neighbor_rssi[i] = calc_rssi(nodes[i],nodes[self.id])
                    self.neighbor_ids.append(i)


def calc_rssi(tx, rx):
    d = np.sqrt((tx.x-rx.x)*(tx.x-rx.x)+(tx.y-rx.y)*(tx.y-rx.y))
    Ptx = 14
    gamma = 2.08
    d0 = 40.0
    Lpld0 = 127.41
    GL = 0
    if(d != 0):
        Lpl = Lpld0 + 10*gamma*math.log10(d/d0)
    else:
        Lpl = 0
    rssi = Ptx - GL - Lpl
    return rssi + random.uniform(-1, 1)
    
def calc_dist(rssi):
    Ptx = 14
    gamma = 2.08
    d0 = 40.0
    Lpld0 = 127.41
    GL = 0
    Lpl = Ptx -GL -rssi
    d = pow(10,(Lpl -Lpld0)/(10*gamma))*d0
    return d

def plot_weighted_directed_graph(adj_matrix, node_labels=None):
    """
    Plots a weighted, directed graph from an adjacency matrix where A->B and B->A can both exist.

    Parameters:
    - adj_matrix (2D list or np.array): Weighted adjacency matrix. Zero means no edge.
    - node_labels (list): Optional list of labels for nodes.

    Returns:
    - None
    """
    adj_matrix = np.array(adj_matrix)
    G = nx.DiGraph()

    num_nodes = adj_matrix.shape[0]
    G.add_nodes_from(range(num_nodes))

    # Add edges with weights
    for i in range(num_nodes):
        for j in range(num_nodes):
            weight = int(adj_matrix[i, j])
            if weight != 0:
                G.add_edge(i, j, weight=weight)

    labels = {i: node_labels[i] for i in range(num_nodes)} if node_labels else None
    # pos = nx.spring_layout(G)
    pos = nx.spring_layout(G, k=0.8, iterations=100000)

    # Draw nodes and labels
    nx.draw_networkx_nodes(G, pos, node_color='lightgreen', node_size=1000)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=12)

    # Draw edges with curved style to distinguish bidirectional links
    curved_edges = [edge for edge in G.edges() if G.has_edge(edge[1], edge[0])]
    straight_edges = [edge for edge in G.edges() if edge not in curved_edges]

    nx.draw_networkx_edges(G, pos, edgelist=straight_edges, arrowstyle='->', arrowsize=20)
    nx.draw_networkx_edges(G, pos, edgelist=curved_edges, arrowstyle='->', connectionstyle='arc3,rad=0.2', arrowsize=20)

    # Draw edge weights
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights)

    plt.title("Weighted Directed Graph with Bidirectional Edges")
    plt.axis('off')
    plt.show()

#network 1
# Node(1000,500, "gw")
# Node(900, 500, "rp")
# Node(800, 500, "rp")
# Node(700, 500, "rp")
# Node(600, 500, "rp")
# Node(500, 500, "rp")
# Node(500, 600, "rp")
# Node(500, 700, "rp")
# Node(500, 800, "rp")
# Node(500, 900, "rp")

# Node(400, 500, "rp")
# Node(300, 500, "rp")
# Node(200, 500, "rp")
# Node(100, 500, "rp")

# Node(500, 1000, "gw")

repeaters =[]
enddevices = []

#Repeaters
d = maxDist*0.99

gw1 = Node(6.00*d, 1.00*d, "gw")

repeaters.append(Node(5.50*d, 1.00*d, "rp"))
repeaters.append(Node(5.00*d, 1.00*d, "rp"))
repeaters.append(Node(4.50*d, 1.00*d, "rp"))
repeaters.append(Node(4.00*d, 1.00*d, "rp"))
repeaters.append(Node(3.50*d, 1.00*d, "rp")) #junction 1
repeaters.append(Node(3.00*d, 1.00*d, "rp"))
repeaters.append(Node(2.66*d, 1.00*d, "rp"))
repeaters.append(Node(2.33*d, 1.00*d, "rp")) #junction 2
repeaters.append(Node(2.00*d, 1.00*d, "rp"))
repeaters.append(Node(1.66*d, 1.00*d, "rp"))


repeaters.append(Node(4.00*d, 1.50*d, "rp")) #branch at j1
repeaters.append(Node(4.00*d, 2.00*d, "rp"))
repeaters.append(Node(4.00*d, 2.50*d, "rp"))

repeaters.append(Node(2.33*d, 1.50*d, "rp")) #branch at j2
repeaters.append(Node(2.33*d, 2.00*d, "rp"))
repeaters.append(Node(2.33*d, 2.33*d, "rp"))
repeaters.append(Node(2.33*d, 2.66*d, "rp"))
gw2 = Node(2.33*d, 3.00*d, "gw")


no_of_repeaters = len(repeaters)



g = Graph(len(nodes))

for n in nodes:
    n.learn_local_positions()
    # print(n.neighbor_rssi)

for i in range(len(nodes)):
    # print(nodes[i].neighbor_rssi)
    for j in range(len(nodes)):
        if(nodes[i].neighbor_rssi[j] != 0):
            g.graph[j][i] = calc_dist(nodes[i].neighbor_rssi[j])
            # graph_file.write(f"{j},{i},{int(g.graph[j][i])}\n")
            graph_file.write(f"{j} {i}\n")


print(g.graph)
plt.figure() 
plot_weighted_directed_graph(g.graph, node_labels=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18])

distFromGWs = []
for i in range(len(nodes)):
    if(nodes[i].type == "gw"):
        distFromGWs.append(g.dijkstra(i))

dist = [1e7 for x in range(len(nodes))]

for distset in distFromGWs:
    for i in range(len(dist)):
        if(distset[i]<dist[i]):
            dist[i] = distset[i]

print("\nNode \t Distance from nearest GW")
for i in range(len(dist)):
    print(i, "\t\t", dist[i])


nextNodeUp = []

for i in range(len(nodes)):
    nextNodeUp.append(i)
    nextNodeUpDist = dist[i]
    for j in range(len(nodes[i].neighbor_ids)):
        d = dist[nodes[i].neighbor_ids[j]]
        if(d < nextNodeUpDist):
            nextNodeUpDist = d
            nextNodeUp[i] = nodes[i].neighbor_ids[j]

print("\nNode \t Next RP/GW (Upstream) \t  Neighbours")
for i in range(len(nextNodeUp)):
    print(i, "\t\t", nextNodeUp[i], "\t\t", nodes[i].neighbor_ids)




# rssi = calc_rssi(nodes[0],nodes[1])
# print(rssi)
# print(calc_dist(rssi))
# rssi = calc_rssi(nodes[0],nodes[2])
# print(rssi)
# print(calc_dist(rssi))
# rssi = calc_rssi(nodes[0],nodes[3])
# print(rssi)
# print(calc_dist(rssi))





if (True):
    input('Press Enter to continue ...')