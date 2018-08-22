from random import random,randint
import math
from pylab import *
import optimization

def wineprice(rating,age):
    peak_age=rating-50
     # Calculate price based on rating
    price=rating/2
    if age>peak_age:
        # Past its peak, goes bad in 5 years
        price = price*(5-(age-peak_age))
    else:
        # Increases to 5x original value as it
        # approaches its peak
        price = price*(5*((age+1)/peak_age))
    if price<0:
        return 0
    return price

def wineset():
    rows=[]
    for i in range(300):
        rating=random()*50+50
        age=random()*50
        
        price=wineprice(rating,age)
        # Add some noise 
        price*=(random( )*0.4+0.8)
        rows.append({'input':(rating,age),
                   'result':price})
    return rows

def wineset2():
    rows=[]
    for i in range(300):
        rating=random()*50+50
        age=random()*50
        aisle=float(randint(1,20))
        bottlesize=[375.0,750.0,1500.0,3000.0][randint(0,3)]
        
        price=wineprice(rating,age)
        price*=(bottlesize/750)
        price*=(random( )*0.9+0.2)
        # Add some noise 
        price*=(random( )*0.4+0.8)
        rows.append({'input':(rating,age,aisle,bottlesize),
                      'result':price})
    return rows  

def wineset3():
    rows=wineset()
    for row in rows:
        # Wine was bought at a discount store
        if random()<0.5:
            row['result']*=0.6
    return rows



def euclidence(v1,v2):
    d=0.
    for i in range(len(v1)):
        d+=(v1[i]-v2[i])**2
    return math.sqrt(d)

def getdistance(data,vec1):
    distancelist=[]
    for i in range(len(data)):
        vec2=data[i]['input']
        distancelist.append((euclidence(vec1,vec2),i))
    distancelist.sort()
    return distancelist

def knnestimate(data,vec1,k=3):
    # Get sorted distances
    dlist=getdistance(data,vec1)
    avg=0.
    # Take the average of the top k results
    for i in range(k):
        idx=dlist[i][1]
        avg+=data[idx]['result']
    avg=avg/k
    return avg

def inverseweight(dist,num=1.0,const=0.1):
    return num/(dist+const)

def subtractweight(dist,const=1.0):
    if dist>const:
        return 0
    else:
        return const-dist
    
def gaussian(dist,sigma=10.0):
    return math.e**(-dist**2/(2*sigma**2))

def weightedknn(data,vec1,k=5,weightf=gaussian):
    # Get sorted distances
    dlist=getdistance(data,vec1)
    avg=0.
    totalweight=0.
    # Take the average of the top k results
    for i in range(k):
        idx=dlist[i][1]
        weight=weightf(dlist[i][0])
        avg+=weight*data[idx]['result']
        totalweight+=weight
    avg=avg/totalweight
    return avg

def dividedata(data,test=0.05):
    trainset=[]
    testset=[]
    for row in data:
        if random()<test:
            testset.append(row)
        else:
            trainset.append(row)
    return trainset,testset
def testalgorithm(algf,trainset,testset):
    error=0.
    for row in testset:
        guess=algf(trainset,row['input'])
        error+=(row['result']-guess)**2
    return error/len(testset)

def crossvalidate(algf,data,trial=100,test=0.05):
    error=0.
    for i in range(trial):
        trainset,testset=dividedata(data,test)
        error+=testalgorithm(algf,trainset,testset)
    return error/trial

def rescale(data,scale):
    scaleddata=[]
    for row in data:
        scaled = [scale[i]*row['input'][i] for i in range(len(scale))]
        scaleddata.append({'input':scaled,
                           'result':row['result']})
    return scaleddata

def createcostfunction(algf,data):
    def costf(scale):
        sdata = rescale(data,scale)
        return crossvalidate(algf,sdata,trial=10)
    return costf

def probguess(data,vec,low,high,k=5,weightf=gaussian):
    nweight=0.
    tweight=0.
    
    dlist=getdistance(data,vec)
    for i in range(k):
        dist=dlist[i][0]
        idx=dlist[i][1]
        weight=weightf(dist)
        v=data[idx]['result']
        if v>low and v<high:
            nweight+=weight
        tweight+=weight
    if tweight==0:
        return 0
    # The probability is the weights in the range divided by all the weights
    return nweight/tweight


def cumulativegraph(data,vec,high,k=5,weightf=gaussian):
    t1=arange(0.0,high,0.1)
    cprob=array([probguess(data,vec,0,v,k,weightf) for v in t1])
    plot(t1,cprob)
    show( )
    
def probabilitygraph(data,vec,high,k=5,weightf=gaussian,ss=5.0):
    # Make a range for the prices
    t1=arange(0.0,high,0.1)
    probs=[probguess(data,vec,v,v+0.1,k,weightf) for v in t1]
    # Smooth them by adding the gaussian of the nearby probabilites
    smoothed=[]
    for i in range(len(probs)):
        sv=0.
        for j in range(len(probs)):
            dist=abs(i-j)*0.1
            weight=gaussian(dist,ss)
            sv+=weight*probs[j]
        smoothed.append(sv)
    plot(t1,smoothed)
    show()
        
if __name__=='__main__':
    #data = wineset()
    #data = wineset2()
    data = wineset3()
    cumulativegraph(data, (99, 20), 120)
    probabilitygraph(data, (99, 20), 120,ss=8.)
    
    