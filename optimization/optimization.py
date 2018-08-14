import random
import time
import math

people = [('Seymour','BOS'),
          ('Franny','DAL'),
          ('Zooey','CAK'),
          ('Walt','MIA'),
          ('Buddy','ORD'),
           ('Les','OMA')]
# LaGuardia airport in New York
destination='LGA'

flights = {}
with open('schedule.txt') as f:
    for line in f:
        origin,dest,depart,arrive,price = line.strip().split(',')
        flights.setdefault((origin,dest),[])
        flights[(origin,dest)].append((depart,arrive,int(price)))

        
def getminute(t):
    x=time.strptime(t,'%H:%M')
    return x[3]*60+x[4]

def printschedule(r):
    for d in range(int((len(r)/2))):
        name=people[d][0]
        origin=people[d][1]
        out=flights[(origin,dest)][r[2*d]]
        ret=flights[(dest,origin)][r[2*d+1]]
        print('%10s%10s %5s-%5s $%3s %5s-%5s $%3s'%(name,origin,
                                                   out[0],out[1],out[2],
                                                   ret[0],ret[1],ret[2]))
        
#cost function
def schedulecost(sol):
    totalcost=0
    totalwait=0
    latestarrival=0
    earliestdep=24*60
    for d in range(int(len(sol)/2)):
        origin=people[d][1]
        outbound=flights[(origin,dest)][sol[2*d]]
        returnf=flights[(dest,origin)][sol[2*d+1]]
        
        totalcost+=outbound[2]
        totalcost+=returnf[2]
        
        if latestarrival<getminute(outbound[1]):
            latestarrival=getminute(outbound[1])
        if earliestdep>getminute(returnf[0]):
            earliestdep=getminute(returnf[0])
    for d in range(int(len(sol)/2)):
        origin=people[d][1]
        outbound=flights[(origin,dest)][sol[2*d]]
        returnf=flights[(dest,origin)][sol[2*d+1]]
        
        totalwait+=latestarrival-getminute(outbound[1])
        totalwait+=getminute(returnf[0])-earliestdep
        
    # rent for car
    if latestarrival<earliestdep:
        totalcost+=50
    
    return totalcost+totalwait

# random search
def randomoptimize(domain,costf):
    best=9999999999
    bestr=None
    for i in range(10000):
        r=[random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
    cost=costf(r)
    if cost<best:
        best=cost
        bestr=r
    return r
    
#hill climbing
def hillclimb(domain,costf):
    sol = [random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
    neighbors=[]
    while 1:
        for i in range(len(domain)):
            if sol[i]<domain[i][1]:
                neighbors.append(sol[0:i]+[sol[i]-1 if sol[i]-1>domain[i][0] else domain[i][1]]+sol[i+1:])
            if sol[i]>domain[i][0]:
                neighbors.append(sol[0:i]+[sol[i]+1 if sol[i]+1<domain[i][1] else domain[i][0]]+sol[i+1:])
        current=costf(sol)
        best=current
        for i in range(len(neighbors)):
            cost=costf(neighbors[i])
            if cost<best:
                best=cost
                sol=neighbors[i]
        if cost==best:
            break
    
    
    return sol

#Simulated Annealing
def annealingoptimize(domain,costf,T=1000.0,cool=0.95,step=1):
    vec = [random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
    while T>0.1:
        
        i=random.randint(0,len(domain)-1)
        dir_=random.randint(-step,step)
        vecb=vec[:]
        vecb[i]+=dir_
        if vecb[i]<domain[i][0]:
            vecb[i]=domain[i][0]
        elif vecb[i]>domain[i][1]:
            vecb[i]=domain[i][1]
    
        ea=costf(vec)
        eb=costf(vecb)
        p=pow(math.e,(-ea-eb)/T)
    
        if ea>eb or random.random()<p:
            vec=vecb
        T=T*cool
    return vec

#genetic algorithms
def geneticoptimize(domain,costf,popsize=50,mutprod=0.2,elite=0.2,step=1,maxiter=150):
    #mutation operation
    def mutate(vec):
        if random.random()<0.7:
            i=random.randint(0,len(domain)-1)
            if vec[i]<domain[i][1]:
                return vec[0:i]+[vec[i]+step]+vec[i+1:]
            elif vec[i]>domain[i][0]:
                return vec[0:i]+[vec[i]-step]+vec[i+1:]
            elif vec[i]==domain[i][0]:
                return vec[0:i]+[domain[i][1]]+vec[i+1:]
            elif vec[i]==domain[i][1]:
                return vec[0:i]+[domain[i][0]]+vec[i+1:]
        return vec
    #crossover operation
    def crossover(r1,r2):
        i=random.randint(0,len(domain)-2)
        return r1[0:i]+r2[i:]
    
    #initial population
    pop=[]
    for i in range(popsize):
        vec=[random.randint(domain[j][0],domain[j][1]) for j in range(len(domain))]
        pop.append(vec)
    
    topelite=int(elite)*popsize
    #main loop
    for i in range(maxiter):
        scores = [(costf(v),v) for v in pop]
        scores.sort()
        ranked = [v for u,v in scores]
    
        pop = ranked[0:topelite]
        while len(pop)<popsize:
            if random.random()<mutprod:
                c=random.randint(0,topelite)
                pop.append(mutate(ranked[c]))
            else:
                c1=random.randint(0,topelite)
                c2=random.randint(0,topelite)
                pop.append(crossover(ranked[c1],ranked[c2]))
        # print current best score        
        print(scores[0][0])
    return scores[0][1]



if __name__ == '__main__':
    domain = [(0,9)]*len(people)*2
    s = geneticoptimize(domain,schedulecost)
    printschedule(s)