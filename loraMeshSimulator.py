import simpy
import random
import numpy as np
import math
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg

# Debug Mode
debug = 1

# turn on/off graphics
graphics = 1
realtime_graphics = 0
fignum = 1
slideShowPause = 0.0 #number of seconds to pause OR 0 to wait until key press

# do the full collision check
full_collision = True

#carrier sensing
carrier_sensing_ed = False
carrier_sensing_rp = True 

#global awareness
positional_algo = True
standby_repeater_algo = True
energy_aware_algo = True

total_stanby = 0
standby_retains = 0
standby_recoveries = 0
repeater_role_changes = 0

# Averaege packet sending interval of end devices
avgSendTime = 600000 #in ms 
repeatDelayMultiplier = 5 #mean repeater waiting period = airtime * repeatDelayMultiplier 

# experiments:
# 0: packet with longest airtime, aloha-style experiment
# 1: one with 3 frequencies, 1 with 1 frequency
# 2: with shortest packets, still aloha-style
# 3: with shortest possible packets depending on distance
experiment = 11

# These are arrays with measured values for sensitivity
#---------------SF---125-----250-----500----(BW in kHz)
sf7  = np.array([7, -126.50,-124.25,-120.75])
sf8  = np.array([8, -127.25,-126.75,-124.00])
sf9  = np.array([9, -131.25,-128.25,-127.50])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.50,-132.75,-128.75])
# sf12 = np.array([12,-133.25,-132.25,-132.25])
sf12 = np.array([12,-134.50,-132.25,-132.25])

#COLLISION CHECK
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
        if(debug):
            print("   --collision since node",receiverNode.id,"is in transmitting state")
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
    for i in range(len(mainNodes)):
        if(mainNodes[i].type == "gw"):
            distFromGWs.append(g.dijkstra(i))

    dist = [1e7 for x in range(len(mainNodes))]

    for distset in distFromGWs:
        for i in range(len(dist)):
            if(distset[i]<dist[i]):
                dist[i] = distset[i]

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

    k = 0
    for i in range(len(nodes)):
        if(nodes[i].type == "rp" or nodes[i].type == "gw"):
            nodes[i].nextRp = nextNodeUp[k]
            nodes[i].nextRpOriginal = nextNodeUp[k]
            nodes[i].distanceValue = dist[k]
            k = k + 1


    # print("\nNode \t Next RP/GW (Upstream) \t  Neighbours")
    # for i in range(len(nextNodeUp)):
    #     print(i, "\t\t", nextNodeUp[i], "\t\t", mainNodes[i].neighbor_ids)

    

