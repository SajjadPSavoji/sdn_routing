import matplotlib.pyplot as plt

class FT():
    def __init__(self, ft_string):
        '''
        dpid=1 src=e6:9a:b3:e3:16:85 dst=ee:0d:33:e9:b8:a7 in_port=1 out_port=2 time=4.8078379631
        '''
        self.dpid = None
        self.src = None
        self.dst = None
        self.in_port = None
        self.out_port = None
        self.time = None
        self.attrs = [self.dpid, self.src, self.dst, self.in_port, self.out_port, self.time]

        ft_seperated = ft_string.split()
        for i, part in enumerate(ft_seperated):
            temp = part.split('=')
            if temp[0] == 'time':
                self.attrs[i]  = float(temp[1])
                self.time = float(temp[1])
            elif temp[0] == 'dpid':
                self.attrs[i]  = temp[1]
                self.dpid  = temp[1]
            elif temp[0] == 'src':
                self.attrs[i]  = temp[1]
                self.src  = temp[1]
            elif temp[0] == 'dst':
                self.attrs[i]  = temp[1]
                self.dst  = temp[1]
            elif temp[0] == 'in_port':
                self.attrs[i]  = temp[1]
                self.in_port  = temp[1]
            elif temp[0] == 'out_port':
                self.attrs[i]  = temp[1]
                self.out_port  = temp[1]


    def __str__(self):
        return str(self.attrs)
    def __repr__(self):
        return self.__str__()

fts = []

with open('flowtable.trace', 'r') as f:
    while(True):
        line = f.readline()
        if not line:
            break
        fts.append(FT(line))

dpids = []
for ft in fts:
    if not ft.dpid in dpids:
        dpids.append(ft.dpid)

dpid_ft_map = {}
rates = {}
for dpid in dpids:
    dpid_ft_map[dpid] = []
    rates[dpid] = -1

for ft in fts:
    dpid_ft_map[ft.dpid].append(ft)

for dpid in dpids:
    data = [x.time for x in dpid_ft_map[dpid]]
    rates[dpid] = len(data)/(max(data) - min(data))

for dpid in dpids:
    plt.plot([x.time for x in dpid_ft_map[dpid]], [i for i in range(len(dpid_ft_map[dpid]))], label='s'+dpid + ":  rate={:.2f}".format(rates[dpid]))
plt.grid()
plt.legend()
plt.xlabel('time')
plt.ylabel('updates made')
plt.title('update frequency of flow tables in switches')
plt.savefig('res_updates.png')