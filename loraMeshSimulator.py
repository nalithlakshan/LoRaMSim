import simpy
import random
import numpy as np
import math
import os
from inspect import currentframe
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg

# Simpy environment
env = simpy.Environment()

# Debug Mode
debug = 1
state_data_logging = False

# turn on/off graphics
graphics = 1
realtime_graphics = 0
fignum = 1
slideShowPause = 0.0 #number of seconds to pause OR 0 to wait until key press

# do the full collision check
full_collision = True

#carrier sensing
carrier_sensing_ed = True
carrier_sensing_rp = True 

#global awareness, routing, sleep algorithms
positional_algo = True
standby_repeater_algo = True
energy_aware_algo = True
repeater_sleep_algo = True

total_stanby = 0
standby_retains = 0
standby_recoveries = 0
repeater_role_changes = 0

# Averaege packet sending interval of end devices
avgSendTime = 600000 #in ms 
repeatDelayMultiplier = 5 #mean repeater waiting period = airtime * repeatDelayMultiplier 

experiment = 1

# These are arrays with measured values for sensitivity
#---------------SF---125-----250-----500----(BW in kHz)
sf7  = np.array([7, -126.50,-124.25,-120.75])
sf8  = np.array([8, -127.25,-126.75,-124.00])
sf9  = np.array([9, -131.25,-128.25,-127.50])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.50,-132.75,-128.75])
sf12 = np.array([12,-134.50,-132.25,-132.25])

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])
sf = 7
bw = 500
bw_index = {125: 1, 250: 2, 500: 3}
minsensi = sensi[sf-7][bw_index[bw]] #if SF, BW unknown, use -112.0dB for minsensi

#Path loss function parameters
Ptx = 14
gamma = 2.08
d0 = 40.0
var = 0  # variance ignored for now
Lpld0 = 127.41
GL = 0
Lpl = Ptx - minsensi
maxDist = d0*(10**((Lpl-Lpld0)/(10.0*gamma))) #CORRECTED MISTAKE HERE: REPLACED 'e' with 10
print ("amin", minsensi, "Lpl", Lpl)
print ("maxDist:", maxDist)
xmax = 0
ymax = 0

#Graphic related variables
timePlot = None
txInfoPlot = None
transmittingNodeIDs = []
colInfoPlot = None

# prepare graphics and add sink
if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()

# global value of packet sequence numbers
packetSeq = 0
totalSimPackets = 20
lastPacketGenTime = 0

# list of nodes
nodes = []
repeaterProcessingTime = 10
# maximum number of packets the node rx can receive at the same time
maxRxReceives = 8

# list of received packets (accounting reception at all the nodes)
collidedPackets=[]
lostPackets = []
#global packet seq numbers received at gateways
packetsRecBS = []
Q1_time = 0
Q2_time = 0
Q3_time = 0
predicted_DER = 1
packetLatencies = []

# WOR and CAD related
nodeClockAccuracy = 2.5 #ppm

# ----------------------------------------------------------------------------------
#COLLISION CHECK
# ----------------------------------------------------------------------------------
def checkcollision(packet, receiverNode):

    col = 0  #collision flag
    processing = 0

    for i in range(0,len(receiverNode.packetSourcesAtRx)):
        if receiverNode.packetSourcesAtRx[i].packet[receiverNode.id].processed == 1:
            processing = processing + 1
    if (processing >= maxRxReceives):
        print ("Too many packets at the receiver node. No of packets:", len(receiverNode.packetSourcesAtRx))
        packet.processed = 0
        return 1
    else:
        packet.processed = 1

    if(debug):
        print ("CHECK collision for packet-{} from node {} to node {} (sf:{} bw:{}kHz freq:{:.0f}MHz) No of other packets at rx: {}".format(
            packet.seqNr, packet.nodeid,receiverNode.id, packet.sf, packet.bw, packet.freq/10.0**6, len(receiverNode.packetSourcesAtRx)-1))

    #checking whether the receiving node has only one antenna, which is also in TX mode
    if(receiverNode.antennaType.lower() == "single" and receiverNode.tx_activity["active"]):
        packet.collided = 1
        packet.processed = 0
        col = 1
        if(debug and receiverNode.id!=packet.nodeid):
            print("   --collision since node",receiverNode.id,"is in transmitting state. Tx Acivity --> {", receiverNode.tx_activity["active"], receiverNode.tx_activity["start"], receiverNode.tx_activity["end"], receiverNode.tx_activity["preamble_duration"], receiverNode.tx_activity["tx_packet_type"],receiverNode.tx_activity["in_preamble"](env) ,"}")
        return col

    #checking packet collisions at receiving antenna
    elif receiverNode.packetSourcesAtRx:
        for other in receiverNode.packetSourcesAtRx:
            if other.id != packet.nodeid:
                if(debug): 
                    print (">> node {} (sf:{} bw:{}kHz freq:{:.0f}MHz)".format(
                        other.id, other.packet[receiverNode.id].sf, other.packet[receiverNode.id].bw, other.packet[receiverNode.id].freq/10.0**6))
                # simple collision
                if frequencyCollision(packet, other.packet[receiverNode.id]) \
                    and sfCollision(packet, other.packet[receiverNode.id]):
                    if full_collision:
                        if timingCollision(packet, other.packet[receiverNode.id]):
                            # check who collides in the power domain
                            c = powerCollision(packet, other.packet[receiverNode.id]) #returns a tuple of pwr collided packets
                            # 'c' may include either this packet, or the other packet, or both
                            for p in c:
                                p.collided = 1
                                if(p == packet):
                                    col = 1
                        else:
                            # no timing collision, all fine
                            pass
                    else:
                        packet.collided = 1
                        other.packet[receiverNode.id].collided = 1  # other packet also got collided, if it wasn't collided already
                        col = 1
        return col
    return 0


# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):  #240 not 120 ????????
        if(debug):
            print ("   --collision frequency at 500kHz bw")
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)): #120 not 60 ?????????
        if(debug):
            print ("   --collision frequency at 250kHz bw")
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):                                #60 not 30 (at CF=125kHz) ??????????
            if(debug):
                print ("   --collision frequency at 125kHz bw")
            return True
        #else:
    if(debug):
        print ("   --no frequency coll")
    return False


def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        if(debug):
            print ("   --collision sf node {} and node {}".format(p1.nodeid, p2.nodeid))
        # p2 may have been lost too, will be marked by other checks
        return True
    if(debug):
        print ("   --no sf collision")
    return False


def powerCollision(p1, p2):
    powerThreshold = 6 # or 6 dB considering worst cases
    if(debug):
        print ("   --pwr: node {0.nodeid} {0.rssi:3.2f} dBm node {1.nodeid} {1.rssi:3.2f} dBm; diff {2:3.2f} dBm".format(p1, p2, round(p1.rssi - p2.rssi,2)))
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        if(debug):
            print ("   --collision pwr both node {} and node {}".format(p1.nodeid, p2.nodeid))
        # packets are too close to each other, both collide
        # return both packets as casualties
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        # p2 overpowered p1, return p1 as casualty
        if(debug):
            print ("   --collision pwr node {} overpowered node {}".format(p2.nodeid, p1.nodeid))
        return (p1,)
    if(debug):
        print ("   --p1 wins, p2 lost")
    # p2 was the weaker packet, return it as a casualty
    return (p2,)


def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    if(debug):
        print ("   --collision timing node {} ({},{},{}) node {} ({},{})".format(
            p1.nodeid, env.now - env.now, p1_cs - env.now, p1.rectime,
            p2.nodeid, p2.addTime - env.now, p2_end - env.now
        ))
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        if(debug):
            print ("   --not late enough")
        return True
    if(debug):
        print ("   --saved by the preamble")
    return False


# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf,cr,pl,bw, premlen=8):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    if(premlen == -1): #A preamble equal to CAD Periodicity
        Tpream = 1000 #ms
    else: 
        Tpream = (premlen + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream, Tpayload


#FUNCTIONS FOR POSITION LEARNING ALGORITHM
def estimate_dist_from_rssi(rssi):
    global Ptx
    global gamma
    global d0
    global Lpld0
    global GL
    Lpl = Ptx -GL -rssi
    d = pow(10,(Lpl -Lpld0)/(10*gamma))*d0
    return d


def run_position_learning():
    global nodes
    mainNodes = []
    for i in range(len(nodes)):
        if(nodes[i].type == "rp" or nodes[i].type == "gw"):
            mainNodes.append(nodes[i])

    g = Graph(len(mainNodes))

    for i in range(len(mainNodes)):
        # print(nodes[i].neighbor_rssi)
        for j in range(len(mainNodes)):
            if(mainNodes[i].neighbor_rssi[j] != 0):
                g.graph[j][i] = estimate_dist_from_rssi(mainNodes[i].neighbor_rssi[j])

    print(g.graph)

    distFromGWs = []
    idsOfGWs = []
    for i in range(len(mainNodes)):
        if(mainNodes[i].type == "gw"):
            distFromGWs.append(g.dijkstra(i))
            idsOfGWs.append(i)

    dist = [1e7 for x in range(len(mainNodes))]
    nearestGW = [0 for x in range(len(mainNodes))]
    k=0
    for distset in distFromGWs:
        gwId = idsOfGWs[k]
        for i in range(len(dist)):
            if(distset[i]<dist[i]):
                dist[i] = distset[i]
                nearestGW[i] = gwId
        k += 1

    # print("\nNode \t Distance from nearest GW")
    # for i in range(len(dist)):
    #     print(i, "\t\t", dist[i])

    nextNodeUp = []

    for i in range(len(mainNodes)):
        nextNodeUp.append(i)
        nextNodeUpDist = dist[i]
        for j in range(len(mainNodes[i].neighbor_ids)):
            d = dist[mainNodes[i].neighbor_ids[j]]
            if(d < nextNodeUpDist):
                nextNodeUpDist = d
                nextNodeUp[i] = mainNodes[i].neighbor_ids[j]

    m = 0
    for i in range(len(nodes)):
        if(nodes[i].type == "rp" or nodes[i].type == "gw"):
            nodes[i].nextRp = nextNodeUp[m]
            nodes[i].nextRpOriginal = nextNodeUp[m]
            nodes[i].distanceValue = dist[m]
            nodes[i].nearestGwId = nearestGW[m]
            m = m + 1

    # print("\nNode \t Next RP/GW (Upstream) \t  Neighbours")
    # for i in range(len(nextNodeUp)):
    #     print(i, "\t\t", nextNodeUp[i], "\t\t", mainNodes[i].neighbor_ids)



#debugging function to get current line number
def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno


#
# This is called to configure the network after creating all nodes
#
def networkConfig():
    global nodes
    for i in range(len(nodes)):
        nodes[i].createPackets()
        # if(realtime_graphics == 1 and graphics == 1):
        nodes[i].txArrowPlots = [None] * len(nodes)

    run_position_learning()
    
    #Graphic Config
    if(graphics):
        global xmax
        global ymax
        for i in range(len(nodes)):
            if(nodes[i].x > xmax):
                xmax = nodes[i].x
            if(nodes[i].y > ymax):
                ymax = nodes[i].y
        xmax = xmax*1.1
        ymax = ymax*1.1
        
        ax.add_patch(Rectangle((0, 0), xmax, ymax, fill=None, alpha=1))
        current_script_path = os.path.abspath(__file__)
        current_script_directory = os.path.dirname(current_script_path)
        legendImg = mpimg.imread(current_script_directory+"/simulatorLegend.png")
        ax.imshow(legendImg, extent=(xmax*0.03, xmax*0.19, ymax*0.08, ymax*0.32), aspect='auto')


# ----------------------------------------------------------------------------------
# Python classes
# ----------------------------------------------------------------------------------

#
# this class creates a node
#
class node():
    def __init__(self, env, x, y, type):
        global nodes
        nodes.append(self)
        self.id = len(nodes)-1
        self.x = x
        self.y = y
        self.type = type #3 TYPES: end device(ed), repeater(rp), gateway(gw)
        self.mode = "RX" #Can be "SLEEP", "CAD", "RX", "TX"
        self.lastStateChangeTime = 0

        #position and routing info
        self.distanceValue = -1
        self.nextRp = -1
        self.nextRpOriginal = -1
        self.neighbor_ids = []
        self.neighbor_rssi = []

        #Tx antenna state
        self.tx_activity = {
            "active": False,
            "start": None,
            "end": None,
            "preamble_duration": None,
            "tx_packet_type": "OTHER",  # Can be "WOR_up", "WOR_down", "DATA_up", "DATA_down", "OTHER"
            "in_preamble": lambda env: self.tx_activity["start"] is not None and self.tx_activity["start"] <= env.now < self.tx_activity["start"] + self.tx_activity["preamble_duration"]
        }

        #Power Consumption
        self.batteryCapacity  = 100 #mAh
        self.batteryRemaining = 100 #mAh
        self.batteryPercentage = 100
        self.batteryDischargeRate = 1 #mA
        self.batteryLastRecordedTime = 0
        # self.currentRx = 81.6 #mA
        # self.currentTx = 512 #mA
        self.currentRx = 50 #mA
        self.currentTx = 5000 #mA
        self.currentCad = 1 #mA
        self.cadPeriodity = 1000 #in ms

        # properties common for all types
        self.antennaType = "single"  #single/dual
        self.packetSourcesAtRx = []
        self.recPackets = []
        self.txPackets = []
        self.packet = []
        self.dist = []
        self.txArrowPlots = []

        #properties specific to end-devices
        self.sent = 0
        self.sentSuccessful = 0
        self.period = avgSendTime

        #properties specific to repeaters
        self.packetsFifo = simpy.Store(env)
        self.nTransmitters = simpy.Resource(env, capacity=1)
        self.tx_activity["active"] = False
        self.standbyBufferCount = 0
        self.lowerDistanceRecBuffer = []
        self.txTimePercentage = 0
        self.nearestGwId = -1

        # WOR and CAD related
        self.lastCadScanTime = 0
        global nodeClockAccuracy
        self.clockAccuracy = random.uniform(-nodeClockAccuracy,nodeClockAccuracy)/1000000
        self.worAckReceived = -1    # -1 means not expecting ack, 0 means expecting ack, 1 means ack received
        self.awaitingToSendWorAck = 0 #by Rp to ED
        self.toWhichEdAmIAwaitingToSendAck = [] #list of ED IDs

        #data dump files
        tx_status_file_name = 'tx status data\dump_node_'+ str(self.id)+'.txt'       
        self.tx_status_file = open(tx_status_file_name, 'w')
        # self.tx_status_file.write("initiated file for node"+str(self.id))
        
        battery_status_file_name = 'battery status data\dump_node_'+ str(self.id)+'.csv'       
        self.battery_status_file = open(battery_status_file_name, 'w')
        # self.battery_status_file.write("initiated file for node"+str(self.id)+"\n")
        self.battery_status_file.write(f"{self.id},{env.now},{self.batteryRemaining},{round(self.batteryPercentage,2)}\n")

        # State diagram data file
        if(state_data_logging):
            state_diagram_file_name = 'state diagram data/dump_node_'+ str(self.id)+'.txt'       
            self.state_diagram_file = open(state_diagram_file_name, 'w')
            self.state_diagram_file.write(f"{env.now} {self.mode}\n")

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            if  (self.type.lower() == "ed"):
                self.icon = ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))
                self.label = ax.add_artist(plt.text(self.x+6,self.y,self.id, color='#888888'))
            elif(self.type.lower() == "rp"):
                self.icon = ax.add_artist(plt.Circle((self.x, self.y), 4, fill=True, color='green'))
                self.label = ax.add_artist(plt.text(self.x+6,self.y,self.id))
            elif(self.type.lower() == "gw"):
                self.icon = ax.add_artist(plt.Circle((self.x, self.y), 4, fill=True, color='red'))
                self.label = ax.add_artist(plt.text(self.x+6,self.y,self.id))
            else:
                print("Incorrect device type!")

    def setIconColorByMode(self, env, lineNo = 0):
        global graphics
        global state_data_logging

        if(state_data_logging):
            # Record state change in state diagram file
            if self.mode == "TX":
                # For TX mode, write both preamble and frame timing
                self.state_diagram_file.write(f"{env.now} TX_preamble\n")
                self.state_diagram_file.write(f"{env.now + self.tx_activity['preamble_duration']} TX_frame\n")
            else:
                # For all other modes, write single state
                self.state_diagram_file.write(f"{env.now} {self.mode}\n")
            self.state_diagram_file.flush()  # Ensure writing to disk immediately
        
        if (graphics == 1):
            if (self.mode == "CAD" or self.mode == "SLEEP"):
                if self.type.lower() == "ed":
                    color = 'lightblue'
                elif self.type.lower() == "rp":
                    color = 'lightgreen'
                elif self.type.lower() == "gw":
                    color = 'pink'
            else:
                if self.type.lower() == "ed":
                    color = 'blue'
                elif self.type.lower() == "rp":
                    color = 'green'
                elif self.type.lower() == "gw":
                    color = 'red'
            if(color != self.icon.get_facecolor()):
                if(debug):
                    print(f"Node {self.id} changing color to {color} at line {lineNo}")
            self.lastStateChangeTime = env.now
            self.icon.set_color(color)


    def batteryUpdate(self, env, dischargeRate):
        T = (env.now - self.batteryLastRecordedTime)/3600000
        self.batteryRemaining = self.batteryRemaining - T*self.batteryDischargeRate
        self.batteryPercentage = 100*self.batteryRemaining/self.batteryCapacity
        self.battery_status_file.write(f"{self.id},{env.now},{self.batteryRemaining},{round(self.batteryPercentage,2)}\n")
        self.batteryLastRecordedTime = env.now
        self.batteryDischargeRate = dischargeRate
        

    def calc_rssi(self, otherNodeID):
        global Ptx
        global gamma
        global d0
        global Lpld0
        global GL
        d = self.dist[otherNodeID]
        if(d != 0):
            Lpl = Lpld0 + 10*gamma*math.log10(d/d0)
        else:
            Lpl = 0
        rssi = Ptx - GL - Lpl
        return rssi + random.uniform(-1, 1) #random noise added


    def createPackets(self, packetType = "OTHER", premlen=8, intendedRxId=-1, nodeAcknowledged=-1, seqNr=None, addTime=None):
        global experiment
        global Ptx
        global minsensi
        global maxDist

        self.neighbor_rssi = [0 for x in range(len(nodes))]

        # determining distances to RX nodes
        for i in range(0,len(nodes)):
            # d = np.sqrt((self.x-nodes[i].x)*(self.x-nodes[i].x)+(self.x-nodes[i].x)*(self.y-nodes[i].y))
            d = abs(self.x-nodes[i].x) + abs((self.y-nodes[i].y))
            self.dist.append(d)

            if(d<= maxDist and self.type != "ed" and nodes[i].type != "ed" and i != self.id):
                self.neighbor_rssi[i] = self.calc_rssi(i)
                self.neighbor_ids.append(i)

        # if(debug):
        #     print(self.type.upper(),":",self.id, "x", self.x, "y", self.y, "dist: ", self.dist)


        #cr =1,2,3,or 4
        #cr = 1 corresponds to coding rate 4/5 and cr=4 corresponds to coding rate 4/8
        # 4/8 coding rate means that for every 4 bits of useful information the coder generates 8bits of data including error correction bits
        # determining tx LoRa params  
        if(experiment == 1):     
            sf = 7
            bw = 500
            cr = 2
            freq = 915900000 # Data channel for repeaters
            if (self.type.lower() == "ed"):
                freq = 917500000 #Data channel for end devices
            if ((packetType == "WOR_up" or packetType == "WOR_down")and self.type.lower() == "ed"):
                freq = 916200000 #WOR channel
            if ((packetType == "WOR_up" or packetType == "WOR_down")and self.type.lower() != "ed"):
                freq = 916500000 #WOR channel            

        # Here more experiments with different parameters can be added
        # ...
   
        # create virtual packets for each other node
        self.packet = []
        if(packetType == "WOR_up" or packetType == "WOR_down"):
            for i in range(0,len(nodes)):
                if(self.type.upper() == "ED"):
                    self.packet.append(myPacket(self.id, 15, self.dist[i], i, Ptx/2, sf, cr, bw, freq, packetType, premlen, intendedRxId, nodeAcknowledged, seqNr, addTime))
                else:
                    self.packet.append(myPacket(self.id, 15, self.dist[i], i, Ptx, sf, cr, bw, freq, packetType, premlen, intendedRxId, nodeAcknowledged, seqNr, addTime))
        else:
            for i in range(0,len(nodes)):
                if(self.type.upper() == "ED"):
                    self.packet.append(myPacket(self.id, 20, self.dist[i], i, Ptx/2, sf, cr, bw, freq, packetType, premlen, intendedRxId, nodeAcknowledged, seqNr, addTime))
                else:
                    self.packet.append(myPacket(self.id, 20, self.dist[i], i, Ptx, sf, cr, bw, freq, packetType, premlen, intendedRxId, nodeAcknowledged, seqNr, addTime))


    def drawTxArrows(self):
        for i in range(len(self.packet)):
            pk = self.packet[i]
            if(pk.lost == False):
                x = nodes[pk.nodeid].x
                y = nodes[pk.nodeid].y
                dx = nodes[pk.rxNodeId].x -x
                dy = nodes[pk.rxNodeId].y -y
                if(pk.packetType == "WOR_up" or pk.packetType == "WOR_down"):
                        self.txArrowPlots[i] = plt.arrow(x,y,dx,dy, width=1, color="lightblue", head_width=5, length_includes_head=True)
                elif(nodes[pk.rxNodeId].type.upper() == "ED"):
                    self.txArrowPlots[i] = plt.arrow(x,y,dx,dy, width=1, color="gray", head_width=5, length_includes_head=True)
                else:
                    self.txArrowPlots[i] = plt.arrow(x,y,dx,dy, width=1, color="black", head_width=5, length_includes_head=True, linewidth=2)


    def eraseTxArrows(self):
        for i in range(len(self.txArrowPlots)):
            if(self.txArrowPlots[i] != None):
                self.txArrowPlots[i].remove()
                self.txArrowPlots[i] = None


    def markCollidedArrows(self):
        for i in range(len(self.packet)):
            if(self.packet[i].lost == False):
                for node in nodes[i].packetSourcesAtRx:
                    if(node.packet[i].collided == True):
                        node.txArrowPlots[i].set_color("red")


    def drawTime(self, env):
        T = int(env.now)
        seconds = T // 1000
        minutes = seconds // 60
        hours = minutes // 60
        seconds %= 60
        minutes %= 60
        hours %= 24
        timeString = f"T= {hours:02d}:{minutes:02d}:{seconds:02d}"
        global timePlot
        global xmax
        global ymax
        if(timePlot != None):
            timePlot.remove()
        timePlot = plt.text(xmax*0.03, ymax*0.95, timeString, fontsize='large', verticalalignment='top')


    def drawTransmittingInfo(self):
        global txInfoPlot
        global transmittingNodeIDs
        global nodes
        global xmax
        global ymax
        if(self.id not in transmittingNodeIDs and self.tx_activity["active"]):
            transmittingNodeIDs.append(self.id)
        transmittingNodeIDsTemp = transmittingNodeIDs.copy()
        txInfoString = ""
        for i in range(len(transmittingNodeIDsTemp)):
            if(nodes[transmittingNodeIDsTemp[i]].tx_activity["active"]):
                x,y,t,pktType = nodes[transmittingNodeIDsTemp[i]].packet[0].seqNr.split('|')
                txInfoString += f"Node {transmittingNodeIDsTemp[i]} sending pkt {x}|{y}|{pktType}\n"
            else:
                transmittingNodeIDs.remove(transmittingNodeIDsTemp[i])
        if(txInfoPlot != None):
            txInfoPlot.remove()
        txInfoPlot = plt.text(xmax*0.33, ymax*0.95, txInfoString, fontsize='large', verticalalignment='top')


    def drawCollisionInfo(self):
        global colInfoPlot
        # global colPktObjects
        global transmittingNodeIDs
        global nodes
        global xmax
        global ymax
        if(self.id not in transmittingNodeIDs and self.tx_activity["active"]):
            transmittingNodeIDs.append(self.id)
        
        colPktObjects = []
        for i in range(len(transmittingNodeIDs)):
            if(nodes[transmittingNodeIDs[i]].tx_activity["active"]):
                for j in range(len(nodes)):
                    pk = nodes[transmittingNodeIDs[i]].packet[j]
                    if(pk.lost == False and pk.collided == True):
                        if(pk not in colPktObjects):
                            colPktObjects.append(pk)
                    else:
                        if(pk in colPktObjects):
                            colPktObjects.remove(pk)

        colInfoString = ""
        for pk in colPktObjects:
            if(pk.nodeid != pk.rxNodeId):
                colInfoString += f"Node {pk.nodeid} to Node {pk.rxNodeId} transmission collided\n"

        if(colInfoPlot != None):
            colInfoPlot.remove()
        colInfoPlot = plt.text(xmax*0.66, ymax*0.95, colInfoString, fontsize='large', verticalalignment='top')
    

    def endDeviceStateMachine(self, env):
        global packetSeq
        global lastPacketGenTime
        global totalSimPackets
        global nodes

        while(True):
            self.mode = "CAD"
            self.batteryUpdate(env, self.currentCad)
            self.setIconColorByMode(env, get_linenumber())
            yield env.timeout(random.expovariate(1.0/float(self.period)))

            packetSeq = packetSeq + 1

            if (packetSeq > totalSimPackets):
                lastPacketGenTime = env.now
                break

            self.mode = "RX"
            self.batteryUpdate(env, self.currentRx)
            self.setIconColorByMode(env, get_linenumber())

            #carrier sensing
            if(carrier_sensing_ed ==1): 
                while(len(self.packetSourcesAtRx) != 0):
                    yield env.timeout(1)
                    # if(debug):
                    #     print("ED: waiting till medium is idle")

            # $$$$$$$$$$$$$$$$$
            # if(packetSeq == 95):
            #     global realtime_graphics
            #     global debug
            #     realtime_graphics = 1
            #     debug = 1
            
            if(repeater_sleep_algo):
                if(self.worAckReceived == -1):
                    #first send WORed then data packet
                    self.nextRp = -1 #broadcast WOR
                    seqNr = f"{self.id}|{packetSeq}|{round(env.now, 1)}|WOR_up"
                    addTime = round(env.now, 1)
                    self.tx_activity["active"] = True
                    self.createPackets(packetType="WOR_up", premlen=-1, seqNr=seqNr, addTime=addTime)
                    self.tx_activity["start"] = env.now
                    self.tx_activity["end"] = env.now + self.packet[0].rectime
                    self.tx_activity["preamble_duration"] = self.packet[0].Tprem
                    self.tx_activity["tx_packet_type"] = "WOR_up"
                    self.worAckReceived = 0
                    self.tx_status_file.write(str(env.now))
                    yield env.process(self.transmit(env))

                    self.mode = "RX"
                    self.batteryUpdate(env, self.currentRx)
                    self.setIconColorByMode(env, get_linenumber())
                    k = 0
                    while (self.worAckReceived == 0):
                        yield env.timeout(1) #waiting for WOR ACK
                        k = k + 1
                        if(k > 20000):
                            self.worAckReceived = 1
                            print("ED:",self.id,"WOR ACK wait timeout")
                            break

                    if(self.worAckReceived == 1):
                        #carrier sensing
                        if(carrier_sensing_ed ==1): 
                            while(len(self.packetSourcesAtRx) != 0):
                                yield env.timeout(1)
                                # if(debug):
                                #     print("ED: waiting till medium is idle")

                        self.worAckReceived = -1
                        seqNr = f"{self.id}|{packetSeq}|{round(env.now, 1)}|DATA_up"
                        addTime = round(env.now, 1)
                        self.tx_activity["active"] = True
                        self.createPackets(packetType="DATA_up", intendedRxId=self.nextRp, seqNr=seqNr, addTime=addTime)
                        self.tx_activity["start"] = env.now
                        self.tx_activity["end"] = env.now + self.packet[0].rectime
                        self.tx_activity["preamble_duration"] = self.packet[0].Tprem
                        self.tx_activity["tx_packet_type"] = "DATA_up"
                        self.sent = self.sent + 1
                        self.tx_status_file.write(" "+str(env.now))
                        yield env.process(self.transmit(env))

            else:
                seqNr = f"{self.id}|{packetSeq}|{round(env.now, 1)}|DATA_up"
                addTime = round(env.now, 1)
                self.tx_activity["active"] = True
                self.createPackets(packetType="DATA_up", seqNr=seqNr, addTime=addTime)
                self.tx_activity["start"] = env.now
                self.tx_activity["end"] = env.now + self.packet[0].rectime
                self.tx_activity["preamble_duration"] = self.packet[0].Tprem
                self.tx_activity["tx_packet_type"] = "DATA_up"
                self.sent = self.sent + 1
                self.tx_status_file.write(str(env.now))
                # for i in range(0, len(nodes)):
                #     self.packet[i].addTime = round(env.now, 1)
                #     self.packet[i].seqNr = f"{self.id}|{packetSeq}|{self.packet[i].addTime}|{self.tx_activity['tx_packet_type']}"
                yield env.process(self.transmit(env))


    #only for the transmission by end-devices
    def transmit(self, env, seqNr=None):
        global packetSeq
        global lastPacketGenTime
        global totalSimPackets
        global nodes
        global lostPackets
        global collidedPackets
        global fignum
        self.mode = "TX"
        self.batteryUpdate(env, self.currentTx)
        self.setIconColorByMode(env, get_linenumber())

        if(debug):
            # print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Transmitted Packet:{self.id}|{packetSeq}|{self.tx_activity['tx_packet_type']}")
            print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Transmitted Packet:{self.packet[0].seqNr}")

        for i in range(0, len(nodes)):
            self.packet[i].addTime = round(env.now, 1)
            if(seqNr != None):
                self.packet[i].seqNr = seqNr            
            if(self.packet[i].lost == 0): #checking if the packet reachs at node[i]
                if (self in nodes[i].packetSourcesAtRx):
                    print("ERROR: packet",self.packet[i].seqNr, "from node",self.id,"is already in node",i,"RX")
                else:
                    nodes[i].packetSourcesAtRx.append(self)
                    # checking collision at the start of packet reception
                    if (checkcollision(self.packet[i], nodes[i])==1):
                        self.packet[i].collided = 1
                    else:
                        self.packet[i].collided = 0
        
        self.txPackets.append(self.packet[0].seqNr)

        if(realtime_graphics  and graphics):
            self.drawTxArrows()
            self.drawTime(env)
            self.drawTransmittingInfo()
            self.markCollidedArrows()
            self.drawCollisionInfo()
            if(slideShowPause):
                plt.pause(slideShowPause)
            else:
                plt.waitforbuttonpress()
            ext = ".png"
            figname = str(fignum) + ext
            save_path = os.path.join("plots", figname)
            fignum +=1
            plt.savefig(save_path)
        
        # air time (take first packet rectime)
        yield env.timeout(self.packet[0].rectime)
        self.tx_activity["active"] = False
        self.tx_status_file.write(" "+str(env.now)+"\n")
        self.mode = "RX"
        self.batteryUpdate(env, self.currentRx)
        self.setIconColorByMode(env, get_linenumber())

        if(realtime_graphics  and graphics):
            self.eraseTxArrows()

        # if packet did not collide, add it in list of received packets
        # unless it is already in
        nodesThatReceivedPkt = []
        for i in range(0, len(nodes)):
            if(i != self.id):
                if self.packet[i].lost:
                    lostPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
                else:
                    if ((self.packet[i].collided == 0) and (self.packet[i].processed == 1)):
                        if (nodes[i].mode == "RX"):
                            if(debug):
                                print(f"called nodes[{i}].receive() from node {self.id}")
                            env.process(nodes[i].receive(env, self.packet[i], self.packet[i].seqNr, self.distanceValue, self.nextRp, self.id))
                            nodesThatReceivedPkt.append(i)
                        else:
                            if(debug):
                                print(f"nodes[{i}] is in {nodes[i].mode} mode, cannot receive packet from node {self.id}")
                    else:
                        # XXX only for debugging
                        collidedPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
        
        # if(debug):
        #     print("|____Nodes that received the packet:",nodesThatReceivedPkt)

        # complete packet has been received by base station
        # can remove it
        for i in range(0, len(nodes)):
            if (self in nodes[i].packetSourcesAtRx):
                nodes[i].packetSourcesAtRx.remove(self)
            # reset the packet
            self.packet[i].collided = 0
            self.packet[i].processed = 0



    def receive(self, env, packet, seqNr, prevDistanceValue, nextRp, prevRp):
        global nodes
        # yield env.timeout(repeaterProcessingTime) #wait for the processing time

        if (self.distanceValue >= prevDistanceValue and (packet.packetType == "DATA_up" or packet.packetType == "WOR_up")):
            self.lowerDistanceRecBuffer.append([seqNr, nodes[prevRp].batteryPercentage, prevRp])
            if(self.type.lower() == "rp" and packet.packetType == "WOR_up" and nodes[prevRp].type.lower() != "ed" and self.nearestGwId==nodes[prevRp].nearestGwId and self.worAckReceived==0):
                self.worAckReceived = 1

        if(self.type.lower() == "rp" and packet.packetType == "WOR_up" and nodes[packet.nodeid].type.lower() != "ed"):
            if(nodes[packet.nodeAcknowledged].type.lower() == "ed" and self.awaitingToSendWorAck ==1 and (packet.nodeAcknowledged in self.toWhichEdAmIAwaitingToSendAck)):
                if(debug):
                    print("Rp:",self.id,"backing off without sending a WOR-ACK to ED:",packet.nodeAcknowledged)
                self.toWhichEdAmIAwaitingToSendAck.remove(packet.nodeAcknowledged)
                if len(self.toWhichEdAmIAwaitingToSendAck) == 0:
                    self.awaitingToSendWorAck = 0

        if (seqNr not in self.recPackets):
            self.recPackets.append(seqNr) 
        else:
            return 0 #already processed
        
        if(debug):
            print(f"Node {self.id}({self.type.upper()}) Processing Packet:{seqNr}")

        #check if it is a gateway
        if (self.type.lower() == "gw"):

            if(repeater_sleep_algo):

                if(packet.packetType == "WOR_up" and (packet.intendedRxNodeId == self.id or packet.intendedRxNodeId == -1)):
                    self.packetsFifo.put(packet)
                    with self.nTransmitters.request() as req:
                        yield req
                        outputPacket = yield self.packetsFifo.get()

                        if(carrier_sensing_rp ==1):
                            while(True):
                                if(len(self.packetSourcesAtRx) == 0): 
                                    break
                                yield env.timeout(random.expovariate(1.0/float(outputPacket.rectime*repeatDelayMultiplier)))
                        
                        if(outputPacket.packetType == "WOR_up"):
                            self.tx_activity["active"] = True
                            self.createPackets("WOR_up", -1, nodeAcknowledged=outputPacket.nodeid, seqNr=outputPacket.seqNr)
                            self.tx_activity["start"] = env.now
                            self.tx_activity["end"] = env.now + self.packet[0].rectime
                            self.tx_activity["preamble_duration"] = self.packet[0].Tprem
                            self.tx_activity["tx_packet_type"] = "WOR_up"
                            self.tx_status_file.write(str(env.now))
                            yield env.process(self.transmit(env))

                elif(packet.packetType == "DATA_up"):
                    #Do no more transmissions. Account the packets received.
                    if(debug):
                        print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
                        # print("T =",env.now, "|GW",self.id, "Received Packet:",seqNr,"\n")
                    if seqNr not in packetsRecBS:
                        packetsRecBS.append(seqNr)
                        x,y,t,pktType =seqNr.split("|")
                        latency = env.now -float(t)
                        # print("Latency:",latency)
                        packetLatencies.append(latency)          
            
            else:
                #Do no more transmissions. Account the packets received.
                if(debug):
                    print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
                    # print("T =",env.now, "|GW",self.id, "Received Packet:",seqNr,"\n")
                if seqNr not in packetsRecBS:
                    packetsRecBS.append(seqNr)
                    x,y,t,pktType =seqNr.split("|")
                    latency = env.now -float(t)
                    # print("Latency:",latency)
                    packetLatencies.append(latency)
            
            #overall receiving rate calculation when 50% of the packets are received 
            global totalSimPackets
            global Q1_time
            global Q2_time
            global Q3_time
            global predicted_DER
            if(len(packetsRecBS) == int(totalSimPackets*predicted_DER*1/4)):
                Q1_time = env.now
            if(len(packetsRecBS) == int(totalSimPackets*predicted_DER*2/4)):
                Q2_time = env.now  
            if(len(packetsRecBS) == int(totalSimPackets*predicted_DER*3/4)):
                Q3_time = env.now
            


        #check if it is an end-device
        elif (self.type.lower() == "ed"):
            if(repeater_sleep_algo):
                if(packet.packetType == "WOR_up" and self.worAckReceived == 0 and nodes[packet.nodeid].type.lower() != "ed"):
                    self.worAckReceived = 1
                    self.nextRp = packet.nodeid
                    if(debug):
                        print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received WOR ACK:{seqNr} | Next RP set to {self.nextRp}")
                elif(packet.packetType == "DATA_up" or packet.packetType == "DATA_down"):
                    if(debug):
                        print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
            
            else:
                if(debug):
                    print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
        
        #if it is a repeater
        else:
            if(repeater_sleep_algo):
                if(debug):
                    print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr} from Node {prevRp}({nodes[prevRp].type.upper()})")

                if(packet.packetType == "WOR_up" and nodes[prevRp].type.lower() == "ed"):
                    self.awaitingToSendWorAck = 1
                    self.toWhichEdAmIAwaitingToSendAck.append(prevRp)
                    self.worAckReceived = 0
                    yield env.timeout(random.uniform(packet.rectime*0.0, packet.rectime*4.0))
                    # yield env.timeout(random.expovariate(1.0/float(packet.rectime*repeatDelayMultiplier)))
                    if(carrier_sensing_rp ==1):
                        while(len(self.packetSourcesAtRx) != 0):
                            yield env.timeout(random.uniform(1,10))

                    if(self.awaitingToSendWorAck == 1):
                        
                        packetInfo = [seqNr, prevRp]
                        self.packetsFifo.put(packetInfo)
                        with self.nTransmitters.request() as req:
                            yield req
                            packetInfoOut = yield self.packetsFifo.get()
                            edId,packetSeq,genTime,pktType =packetInfoOut[0].split("|")

                            if(carrier_sensing_rp ==1):
                                while(len(self.packetSourcesAtRx) != 0):
                                    yield env.timeout(random.uniform(1,10))

                            if((self.worAckReceived == 1 or self.awaitingToSendWorAck == 0) and pktType=="WOR_up"):
                                if(debug):
                                    print(f"Node {self.id} not sending WOR ACK to ED {edId} as it already received ACK or is not expecting any ACK")
                                return 0
                            self.tx_activity["active"] = True
                            self.createPackets(pktType, -1, self.nextRp, packetInfoOut[1], packetInfoOut[0], round(env.now, 1))
                            self.tx_activity["start"] = env.now
                            self.tx_activity["end"] = env.now + self.packet[0].rectime
                            self.tx_activity["preamble_duration"] = self.packet[0].Tprem
                            self.tx_activity["tx_packet_type"] = pktType
                            self.tx_status_file.write(str(env.now))
                            yield env.process(self.transmit(env))
                            self.awaitingToSendWorAck = 0
                            self.toWhichEdAmIAwaitingToSendAck = []
                    
                else:
                    if(positional_algo):
                        standby = 0

                        if(nodes[prevRp].type.lower()!="ed" and self.nearestGwId!=nodes[prevRp].nearestGwId):
                            if(self.worAckReceived!=0 and self.awaitingToSendWorAck==0 and len(self.packetsFifo.items)==0 and self.standbyBufferCount==0):
                                self.mode = "CAD"
                                self.batteryUpdate(env, self.currentCad)
                                self.setIconColorByMode(env, get_linenumber())
                                self.worAckReceived = -1
                            return 0

                        if(packet.packetType == "WOR_up" or packet.packetType == "DATA_up"):
                            if(self.distanceValue < prevDistanceValue or prevDistanceValue == -1):
                                
                                packetInfo = [seqNr, prevRp]
                                
                                if(packet.packetType == "WOR_up" and self.nearestGwId==nodes[prevRp].nearestGwId):
                                    self.worAckReceived = 0

                                if(standby_repeater_algo):          
                                    if(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="rp" and self.distanceValue>nodes[nextRp].distanceValue):
                                        
                                        if(packet.packetType=="DATA_up" and self.worAckReceived==0):
                                            k = 0
                                            while(True):
                                                yield env.timeout(10)
                                                k +=1
                                                if(self.worAckReceived==1 or k==1000):
                                                    if(debug and k==1000):
                                                        print(f"Node {self.id}({self.type.upper()}) didn't receive a WOR-ACK for Pkt:{seqNr}")
                                                    break
                                        elif(packet.packetType=="DATA_up" and self.worAckReceived==-1):
                                            if(debug):
                                                print(f"Node {self.id}({self.type.upper()}) isn't expecting any Pkt but got:{seqNr}")
                                            return 0
                                        
                                        if(packet.packetType=="DATA_up"):
                                            standByTime = float(packet.rectime*repeatDelayMultiplier +5000)
                                        elif(packet.packetType=="WOR_up"):
                                            standByTime = float(packet.rectime*repeatDelayMultiplier)

                                        standby = 1
                                        self.standbyBufferCount += 1
                                        # standByTime = float(packet.rectime +packet.rectime*repeatDelayMultiplier*5+5000) 
                                        standby = yield env.process(self.standbyMode(env, packetInfo, standByTime, prevRp))
                                        self.standbyBufferCount -= 1
                                        if(standby == 1):
                                            if(debug):
                                                print(f"Standby Recovery by Node {self.id} at T={round(env.now,2)} (Standby Time={round(standByTime,2)})")
                                            self.packetsFifo.put(packetInfo)
                                            with self.nTransmitters.request() as req:
                                                yield req
                                                packetInfoOut = yield self.packetsFifo.get()
                                                if(packet.packetType == "WOR_up" or packet.packetType == "WOR_down"):
                                                    yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[1]))
                                                else:
                                                    yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
                                        else:
                                            #Whether goes back to RX mode or CAD
                                            if((packet.packetType == "DATA_up" or packet.packetType == "DATA_down") and (len(self.packetsFifo.items) == 0) and self.awaitingToSendWorAck==0 and self.standbyBufferCount==0):
                                                if(debug):
                                                    print(f"-*-*-*-Node {self.id} standby period ends with Sb={standby} Pkt-type={packet.packetType} (seqNr:{seqNr})") 
                                                self.mode = "CAD"
                                                self.batteryUpdate(env, self.currentCad)
                                                self.setIconColorByMode(env, get_linenumber())
                                                self.worAckReceived = -1

                                    elif(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="gw" and packet.packetType=="DATA_up" and (len(self.packetsFifo.items) == 0) and self.awaitingToSendWorAck==0 and self.standbyBufferCount==0):
                                        self.mode = "CAD"
                                        self.batteryUpdate(env, self.currentCad)
                                        self.setIconColorByMode(env, get_linenumber())
                                        self.worAckReceived = -1
                                        # print(f"-*-*-*-Node {self.id} going to CAD mode as nextRp is GW (seqNr:{seqNr})")

                                    elif(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="rp" and nodes[prevRp].distanceValue>nodes[nextRp].distanceValue>self.distanceValue):
                                        if(energy_aware_algo):
                                            if(round(nodes[nextRp].batteryPercentage%10) == 0):
                                                if(nodes[nextRp].batteryPercentage<(self.batteryPercentage)):
                                                    nodes[prevRp].nextRp = self.id
                                                    if(debug):
                                                        print("Energy Aware Algo changed node ",prevRp,"'s nextRp to ", self.id)
                                    
                                    elif(self.id == nextRp or nextRp == -1):
                                        # print("received by the one addressed!")
                                        if(packet.packetType=="DATA_up" and self.worAckReceived==0):
                                            k = 0
                                            while(True):
                                                yield env.timeout(10)
                                                k +=1
                                                if(self.worAckReceived==1 or k==1000):
                                                    break

                                        elif(packet.packetType=="DATA_up" and self.worAckReceived==-1):
                                            return 0
                                        
                                        # elif(packet.packetType=="WOR_up" and self.worAckReceived==1):
                                        #     return 0

                                        self.packetsFifo.put(packetInfo)
                                        with self.nTransmitters.request() as req:
                                            yield req
                                            packetInfoOut = yield self.packetsFifo.get()
                                            if(packet.packetType == "WOR_up" or packet.packetType == "WOR_down"):
                                                yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[1]))
                                            else:
                                                yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
                                else:
                                    self.packetsFifo.put(packetInfo)
                                    with self.nTransmitters.request() as req:
                                        yield req
                                        packetInfoOut = yield self.packetsFifo.get()
                                        yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
                            
                            elif(self.distanceValue > prevDistanceValue and nodes[prevRp].type.lower()!="ed" and packet.packetType=="WOR_up" and len(self.packetsFifo.items)==0):
                                self.mode = "CAD"
                                self.batteryUpdate(env, self.currentCad)
                                self.setIconColorByMode(env, get_linenumber())
                                self.worAckReceived = -1

                    else:
                        packetInfo = [seqNr, prevRp]
                        self.packetsFifo.put(packetInfo)
                        with self.nTransmitters.request() as req:
                            yield req
                            packetInfoOut = yield self.packetsFifo.get()
                            yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
                    
            else:
                if(debug):
                    print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")

                if(positional_algo):
                    standby = 0
                    
                    if(self.distanceValue < prevDistanceValue or prevDistanceValue == -1):
                        
                        packetInfo = [seqNr, prevRp]
                        
                        if(standby_repeater_algo):           
                            if(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="rp" and self.distanceValue>nodes[nextRp].distanceValue and self.distanceValue<nodes[prevRp].distanceValue):
                                standby = 1
                                standByTime = float(self.packet[0].rectime +self.packet[0].rectime*repeatDelayMultiplier*5)
                                standby = yield env.process(self.standbyMode(env, packetInfo, standByTime, prevRp))
                                if(standby == 1):
                                    self.packetsFifo.put(packetInfo)
                                    with self.nTransmitters.request() as req:
                                        yield req
                                        packetInfoOut = yield self.packetsFifo.get()
                                        yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))

                            elif(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="rp" and nodes[prevRp].distanceValue>nodes[nextRp].distanceValue>self.distanceValue):
                                if(energy_aware_algo):
                                    if(round(nodes[nextRp].batteryPercentage%10) == 0):
                                        if(nodes[nextRp].batteryPercentage<(self.batteryPercentage)):
                                            nodes[prevRp].nextRp = self.id
                            
                            elif(self.id == nextRp or nextRp == -1):
                                # print("received by the one addressed!")              
                                self.packetsFifo.put(packetInfo)
                                with self.nTransmitters.request() as req:
                                    yield req
                                    packetInfoOut = yield self.packetsFifo.get()
                                    yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
                        else:
                            self.packetsFifo.put(packetInfo)
                            with self.nTransmitters.request() as req:
                                yield req
                                packetInfoOut = yield self.packetsFifo.get()
                                yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))
            
                else:
                    packetInfo = [seqNr, prevRp]
                    self.packetsFifo.put(packetInfo)
                    with self.nTransmitters.request() as req:
                        yield req
                        packetInfoOut = yield self.packetsFifo.get()
                        yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1]))


    def standbyMode(self, env, packetInfo, standByTime, prevRp):
        global total_stanby
        global standby_retains
        global standby_recoveries
        global repeater_role_changes
        total_stanby += 1

        seqNr = packetInfo[0]
        x,y,t,pktType =seqNr.split("|")

        yield env.timeout(random.uniform(0.8*standByTime, 1.2*standByTime))
        # exactStandByTime = int(random.uniform(0.8*standByTime, 1.2*standByTime))
        # if(debug):
        #     print(f"Node {self.id}({self.type.upper()}) entering Standby for {exactStandByTime} ms at T={round(env.now,2)} (Pkt:{seqNr})")
        
        # k = 0
        # while(k < exactStandByTime):
        #     k +=1
        #     yield env.timeout(1)
        
        for item in self.lowerDistanceRecBuffer:
            if (item[0] == seqNr):
                if(energy_aware_algo):
                    if(round(item[1])%10 == 0):
                        if(item[1]<(self.batteryPercentage-10) and item[1] < (nodes[self.nextRpOriginal].batteryPercentage-10)):

                            if(nodes[prevRp].nextRpOriginal == -1):
                                nodes[prevRp].nextRpOriginal = nodes[prevRp].nextRp
                            nodes[prevRp].nextRp = self.id
                            if(self.nextRpOriginal != -1):
                                self.nextRp = self.nextRpOriginal
                            repeater_role_changes += 1

                standby_retains += 1
                return 0
    
        standby_recoveries += 1
        return 1
        

    def enableCad(self, env):
        global repeater_sleep_algo
        if(repeater_sleep_algo==0):
            return 0
        self.mode = "CAD"
        self.batteryUpdate(env, self.currentCad)
        self.setIconColorByMode(env, get_linenumber())
        # if((env.now - self.lastCadScanTime)%self.cadPeriodity != 0):
        #     yield env.timeout(self.cadPeriodity - (env.now - self.lastCadScanTime)%self.cadPeriodity)

        while(True):

            if(self.mode == "CAD"):
                # CAD Scan: Checking WOR channel activity
                self.lastCadScanTime = env.now
                # if(debug):
                #     print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Performing CAD Scan. [clock accuracy: {self.clockAccuracy*1000000:.2f} ppm]")
                for node in self.packetSourcesAtRx:
                    if node.tx_activity["in_preamble"](env) and (node.tx_activity["tx_packet_type"] == "WOR_up" or node.tx_activity["tx_packet_type"] == "WOR_down"):
                        self.mode = "RX"
                        self.batteryUpdate(env, self.currentRx)
                        self.setIconColorByMode(env, get_linenumber())
                        if(debug):
                            print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Detected WOR Packet from Node {node.id} during CAD")

            #if stuck in RX mode and idling somehow, go back to CAD
            if(self.mode == "RX" and len(self.packetSourcesAtRx) == 0 and self.standbyBufferCount==0 and (self.lastStateChangeTime+10000) < env.now):
                self.mode = "CAD"
                self.batteryUpdate(env, self.currentCad)
                self.setIconColorByMode(env, get_linenumber())
                self.worAckReceived = -1
                if(debug):
                    print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Switching back to CAD mode after idling in RX")

            global state_data_logging
            if(state_data_logging):    
                yield env.timeout(self.cadPeriodity*(1+self.clockAccuracy)-2)
                if(self.mode == "CAD"):
                    self.state_diagram_file.write(f"{env.now} CAD_Scan_rise\n")
                    yield env.timeout(1)
                    self.state_diagram_file.write(f"{env.now} CAD_Scan_fall\n")
                    yield env.timeout(1)
                else:
                    yield env.timeout(2)
            else:
                yield env.timeout(self.cadPeriodity*(1+self.clockAccuracy))

            #Exit CAD function after the end of the simulation
            if(lastPacketGenTime!= 0 and env.now > (lastPacketGenTime + 3600000)):
                break


    def repeat(self, env, seqNr, prevRp, nodeAcknowledged=-1):
        global nodes
        global packetsRecBS
        global collidedPackets
        global lostPackets
        global repeaterProcessingTime
        global fignum

        x,y,t,pktType =seqNr.split("|")

        self.mode = "RX"
        self.batteryUpdate(env, self.currentRx)
        self.setIconColorByMode(env, get_linenumber())

        # yield env.timeout(random.expovariate(1.0/float(nodes[prevRp].packet[0].rectime*repeatDelayMultiplier))) #wait random time with mean =airtime*repeatDelayMultiplier
        yield env.timeout(random.expovariate(1.0/10)) #wait random time with mean =10 ms

        # #modified carrier sensing
        if(carrier_sensing_rp ==1):
            while(True):
                if(len(self.packetSourcesAtRx) == 0): 
                    break
                yield env.timeout(random.expovariate(1.0/float(self.packet[0].rectime*repeatDelayMultiplier)))

        if(repeater_sleep_algo):
            if(pktType == "WOR_up" or pktType == "WOR_down"):
                self.createPackets(pktType, -1, intendedRxId=self.nextRp, nodeAcknowledged=nodeAcknowledged, seqNr=seqNr)
                self.tx_activity["tx_packet_type"] = pktType
            
            elif(pktType == "DATA_up" or pktType == "DATA_down"):
                self.createPackets(pktType, intendedRxId=self.nextRp, seqNr=seqNr)
                self.tx_activity["tx_packet_type"] = pktType

        else:
            self.createPackets("DATA_up", intendedRxId=self.nextRp, seqNr=seqNr)
            self.tx_activity["tx_packet_type"] = "DATA_up"

        self.tx_activity["active"] = True #starting transmission
        self.tx_activity["start"] = env.now
        self.tx_activity["end"] = env.now + self.packet[0].rectime
        self.tx_activity["preamble_duration"] = self.packet[0].Tprem
        self.tx_status_file.write(str(env.now))
        self.mode = "TX"
        self.batteryUpdate(env, self.currentTx)
        self.setIconColorByMode(env, get_linenumber())

        if(debug):
            print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Forwarded Packet:{seqNr}")
        
        self.txPackets.append(seqNr)
        global lastPacketGenTime
        if(lastPacketGenTime != 0 and self.txTimePercentage == 0 and lastPacketGenTime < env.now):
            self.txTimePercentage = (len(self.txPackets)*self.packet[0].rectime)/lastPacketGenTime
        
        for i in range(0, len(nodes)): #add the transmitting node itself too at its own rx
            self.packet[i].addTime = round(env.now, 1)
            self.packet[i].seqNr = seqNr
            self.packet[i].txBattery = self.batteryPercentage

            if(self.packet[i].lost == 0): #checking if the packet reachs at node[i]
                if (self in nodes[i].packetSourcesAtRx):
                    print("ERROR: Packet",self.packet[i].seqNr, "from node",self.id,"is already in node",i,"RX")
                else:
                    nodes[i].packetSourcesAtRx.append(self) 
                    # checking collision at the start of packet reception
                    if (checkcollision(self.packet[i], nodes[i])==1):
                        self.packet[i].collided = 1
                    else:
                        self.packet[i].collided = 0

        if(realtime_graphics  and graphics):
            self.drawTxArrows()
            self.drawTime(env)
            self.drawTransmittingInfo()
            self.markCollidedArrows()
            self.drawCollisionInfo()
            if(slideShowPause):
                plt.pause(slideShowPause)
            else:
                plt.waitforbuttonpress()
            ext = ".png"
            ext = ".png"
            figname = str(fignum) + ext
            save_path = os.path.join("plots", figname)
            fignum +=1
            plt.savefig(save_path)
        
        # air time (take first packet rectime)
        yield env.timeout(self.packet[0].rectime)
        self.tx_activity["active"] = False
        self.tx_status_file.write(" "+str(env.now)+"\n")
        
        #Whether goes back to RX mode or CAD
        if(repeater_sleep_algo):
            if((self.packet[0].packetType == "DATA_up" or self.packet[0].packetType == "DATA_down") and (len(self.packetsFifo.items) == 0)):
                self.mode = "CAD"
                self.batteryUpdate(env, self.currentCad)
                self.setIconColorByMode(env, get_linenumber())
                self.worAckReceived = -1

            else:
                self.mode = "RX"
                self.batteryUpdate(env, self.currentRx)
                self.setIconColorByMode(env, get_linenumber())
        else:
            self.mode = "RX"
            self.batteryUpdate(env, self.currentRx)
            self.setIconColorByMode(env, get_linenumber())

        if(realtime_graphics  and graphics):
            self.eraseTxArrows()

        # if packet did not collide, add it in list of received packets
        # unless it is already in
        nodesThatReceivedPkt = []
        for i in range(0, len(nodes)):
            if(i != self.id):
                if (self.packet[i].lost):
                    lostPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
                else:
                    if (self.packet[i].collided == 0):
                        if (nodes[i].mode == "RX"):
                            if(debug):
                                print(f"called nodes[{i}].receive() from node {self.id}")
                            env.process(nodes[i].receive(env, self.packet[i], self.packet[i].seqNr, self.distanceValue, self.nextRp, self.id))
                            nodesThatReceivedPkt.append(i)
                        # if (self.packet[i].seqNr not in nodes[i].recPackets):
                        #     nodes[i].recPackets.append(self.packet[i].seqNr)
                        #     env.process(nodes[i].receive(env, self.packet[i], self.packet[i].seqNr, self.distanceValue, self.nextRp, self.id))
                        # if (nodes[i].distanceValue >= self.distanceValue):
                        #     nodes[i].lowerDistanceRecBuffer.append([seqNr,self.batteryPercentage, self.id])
                    else:
                        # XXX only for debugging
                        collidedPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
        
        # if(debug):
        #     print("|____Nodes that received the packet:",nodesThatReceivedPkt)

        # complete packet has been received by base station
        # can remove it
        for i in range(0, len(nodes)):
            if (self in nodes[i].packetSourcesAtRx):
                nodes[i].packetSourcesAtRx.remove(self)
            # reset the packet
            self.packet[i].collided  = 0
            self.packet[i].processed = 0


    
    def transmissionSuccessRate(self):
        global packetsRecBS
        for seqNr in packetsRecBS:
            x,y,t,pktType =seqNr.split("|")
            if(self.id == int(x)):
                self.sentSuccessful += 1
        if(self.sent == 0):
            return 0
        else:
            return (float(self.sentSuccessful)/self.sent)