#
# This is called to configure the network after creating all nodes
#
def networkConfig():
    global nodes
    for i in range(len(nodes)):
        nodes[i].createPackets()
        if(realtime_graphics == 1 and graphics == 1):
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
        ymax = ymax*1.6
        
        ax.add_patch(Rectangle((0, 0), xmax, ymax, fill=None, alpha=1))
        current_script_path = os.path.abspath(__file__)
        current_script_directory = os.path.dirname(current_script_path)
        legendImg = mpimg.imread(current_script_directory+"/simulatorLegend.png")
        ax.imshow(legendImg, extent=(xmax*0.03, xmax*0.19, ymax*0.68, ymax*0.92), aspect='auto')


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
        self.distanceValue = -1
        self.nextRp = -1
        self.nextRpOriginal = -1

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

        #local neighbourhood awareness
        self.neighbor_ids = []
        self.neighbor_rssi = []

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
        self.packetlen = 20

        #properties specific to repeaters
        self.packetsFifo = simpy.Store(env)
        self.nTransmitters = simpy.Resource(env, capacity=1)
        self.tx_activity["active"] = False
        self.standbyBuffer = []
        self.lowerDistanceRecBuffer = []
        self.txTimePercentage = 0

        #data dump files
        tx_status_file_name = 'tx status data\dump_node_'+ str(self.id)+'.txt'       
        self.tx_status_file = open(tx_status_file_name, 'w')
        # self.tx_status_file.write("initiated file for node"+str(self.id))
        
        battery_status_file_name = 'battery status data\dump_node_'+ str(self.id)+'.csv'       
        self.battery_status_file = open(battery_status_file_name, 'w')
        # self.battery_status_file.write("initiated file for node"+str(self.id)+"\n")
        self.battery_status_file.write(f"{self.id},{env.now},{self.batteryRemaining},{round(self.batteryPercentage,2)}\n")

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            if  (self.type.lower() == "ed"):
                ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))
                ax.add_artist(plt.text(self.x+6,self.y,self.id))
            elif(self.type.lower() == "rp"):
                ax.add_artist(plt.Circle((self.x, self.y), 4, fill=True, color='green'))
                ax.add_artist(plt.text(self.x+11,self.y,self.id))
            elif(self.type.lower() == "gw"):
                ax.add_artist(plt.Circle((self.x, self.y), 4, fill=True, color='red'))
                ax.add_artist(plt.text(self.x+11,self.y,self.id))
            else:
                print("Incorrect device type!")


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


    def createPackets(self, packetType = "OTHER", premlen=8):
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

        if(debug):
            print(self.type.upper(),":",self.id, "x", self.x, "y", self.y, "dist: ", self.dist)


        #cr =1,2,3,or 4
        #cr = 1 corresponds to coding rate 4/5 and cr=4 corresponds to coding rate 4/8
        # 4/8 coding rate means that for every 4 bits of useful information the coder generates 8bits of data including error correction bits
        # determining tx LoRa params       
        if(experiment == 0):
            sf = 12
            cr = 2
            bw = 125
            freq = 915900000

        if(experiment == 1):
            sf = 12
            cr = 2
            bw = 125
            freq = 915900000
            if (self.type.lower() == "ed"):
                freq = 917500000
        
        
        elif(experiment == 2):
            sf = 7
            cr = 2
            bw = 500
            freq = 915900000


        elif(experiment == 3):
            sf = 7
            cr = 2
            bw = 500
            freq = 915900000
            if (self.type.lower() == "ed"):
                freq = 917500000

        if(experiment == 4):
            sf = 12
            cr = 2
            bw = 500
            freq = 915900000
        
        if(experiment == 5):
            sf = 11
            cr = 2
            bw = 500
            freq = 915900000

        if(experiment == 6):
            sf = 10
            cr = 2
            bw = 500
            freq = 915900000

        if(experiment == 7):
            sf = 9
            cr = 2
            bw = 500
            freq = 915900000

        if(experiment == 8):
            sf = 8
            cr = 2
            bw = 500
            freq = 915900000

        if(experiment == 9):
            sf = 7
            cr = 2
            bw = 500
            freq = 915900000

        if(experiment == 10):
            sf = 12
            cr = 2
            bw = 500
            freq = 915900000
            if (self.type.lower() == "ed"):
                freq = 917500000

        if(experiment == 11):
            sf = 7
            cr = 2
            bw = 500
            freq = 915900000
            if (self.type.lower() == "ed"):
                freq = 917500000
        
        elif(experiment == 40):
            #incomplete
            freq = random.choice([860000000, 864000000, 868000000])
        
        elif(experiment == 50):
            sf = random.randint(6,12)
            cr = random.randint(1,4)
            bw = random.choice([125, 250, 500])
            freq = random.choice([860000000, 864000000, 868000000])
   
        # create virtual packets for each other node
        self.packet = []
        if(packetType == "WOR_up" or packetType == "WOR_down"):
            for i in range(0,len(nodes)):
                if(self.type.upper() == "ED"):
                    self.packet.append(myPacket(self.id, 15, self.dist[i], i, 0, sf, cr, bw, freq, packetType, premlen))
                else:
                    self.packet.append(myPacket(self.id, 15, self.dist[i], i, Ptx, sf, cr, bw, freq, packetType, premlen))
        else:
            for i in range(0,len(nodes)):
                if(self.type.upper() == "ED"):
                    self.packet.append(myPacket(self.id, 20, self.dist[i], i, 0, sf, cr, bw, freq, packetType, premlen))
                else:
                    self.packet.append(myPacket(self.id, 20, self.dist[i], i, Ptx, sf, cr, bw, freq, packetType, premlen))


    def drawTxArrows(self):
        for i in range(len(self.packet)):
            pk = self.packet[i]
            if(pk.lost == False):
                x = nodes[pk.nodeid].x
                y = nodes[pk.nodeid].y
                dx = nodes[pk.rxNodeId].x -x
                dy = nodes[pk.rxNodeId].y -y
                if(nodes[pk.rxNodeId].type.upper() == "ED"):
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
                txInfoString += f"Node {transmittingNodeIDsTemp[i]} transmitting pkt {nodes[transmittingNodeIDsTemp[i]].packet[0].seqNr}\n"
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
            colInfoString += f"Node {pk.nodeid} to Node {pk.rxNodeId} transmission collided\n"

        if(colInfoPlot != None):
            colInfoPlot.remove()
        colInfoPlot = plt.text(xmax*0.66, ymax*0.95, colInfoString, fontsize='large', verticalalignment='top')

    def transmitOnce(self, env):
        #carrier sensing
        if(carrier_sensing_ed ==1): 
            while(len(self.packetSourcesAtRx) != 0):
                yield env.timeout(1)
                if(debug):
                    print("ED: waiting till medium is idle")
        

        global packetSeq
        packetSeq = packetSeq + 1

        global totalSimPackets

        self.tx_activity["active"] = True
        self.createPackets("DATA_up")
        self.tx_activity["start"] = env.now
        self.tx_activity["end"] = env.now + self.packet[0].rectime
        self.tx_activity["preamble_duration"] = self.packet[0].Tprem
        self.tx_activity["tx_packet_type"] = "DATA_up"
        self.sent = self.sent + 1

        global nodes
        global lostPackets
        global collidedPackets
        global fignum

        if(debug):
            print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Transmitted Packet:{self.id}|{packetSeq}")

        for i in range(0, len(nodes)):
            self.packet[i].addTime = round(env.now, 0)
            self.packet[i].seqNr = f"{self.id}|{packetSeq}|{self.packet[i].addTime}"
            
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
        
        if(realtime_graphics  and graphics):
            self.eraseTxArrows()

        # if packet did not collide, add it in list of received packets
        # unless it is already in
        for i in range(0, len(nodes)):
            if(i != self.id):
                if self.packet[i].lost:
                    lostPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
                else:
                    if ((self.packet[i].collided == 0) and (self.packet[i].processed == 1)):
                        if (self.packet[i].seqNr not in nodes[i].recPackets):
                            nodes[i].recPackets.append(self.packet[i].seqNr)
                            env.process(nodes[i].receive(env, self.packet[i].seqNr, self.packetlen, self.distanceValue, self.nextRp, self.id))
                    else:
                        # XXX only for debugging
                        collidedPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")

        # complete packet has been received by base station
        # can remove it
        for i in range(0, len(nodes)):
            if (self in nodes[i].packetSourcesAtRx):
                nodes[i].packetSourcesAtRx.remove(self)
            # reset the packet
            self.packet[i].collided = 0
            self.packet[i].processed = 0


    #only for the transmission by end-devices
    def transmit(self, env):
        while(True):
            yield env.timeout(random.expovariate(1.0/float(self.period)))

            #carrier sensing
            if(carrier_sensing_ed ==1): 
                while(len(self.packetSourcesAtRx) != 0):
                    yield env.timeout(1)
                    if(debug):
                        print("ED: waiting till medium is idle")
            

            global packetSeq
            global lastPacketGenTime
            packetSeq = packetSeq + 1

            global totalSimPackets
            if (packetSeq > totalSimPackets):
                lastPacketGenTime = env.now
                break

            self.tx_activity["active"] = True
            self.createPackets("DATA_up")
            self.tx_activity["start"] = env.now
            self.tx_activity["end"] = env.now + self.packet[0].rectime
            self.tx_activity["preamble_duration"] = self.packet[0].Tprem
            self.tx_activity["tx_packet_type"] = "DATA_up"
            self.sent = self.sent + 1
            self.tx_status_file.write(str(env.now))

            global nodes
            global lostPackets
            global collidedPackets
            global fignum

            if(debug):
                print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Transmitted Packet:{self.id}|{packetSeq}")

            for i in range(0, len(nodes)):
                self.packet[i].addTime = round(env.now, 1)
                self.packet[i].seqNr = f"{self.id}|{packetSeq}|{self.packet[i].addTime}"
                
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
            
            if(realtime_graphics  and graphics):
                self.eraseTxArrows()

            # if packet did not collide, add it in list of received packets
            # unless it is already in
            for i in range(0, len(nodes)):
                if(i != self.id):
                    if self.packet[i].lost:
                        lostPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
                    else:
                        if ((self.packet[i].collided == 0) and (self.packet[i].processed == 1)):
                            if (self.packet[i].seqNr not in nodes[i].recPackets):
                                nodes[i].recPackets.append(self.packet[i].seqNr)
                                env.process(nodes[i].receive(env, self.packet[i].seqNr, self.packetlen, self.distanceValue, self.nextRp, self.id))
                        else:
                            # XXX only for debugging
                            collidedPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")

            # complete packet has been received by base station
            # can remove it
            for i in range(0, len(nodes)):
                if (self in nodes[i].packetSourcesAtRx):
                    nodes[i].packetSourcesAtRx.remove(self)
                # reset the packet
                self.packet[i].collided = 0
                self.packet[i].processed = 0


    def receive(self, env, seqNr, packetlen, prevDistanceValue, nextRp, prevRp):
        self.batteryUpdate(env, self.currentRx)
        yield env.timeout(repeaterProcessingTime) #wait for the processing time
        self.batteryUpdate(env, self.currentCad)

        #check if it is a gateway
        if (self.type.lower() == "gw"):
            #Do no more transmissions. Account the packets received.
            if(debug):
                print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
                # print("T =",env.now, "|GW",self.id, "Received Packet:",seqNr,"\n")
            if seqNr not in packetsRecBS:
                packetsRecBS.append(seqNr)
                x,y,t =seqNr.split("|")
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
            if(debug):
                print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")
                # print("T =",env.now, "|ED",self.id, "Received Packet:",seqNr,"\n")
        
        #if it is a repeater
        else:
            if(debug):
                print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Received Packet:{seqNr}")

            if(positional_algo):
                standby = 0
                
                if(self.distanceValue < prevDistanceValue or prevDistanceValue == -1):
                    
                    packetInfo = [seqNr, packetlen, standby]
                    
                    if(standby_repeater_algo):           
                        if(self.id != nextRp and nextRp != -1 and nodes[nextRp].type.lower()=="rp" and self.distanceValue>nodes[nextRp].distanceValue and self.distanceValue<nodes[prevRp].distanceValue):
                            standby = 1
                            standByTime = float(self.packet[0].rectime +self.packet[0].rectime*repeatDelayMultiplier*5)
                            yield env.process(self.standbyMode(env, packetInfo, standByTime, prevRp))

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
                                yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[2]))
                    else:
                        self.packetsFifo.put(packetInfo)
                        with self.nTransmitters.request() as req:
                            yield req
                            packetInfoOut = yield self.packetsFifo.get()
                            yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[2]))
           


            else:
                packetInfo = [seqNr,packetlen, 0]
                self.packetsFifo.put(packetInfo)
                with self.nTransmitters.request() as req:
                    yield req
                    packetInfoOut = yield self.packetsFifo.get()
                    yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[2]))


    def standbyMode(self, env, packetInfo, standByTime, prevRp):
        global total_stanby
        global standby_retains
        global standby_recoveries
        global repeater_role_changes
        total_stanby += 1

        seqNr = packetInfo[0]

        self.batteryUpdate(env, self.currentRx)
        yield env.timeout(random.uniform(0.8*standByTime, 1.2*standByTime))
        self.batteryUpdate(env, self.currentCad)
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

        #Hard Code ???
        if(self.id == 1 or self.id ==17):
            print("EEEEERRRRRORRRR!!!!!")
        #     return 0
        # if(nodes[self.nextRp].type.lower() == "gw"):
        #     return 0
        
        standby_recoveries += 1
        self.packetsFifo.put(packetInfo)
        with self.nTransmitters.request() as req:
            yield req
            packetInfoOut = yield self.packetsFifo.get()
            yield env.process(self.repeat(env, packetInfoOut[0], packetInfoOut[1], packetInfoOut[2]))


    def repeat(self, env, seqNr, packetlen, standby):
        global nodes
        global packetsRecBS
        global collidedPackets
        global lostPackets
        global repeaterProcessingTime
        global fignum

        self.batteryUpdate(env, self.currentRx)
        yield env.timeout(random.expovariate(1.0/float(self.packet[0].rectime*repeatDelayMultiplier))) #wait random time with mean =airtime*repeatDelayMultiplier

        # #modified carrier sensing
        if(carrier_sensing_rp ==1):
            while(True):
                if(len(self.packetSourcesAtRx) == 0): 
                    break
                yield env.timeout(random.expovariate(1.0/float(self.packet[0].rectime*repeatDelayMultiplier)))

        
        self.tx_activity["active"] = True #starting transmission
        self.createPackets("DATA_up")
        self.tx_activity["start"] = env.now
        self.tx_activity["end"] = env.now + self.packet[0].rectime
        self.tx_activity["preamble_duration"] = self.packet[0].Tprem
        self.tx_activity["tx_packet_type"] = "DATA_up"
        self.tx_status_file.write(str(env.now))
        self.batteryUpdate(env, self.currentTx)

        if(debug):
            print(f"\nT = {env.now:.2f}| Node {self.id}({self.type.upper()}) Forwarded Packet:{seqNr}")
        
        self.txPackets.append(seqNr)
        global lastPacketGenTime
        if(lastPacketGenTime != 0 and self.txTimePercentage == 0 and lastPacketGenTime < env.now):
            self.txTimePercentage = (len(self.txPackets)*self.packet[0].rectime)/lastPacketGenTime
        
        for i in range(0, len(nodes)): #add the transmitting node itself too at its own rx
            self.packet[i].addTime = env.now
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
        self.batteryUpdate(env, self.currentCad)
        
        if(realtime_graphics  and graphics):
            self.eraseTxArrows()

        # if packet did not collide, add it in list of received packets
        # unless it is already in
        for i in range(0, len(nodes)):
            if(i != self.id):
                if (self.packet[i].lost):
                    lostPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")
                else:
                    if (self.packet[i].collided == 0):
                        if (self.packet[i].seqNr not in nodes[i].recPackets):
                            nodes[i].recPackets.append(self.packet[i].seqNr)
                            env.process(nodes[i].receive(env, self.packet[i].seqNr, packetlen, self.distanceValue, self.nextRp, self.id))
                        if (nodes[i].distanceValue >= self.distanceValue):
                            nodes[i].lowerDistanceRecBuffer.append([seqNr,self.batteryPercentage, self.id])
                    else:
                        # XXX only for debugging
                        collidedPackets.append(f"{nodes[i].type.upper()}:{nodes[i].id} SeqNr:{self.packet[i].seqNr}")

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
            x,y,t =seqNr.split("|")
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
    def __init__(self, nodeid, plen, distance, rxNodeId,
                 txPower=14, sf=12, cr=4, bw=125, freq=860000000, packetType="OTHER", premlen=8):
        global experiment
        global gamma
        global d0
        global var
        global Lpld0
        global GL
        global minsensi
        global nodes
        self.seqNr = None
        self.rxNodeId = rxNodeId
        self.nodeid = nodeid
        self.pl = plen
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

        self.Tprem, self.Tpayload = airtime(self.sf,self.cr,self.pl,self.bw)
        if(premlen == 8):
            self.rectime = self.Tprem + self.Tpayload
        else:
            self.Tprem = self.symTime * (premlen + 4.25)
            self.rectime = self.Tprem + self.Tpayload


        global debug
        if(debug):
            print ("\nCreated pkt from Node {} to Node {} |lost: {}".format(self.nodeid, self.rxNodeId, self.lost))
            print ("  Distance", distance)
            print ("  Ptx: ",self.ptx)
            print ("  Lpl: ",Lpl)
            print ("  Prx: ", self.rssi)
            print ("  MinSensi: ",minsensi)
            print ("  Pkt Length: ",self.pl)
            print ("  Freq: ", self.freq)
            print ("  SF:",self.sf," BW:",self.bw," CR:",self.cr)       


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


