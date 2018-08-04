import feedparser
import re

def getwordcounts(url):
    d = feedparser.parse(url)
    wc={}
    for e in d.entries:
        if 'summary' in e:
            summary=e.summary
        else:
            summary=e.description
        words=getwords(e.title+''+e.summary)
        for word in words:
            wc.setdefault(word,0)
            wc[word]+=1
    return (d.feed.title,wc)

def getwords(html):
    txt=re.compile(r'<[^>]+>').sub('',html)
    
    words=re.compile(r'[^A-Z^a-z]+').split(txt)
    
    return [word.lower() for word in words if word!='']

apcount={}#出现某单词的博客数目
wordcounts={}
with open('./Downloads/Programming-Collective-Intelligence-master/chapter3/feedlist.txt') as f:
    feedlist = [line for line in f]
for feedurl in feedlist:    
    try:
        (title, wc) = getwordcounts(feedurl)
        wordcounts[title] = wc
        for (word, count) in wc.items():
            apcount.setdefault(word, 0)
            if count > 1:
                apcount[word] += 1#一条url里的文章单词，如果单词词频大于1，才能算占用一条博客，不然词频<=1，不算占用一条博客
    except:
        print('Failed to parse feed %s' % feedurl)
        
#generate wordlist,filt  words with too high frequency or too low frequency
wordlist=[]
for w,fre in apcount.items():
    frac = fre/len(feedlist)
    if frac>0.1 and frac<0.5:
        wordlist.append(w)        
        
#generate a matrix ,every row is a blog,every column is the word count
with open('blogdata.txt','w') as fw:
    fw.write('Blog')
    for word in wordlist:
        fw.write('\t%s'%word)
    fw.write('\n')
    for blog,wc in wordcounts.items():
        fw.write(blog)
        for word in wordlist:
            if word in wc:
                fw.write('\t%d'%wc[word])
            else:
                fw.write('\t0')
        fw.write('\n')    
        
#-------------------------load in data-----------------------------------
def readfile(filename):
    with open(filename) as f:
        lines=[line for line in f]
    colnames=lines[0].strip().split('\t')[1:]
    rownames=[]
    data=[]
    for line in lines[1:]:
        p=line.strip().split('\t')
        rownames.append(p[0])
        data.append([float(i) for i in p[1:]])
    return rownames,colnames,data



#define distance for two item,use pearson here
from math import sqrt
def pearson(v1,v2):
    sum1 = sum(v1)
    sum2 = sum(v2)
    #sum of products 
    psum = sum([v1[i]*v2[i] for i in range(len(v1))])
    #sum of squares
    sumsq1 = sum([pow(i,2) for i in v1])
    sumsq2 = sum([pow(i,2) for i in v2])
    n=len(v1)
    num = psum-sum1*sum2/n
    den = sqrt((sumsq1-pow(sum1,2)/n)*(sumsq2-pow(sum2,2)/n))
    if den == 0:
        return 0
    
    return 1.-num/den


class bicluster:#每个博客作为一个对象
    def __init__(self,vec,left=None,right=None,distance=0.,id_=None):
        self.vec=vec
        self.left=left
        self.right=right
        self.distance=distance
        self.id_=id_
def hcluster(rows,distance=pearson):
    distances={}
    
    currentclustid=-1
    #clusters anr initially just the rows
    clust=[bicluster(rows[i],id_=i) for i in range(len(rows))]
    while len(clust)>1:
        lowestpair=(0,1)
        closest=distance(clust[0].vec,clust[1].vec)
        
        for i in range(0,len(clust)):
            for j in range(i+1,len(clust)):
                if (clust[i].id_,clust[j].id_) not in distances:
                    distances[(clust[i].id_,clust[j].id_)]=distance(clust[i].vec,clust[j].vec)
                    
                d = distances[(clust[i].id_,clust[j].id_)]
                
                if d<closest:
                    closest=d
                    lowestpair=(i,j)
        #caculate average of the new cluster
        mergevec = [(clust[lowestpair[0]].vec[i]+clust[lowestpair[1]].vec[i])/2 for i in range(len(clust[0].vec))]
        #create new clust
        newcluster = bicluster(mergevec,left=clust[lowestpair[0]],right=clust[lowestpair[1]],distance=closest,id_=currentclustid)
        #clust id weren't in original set were negative
        currentclustid-=1
        del clust[lowestpair[1]]
        del clust[lowestpair[0]]
        clust.append(newcluster)
    return clust[0]

def printclust(clust,labels=None,n=0):
    for i in range(n):
        print(' ',end=" ")
    if clust.id_<0:
        print('-')
    else:    
        if labels==None:
            print(clust.id_)
        else:
            print(labels[clust.id_])
    if clust.left!=None:
        printclust(clust.left,labels=labels,n=n+1)
    if clust.right!=None:
        printclust(clust.right,labels=labels,n=n+1)
        
        
from PIL import Image,ImageDraw

def getheight(clust):
    #the height for endpoint is just 1
    if clust.left == None and clust.right == None:
        return 1
    return getheight(clust.left) + getheight(clust.right)

def getdepth(clust):
    if clust.left == None and clust.right == None:
        return 0.0
    return max(getdepth(clust.left),getdepth(clust.right))+clust.distance

