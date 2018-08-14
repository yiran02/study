import random
import math 
import optimization
# The dorms, each of which has two available spaces
dorms=['Zeus','Athena','Hercules','Bacchus','Pluto']
    # People, along with their first and second choices
prefs=[('Toby', ('Bacchus', 'Hercules')),
        ('Steve', ('Zeus', 'Pluto')),
        ('Andrea', ('Athena', 'Zeus')),
        ('Sarah', ('Zeus', 'Pluto')),
        ('Dave', ('Athena', 'Bacchus')),
        ('Jeff', ('Hercules', 'Pluto')),
        ('Fred', ('Pluto', 'Athena')),
        ('Suzie', ('Bacchus', 'Hercules')),
        ('Laura', ('Bacchus', 'Hercules')),
        ('Neil', ('Hercules', 'Athena'))]

domain = [(0,len(dorms)*2-i-1) for i in range(0,len(dorms)*2)]

def printsolution(vec):
    slots=[]
    # Create two slots for each dorm
    for i in range(len(dorms)): 
        slots+=[i,i]
    for i in range(len(vec)):
        x=vec[i]
        dorm=dorms[slots[x]]
        print(prefs[i][0],':',dorm)
        del slots[x]   
        
#cost function
def dormcost(vec):
    cost=0
    # Create two slots for each dorm
    slots=[0,0,1,1,2,2,3,3,4,4]
    for i in range(len(vec)):
        x=vec[i]
        dorm=dorms[slots[x]]
        pref=prefs[i][1]
        if dorm==pref[0]:
            cost+=0
        elif dorm==pref[1]:
            cost+=1
        else:
            cost+=3
        
        del slots[x] 
    return cost

if __name__=='__main__':
    s=optimization.randomoptimize(domain,dormcost)
    printsolution(s)