critics={'Lisa Rose': {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.5,
      'Just My Luck': 3.0, 'Superman Returns': 3.5, 'You, Me and Dupree': 2.5,
      'The Night Listener': 3.0},
     'Gene Seymour': {'Lady in the Water': 3.0, 'Snakes on a Plane': 3.5,
      'Just My Luck': 1.5, 'Superman Returns': 5.0, 'The Night Listener': 3.0,
      'You, Me and Dupree': 3.5},
     'Michael Phillips': {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.0,
      'Superman Returns': 3.5, 'The Night Listener': 4.0},
     'Claudia Puig': {'Snakes on a Plane': 3.5, 'Just My Luck': 3.0,
      'The Night Listener': 4.5, 'Superman Returns': 4.0,
      'You, Me and Dupree': 2.5},
     'Mick LaSalle': {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
      'Just My Luck': 2.0, 'Superman Returns': 3.0, 'The Night Listener': 3.0,
      'You, Me and Dupree': 2.0},
     'Jack Matthews': {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
      'The Night Listener': 3.0, 'Superman Returns': 5.0, 'You, Me and Dupree': 3.5},
     'Toby': {'Snakes on a Plane':4.5,'You, Me and Dupree':1.0,'Superman Returns':4.0}}

#pearson correlation
def sim_pearson(dic,p1,p2):
    si={}
    for item in dic[p1]:
        if item in dic[p2]:
            si[item]=1
    n = len(si)
    if n==0:
        return 0
    sum1=sum([dic[p1][it] for it in si])
    sum2=sum([dic[p2][it] for it in si])
    
    psum=sum([dic[p1][it]*dic[p2][it] for it in si])
    
    sq_sum1=sum([pow(dic[p1][it],2) for it in si])
    sq_sum2=sum([pow(dic[p2][it],2) for it in si])
    
    num=psum-sum1*sum2/n
    den=sqrt((sq_sum1-pow(sum1,2)/n)*(sq_sum2-pow(sum2,2)/n))
    if den == 0:
        return 0
    return num/den

from math import sqrt
def _toMatch(dic,person,n=5,similarity=sim_pearson):
    scores = [(similarity(dic,person,other),other) for other in dic if other!=person]
    scores.sort()
    scores.reverse()
    return scores[0:n]

def getrecommendations(dic,person,similarity=sim_pearson):
    totals={}
    simsum={}
    for other in dic:
        if other == person:
            continue
        sim = similarity(dic,person,other)
        if sim<=0:
            continue
        for item in dic[other]:
            if item not in dic[person] or dic[person][item]==0:
                totals.setdefault(item,0)
                totals[item]+=dic[other][item]*sim
                simsum.setdefault(item,0)
                simsum[item]+=sim
    rankings=[(total/simsum[item],item) for item,total in totals.items()]
    rankings.sort()
    rankings.reverse()
    
    return rankings

#use only the top five other users to get recommendations.
def getrecommendations5(dic,person,similarity=sim_pearson):
    totals={}
    simsum={}
    for other in [_toMatch(dic,person,similarity=similarity)[i][1] for i in range(0,5)]:
        if other == person:
            continue
        sim = similarity(dic,person,other)
        if sim<=0:
            continue
        for item in dic[other]:
            if item not in dic[person] or dic[person][item]==0:
                totals.setdefault(item,0)
                totals[item]+=dic[other][item]*sim
                simsum.setdefault(item,0)
                simsum[item]+=sim
    rankings=[(total/simsum[item],item) for item,total in totals.items()]
    rankings.sort()
    rankings.reverse()
    
    return rankings

#--------------------item similarity----------------------------
def transform(dic):
    result={}
    for person in dic:
        for item in dic[person]:
            result.setdefault(item,{})
            result[item][person]=dic[person][item]
    return result
movies = transform(critics)

def caculatesimilaritems(dic,n=10):
    result={}
    itemsdic = transform(dic)
    c=0
    for item in itemsdic:
        c+=1
        if c%100==0:
            print("%d / %d"%(c,len(itemsdic)))
        #find the most similar items to this one    
        scores = _toMatch(itemsdic,item,n=n,similarity=sim_pearson)
        result[item]=scores
    return result

def getrecommendeditems(dic,itemmatch,user):
    userrating = dic[user]
    scores={}
    sim={}
    #rating for movies user have seen
    for (item,rating) in userrating.items():
        #similarity from similar datasets for the item
        for (similarity,item2) in itemmatch[item]:
            if item2  in userrating:
                continue
            scores.setdefault(item2,0)
            scores[item2]+=similarity*rating
            sim.setdefault(item2,0)
            sim[item2]+=similarity
    try:
        rankings = [(score / sim[item], item) for item, score in scores.items() if sim[item] != 0]
        # Return the rankings from highest to lowest
        rankings.sort()
        rankings.reverse()
    except ZeroDivisionError:
        rankings = None
    return rankings    

def loadmovieslen(path='./Downloads/ml-100k'):
    movies = {}
    for line in open(path+'/u.item',encoding='latin-1'):
        (id,title) = line.split('|')[0:2]
        movies[id]=title
    prefs = {}
    for line in open(path+'/u.data'):
        (user,movieid,rating,ts) = line.split('\t')
        prefs.setdefault(user,{})
        prefs[user][movies[movieid]] = float(rating)
    return prefs

def main():
    prefs = loadmovieslen()
    itemsim = caculatesimilaritems(prefs, n=50)
    rec = getrecommendeditems(prefs, itemsim, '87')[0:10]
    print(rec[0:5])


if __name__ == '__main__':
    main()