def drawdendrogram(clust,labels,jpeg='clusters.jpg'):
    h=getheight(clust)*20
    w=1200
    d=getdepth(clust)
    #节点缩放
    scaling=float(w-150)/d
    
    
    img=Image.new('RGB',(w,h),(220,220,220))
    draw=ImageDraw.Draw(img)
    
    draw.line((1,h/2,10,h/2),fill=(255,0,0))
    
    drawnode(draw,clust,10,h/2,scaling,labels)
    img.save(jpeg,'JPEG')
    
def drawnode(draw,clust,x,y,scaling,labels):
    if clust.id_<0:
        h1=getheight(clust.left)*20
        h2=getheight(clust.right)*20
        top=y-(h1+h2)/2
        bottom=y+(h1+h2)/2
        # line length
        ll=scaling*clust.distance
        #vertical line
        draw.line((x,top+h1/2,x,bottom-h2/2),fill=(255,0,0))
        #horizontal line
        draw.line((x,top+h1/2,x+ll,top+h1/2),fill=(0,0,255))
        draw.line((x,bottom-h2/2,x+ll,bottom-h2/2),fill=(255,255,0))
        
        drawnode(draw,clust.left,x+ll,top+h1/2,scaling,labels)
        drawnode(draw,clust.right,x+ll,bottom-h2/2,scaling,labels)
    else:    
        draw.text((x+5,y-1),labels[clust.id_],(0,0,0))
        

#列聚类        
def rotatematrix(data):
    newdata=[]
    for j in range(len(data[0])):
        newrow = [data[j][i] for j in range(len(data))]
        newdata.append(newrow)
    return newdata



import random
#k均值聚类
def kcluster(rows,distance=pearson,k=4):
    ranges = [(min([row[i] for row in rows]),max([row[i] for row in rows])) for i in range(len(rows[0]))]
    # k  random centroids
    cluster = [[random.random()*(ranges[i][1]-ranges[i][0])+ranges[i][0] for i in range(len(rows[0]))] for j in range(k)]
    
    lastmatches = None
    for i in range(100):
        print('Interation %d'%i)
        bestmatches = [[] for t in range(k)]
        #find which centroid is the closest to each row
        for j in range(len(rows)):
            row = rows[j]
            bestmatch = 0
            for i in range(k):
                d = distance(cluster[i],row) #计算初始中心点与每一行的距离
                if d<distance(cluster[bestmatch],row):
                    bestmatch = i
            bestmatches[bestmatch].append(j)   #聚类行号
        if bestmatches == lastmatches: #如果与最后一次的聚类相同，跳出迭代
            break
        lastmatches = bestmatches
        # move centroids to average of members
        for m in range(k):
            avgs=[0.0]*len(rows[0])
            if len(bestmatches[m])>1:
                for rowid in range(len(bestmatches[m])):
                    for l in range(len(rows[rowid])):
                        avgs[l]+=rows[rowid][l]
                for j in range(len(avgs)):
                    avgs[j]/=len(bestmatches[m])
                cluster.append(avgs)
    return bestmatches

#----------------------------华丽的分界线---------------------------------
def tanimoto(v1,v2):
    c1,c2,shr=0,0,0
    for i in range(len(v1)):
        if v1[i]!=0:
            c1+=1
        if v2[i]!=0:
            c2+=1
        if v1[i]!=0 and v2[i]!=0:
            shr+=1
    return 1.- (float(shr)/(c1+c2-shr))
#多维缩放
def scaledown(data,distance=pearson,rate=0.01):
    n=len(data)
    realdis = [[distance(data[i],data[j]) for j in range(n)] for i in range(0,n)]
    outsum=0
    loc = [[random.random(),random.random()] for i in range(n)]
    fakedis = [[0.0 for j in range(n)] for i in range(n)]
    lasterror=None
    
    for m in range(1000):
        #project distance
        for i in range(n):
            for j in range(n):
                fakedis[i][j]=sqrt(sum([pow(loc[i][x]-loc[j][x],2) for x in range(len(loc[i]))])) 
        #move points
        grad = [[0.0,0.0] for i in range(n)]
        totalerror=0
        for k in range(n):
            for j in range(n):
                if k == j:
                    continue
                errorterm=(fakedis[j][k]-realdis[j][k])/realdis[j][k]
                grad[k][0]+=((loc[k][0]-loc[j][0])/fakedis[j][k])*errorterm
                grad[k][1]+=((loc[k][1]-loc[j][1])/fakedis[j][k])*errorterm
                totalerror+=abs(errorterm)
        print(totalerror)
        if lasterror and totalerror>lasterror:
            break
        lasterror=totalerror
        
        for k in range(n):
            loc[k][0]-=rate*grad[k][0]
            loc[k][1]-=rate*grad[k][1]
    return loc

def draw2d(data,labels,jpeg='mds2d.jpg'):
    img=Image.new('RGB',(2000,2000),(255,255,255))
    draw=ImageDraw.Draw(img)
    for i in range(len(data)):
        x=(data[i][0]+0.5)*1000
        y=(data[i][1]+0.5)*1000
        draw.text((x,y),labels[i],(0,0,0))
    img.save(jpeg,'JPEG')