# ----------------------------------------------------------------------------------
# "main" program
# ----------------------------------------------------------------------------------

# global stuff
env = simpy.Environment()

# global value of packet sequence numbers
packetSeq = 0
totalSimPackets = 20
lastPacketGenTime = 0

# list of nodes
nodes = []
repeaterProcessingTime = 100
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


#Graphic related variables
timePlot = None
txInfoPlot = None
transmittingNodeIDs = []
colInfoPlot = None

#Path loss function parameters
Ptx = 14
gamma = 2.08
d0 = 40.0
var = 0  # variance ignored for now
Lpld0 = 127.41
GL = 0

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])

## figure out the minimal sensitivity for the given experiment
minsensi = -200.0
if experiment in [0,1]:
    minsensi = sensi[5,1]  # 6th row is SF12, 2nd column is BW125

elif experiment in [2,3]:
    minsensi = sensi[0][3] # 1st row is SF7, 4th column is BW500

elif experiment == 4:
    minsensi = sensi[5][3] # 6th row is SF12, 4th column is BW500
elif experiment == 5:
    minsensi = sensi[4][3] # 5th row is SF11, 4th column is BW500
elif experiment == 6:
    minsensi = sensi[3][3] # 4th row is SF10, 4th column is BW500
elif experiment == 7:
    minsensi = sensi[2][3] # 3th row is SF9, 4th column is BW500
elif experiment == 8:
    minsensi = sensi[1][3] # 2th row is SF8, 4th column is BW500
elif experiment == 9:
    minsensi = sensi[0][3] # 1st row is SF7, 4th column is BW500

elif experiment == 10:
    minsensi = sensi[5][3] # 6th row is SF12, 4th column is BW500
elif experiment == 11:
    minsensi = sensi[0][3] # 1st row is SF7, 4th column is BW500

    # minsensi = -112.0   # no experiments, so value from datasheet

# elif experiment == [3, 5]:
#     minsensi = np.amin(sensi) ## can use any setting, so take minimum

Lpl = Ptx - minsensi
maxDist = d0*(10**((Lpl-Lpld0)/(10.0*gamma))) #CORRECTED MISTAKE HERE: REPLACED 'e' with 10
print ("amin", minsensi, "Lpl", Lpl)
print ("maxDist:", maxDist)

xmax = 0
ymax = 0

# prepare graphics and add sink
if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()