#
# this creates a packet associated between a pair of nodes
#
class myPacket():
    def __init__(self, nodeid, payloadLen, distance, rxNodeId,
                 txPower=14, sf=12, cr=4, bw=125, freq=860000000, packetType="OTHER", premlen=8, intendedRxNodeId=-1, nodeAcknowledged=-1, seqNr=None, addTime=None):
        global experiment
        global gamma
        global d0
        global var
        global Lpld0
        global GL
        global minsensi
        global nodes
        self.seqNr = seqNr
        self.addTime = addTime
        self.rxNodeId = rxNodeId
        self.intendedRxNodeId = intendedRxNodeId
        self.nodeAcknowledged = nodeAcknowledged
        self.nodeid = nodeid
        self.nearestGwId = nodes[nodeid].nearestGwId
        self.payloadLen = payloadLen
        self.preambleLen = premlen
        self.packetType = packetType

        #LoRa Parameters
        self.ptx  = txPower
        self.sf   = sf 
        self.cr   = cr
        self.bw   = bw
        self.freq = freq

        #Transmission related parameters
        if(distance != 0):
            Lpl = Lpld0 + 10*gamma*math.log10(distance/d0)
        else:
            Lpl = 0
        self.rssi = self.ptx - GL - Lpl
        self.symTime = (2.0**self.sf)/self.bw

        self.collided = 0
        self.processed = 0
        if(self.bw == 125):
            minsensi = sensi[self.sf-7][1]
        elif(self.bw == 250):
            minsensi = sensi[self.sf-7][2]
        elif(self.bw == 500):
            minsensi = sensi[self.sf-7][3]
        self.lost = self.rssi < minsensi

        self.Tprem, self.Tpayload = airtime(self.sf,self.cr,self.payloadLen,self.bw, self.preambleLen)
        self.rectime = self.Tprem + self.Tpayload


        global debug
        # if(debug):
        #     print ("\nCreated pkt from Node {} to Node {} |lost: {}".format(self.nodeid, self.rxNodeId, self.lost))
        #     print ("  Distance", distance)
        #     print ("  Ptx: ",self.ptx)
        #     print ("  Lpl: ",Lpl)
        #     print ("  Prx: ", self.rssi)
        #     print ("  MinSensi: ",minsensi)
        #     print ("  Pkt Length: ",self.payloadLen)
        #     print ("  Freq: ", self.freq)
        #     print ("  SF:",self.sf," BW:",self.bw," CR:",self.cr)       


#
# Network graph for position & routing calculations
#
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
        min_val = float('inf')
        min_index = -1
        for v in range(self.V):
            if dist[v] < min_val and sptSet[v] == False:
                min_val = dist[v]
                min_index = v
        return min_index
        
    def dijkstra(self, src):
        dist = [float('inf')] * self.V
        dist[src] = 0
        sptSet = [False] * self.V
        
        # Track visited nodes to identify isolated ones
        visited = set()
        
        for cout in range(self.V):
            u = self.minDistance(dist, sptSet)
            if u == -1:  # No reachable nodes found
                break
            sptSet[u] = True
            visited.add(u)
            for v in range(self.V):
                if (self.graph[u][v] > 0 and 
                    sptSet[v] == False and 
                    dist[v] > dist[u] + self.graph[u][v]):
                    dist[v] = dist[u] + self.graph[u][v]
        
        # Print isolated nodes (nodes not visited during traversal)
        isolated_nodes = set(range(self.V)) - visited
        if isolated_nodes:
            print(f"\nIsolated nodes from source {src}:", list(isolated_nodes))
        
        self.printSolution(dist, src)
        return dist