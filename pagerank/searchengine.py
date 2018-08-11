from urllib.request import urlopen,urljoin
from bs4 import BeautifulSoup
import pymysql
import re
import jieba
import time
import nn
mynet=nn.searchnet('test')

class crawler:
    # Initialize the crawler with the name of database
    def __init__(self,dbname):
        self.con = pymysql.connect(host="*****",port=3306,user="*****",password="*****",
                      database=dbname,charset="utf8",use_unicode=True)
        self.cur = self.con.cursor()
        
    
    
    
    
    def __del__(self):
        #self.cur.close()
        self.con.close()
        
    def dbcommit(self):
        self.con.commit()
    #return the ID of an entry      
    def getentryid(self,table,field,value,cteatenew=True):
        self.cur.execute("select rowid from %s where %s='%s'"%(table,field,value))
        res = self.cur.fetchone()
        if res == None:
            self.cur.execute("insert into %s (%s) values('%s')"%(table,field,value))
            return self.cur.lastrowid#最后插入的一条记录的id
        else:
            return res[0]
    
    #index an individual page
    def addtoindex(self,url,soup):
        if self.isindexed(url):
            return print("Indexing %s"%url)
        text = self.gettextonly(soup)
        words = self.seperateword(text)
        
        urlid = self.getentryid('urllist','url',url)
        for i,word in enumerate(words):
            
            wordid = self.getentryid('wordlist','word',word)
            self.cur.execute('insert into wordlocation (urlid,wordid,location) values(%d,%d,%d)'%(urlid,wordid,i))
            
        
        #extract the text from an html page
    def gettextonly(self,soup):
        '''
        v=soup.string
        if v==None:
            c=soup.contents
            resulttext=''
            for t in c:
                subtext=self.gettextonly(t)
                resulttext+=subtext+'\n'
            return resulttext
        else:
            return v.strip()
        '''    
        
        pat = re.compile(u'[\u4e00-\u9fa5]+')  
        resultext = ' '.join(re.findall(pat,soup.text))
        return resultext
    
    #seperate the words by any non-whitespace character
    def seperateword(self,content):
        '''
        splitter=re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s!='']
        '''
        # use jibeba engine to splits chinese articles

        time0 = time.time()
        words = jieba.cut(content,cut_all=False)
        print ("elapse splits words: {}".format(time.time()-time0))
        
        return (word.strip() for word in words if len(word.strip())>1) # iterator
    
    def isindexed(self,url):
        self.cur.execute("select rowid from urllist where url='%s'" % url)
        u = self.cur.fetchone()
        if u!=None:
        # Check if it has actually been crawled
            self.cur.execute('select * from wordlocation where urlid=%d' % u[0])
            v = self.cur.fetchone() 
            if v!=None: 
                return True
        return False
    
    def addlinkref(self,urlFrom,urlTo,linkText):
        words=self.seperateword(linkText)
        fromid=self.getentryid('urllist','url',urlFrom)
        toid=self.getentryid('urllist','url',urlTo)
        if fromid==toid: 
            return
        self.cur.execute("insert into link (fromid,toid) values (%d,%d)" % (fromid,toid))
        linkid=self.cur.lastrowid
        for word in words:
            if word in ignorewords: 
                continue
            wordid=self.getentryid('wordlist','word',word)
            self.cur.execute("insert into linkwords (linkid,wordid) values (%d,%d)" % (linkid,wordid))
    
    def crawl(self,pages,depth=2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    html = urlopen(page).read().decode('utf-8')
                except:
                    print("can't open this page:%s!"%page)
                    continue
                soup = BeautifulSoup(html,'lxml')
                
                self.addtoindex(page,soup)
                links = soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url = urljoin(page,link['href'])
                        if url.find("'")!=-1:
                            continue
                        url = url.split('#')[0]#remove location portion
                        if url[0:4]=='http' and not self.isindexed(url):
                            newpages.add(url)
                        linkText = self.gettextonly(soup)
                        self.addlinkref(page,url,linkText)
                self.dbcommit()
                    #print("can't parse page:%s"%page)
            pages=newpages
            
                        
    def createindextables(self):
        self.cur.execute('create table urllist (rowid INT NOT NULL AUTO_INCREMENT,url VARCHAR(1000),PRIMARY KEY(rowid))')
        self.cur.execute('create table wordlist(rowid INT NOT NULL AUTO_INCREMENT,word CHAR(100),PRIMARY KEY(rowid))')
        self.cur.execute('create table wordlocation(rowid INT NOT NULL AUTO_INCREMENT,urlid INT,wordid INT,location INT,PRIMARY KEY(rowid))')
        self.cur.execute('create table link(rowid INT NOT NULL AUTO_INCREMENT,fromid INT,toid INT,PRIMARY KEY(rowid))')
        self.cur.execute('create table linkwords(rowid INT NOT NULL AUTO_INCREMENT,wordid INT,linkid INT,PRIMARY KEY(rowid))')
        self.cur.execute('create index wordidx on wordlist(word)')
        self.cur.execute('create index urlidx on urllist(url)')
        self.cur.execute('create index wordurlidx on wordlocation(wordid)')
        self.cur.execute('create index urltoidx on link(toid)') 
        self.cur.execute('create index urlfromidx on link(fromid)') 
        self.dbcommit( )
        
    def caculatepagerank(self,interation=20):
        self.cur.execute("drop table if exists pagerank")
        self.cur.execute("create table pagerank (urlid int primary key,score float)")
        # initialize every url with a PageRank of 1
        self.cur.execute("insert into pagerank select rowid,1.0 from urllist")
        self.dbcommit()
        for i in range(interation):
            print("Interation %d"%i)
            self.cur.execute("select rowid from urllist")
            for (urlid,) in self.cur.fetchall():
                pr=0.15
                # Loop through all the pages that link to this one
                self.cur.execute("select distinct fromid from link where toid=%d"%urlid)
                for (linker,) in self.cur.fetchall():
                    self.cur.execute("select score from pagerank where urlid=%d"%linker)
                    linkingpr = self.cur.fetchone()[0]
                    # Get the total number of links from the linker
                    self.cur.execute("select count(*) from link where fromid=%d"%linker)
                    linkingcount = self.cur.fetchone()[0]
                    pr+=0.85*(linkingpr/linkingcount)
                self.cur.execute("update pagerank set score=%f where urlid=%d"%(pr,urlid))
            self.dbcommit()
                    
            
        
        
        
ignorewords=set(['的','了'])     




class searcher:
    def __init__(self,dbname):
        self.con = pymysql.connect(host="*****",port=3306,user="******",password="******",
                                  database=dbname,charset="utf8",use_unicode=True)
        self.cur = self.con.cursor()
    def __del__(self):
        self.con.close()
        
    #find each word in table wordlocation and join them on their urlid
    def getmatchrows(self,q):
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []
        
        words = q.split(' ')
        tablenumber = 0
        
        for word in words:
            #get word id
            self.cur.execute("select rowid from wordlist where word = '%s'"%word)
            wordrow = self.cur.fetchone()
            if wordrow!=None:
                wordid = wordrow[0]
                wordids.append(wordid)
                if tablenumber>0:
                    tablelist+=','
                    clauselist+=' and '
                    clauselist+='w%d.urlid = w%d.urlid and '%(tablenumber-1,tablenumber)
                fieldlist+=',w%d.location'%tablenumber
                tablelist+='wordlocation w%d'%tablenumber
                clauselist+='w%d.wordid = %d'%(tablenumber,wordid)
                tablenumber+=1
        self.cur.execute("select %s from %s where %s"%(fieldlist,tablelist,clauselist))
        rows = self.cur.fetchall()
        rows = [row for row in rows]
        return rows,wordids
    
    def getscoredlist(self,rows,wordids):
        totalscores = dict([(row[0],0) for row in rows]) #urlid and scores
        
        weights = [(1.0,self.frequencyscore(rows)),
                  (1.0,self.locationscore(rows)),
                  (1.0,self.pagerankscore(rows)),
                  (1.0,self.linktextscore(rows,wordids)),
                  (5.0,self.nnscore(rows,wordids))]
        
        
        for (weight,scores) in weights:
            for url in totalscores:
                totalscores[url]+=weight*scores[url]
        return totalscores
    
    def geturlnames(self,id):
        self.cur.execute("select url from urllist where rowid='%d'"%id)
        res = self.cur.fetchone()
        return res[0]
    
    def query(self,q):
        rows,wordids = self.getmatchrows(q)
        scores = self.getscoredlist(rows,wordids)
        rankedscores = sorted([(score,url) for url,score in scores.items()],reverse=1)
        for score,urlid in rankedscores[0:10]:
            print("%f\t%s"%(score,self.geturlnames(urlid)))
        return wordids,[r[1] for r in rankedscores[0:10]]
    
    #Each score is scaled according to how close it is to the best result
    def normalizescores(self,scores,smallIsBetter=0):
        vsmall = 0.00001  #  Avoid division by zero errors
        if smallIsBetter:
            minscore = min(scores.values())
            return dict([(u,float(minscore)/max(vsmall,l)) for u,l in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u,float(c)/maxscore) for u,c in scores.items()])
        
    #The word frequency metric scores a page based on how many times the words in the query appear on that page.
    def frequencyscore(self,rows):
        counts = dict([(row[0],0) for row in rows])
        for row in rows:
            counts[row[0]]+=1
        return self.normalizescores(counts)
    
    #the search engine can score results higher if the query term appears early in the document. 
    def locationscore(self,rows):
        locations = dict([(row[0],1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:]) #sum of word location
            if loc<locations[row[0]]:
                locations[row[0]]=loc
        return self.normalizescores(locations,smallIsBetter=1)
    
    def distancescore(self,rows):
         # If there's only one word, everyone wins!
        if len(row[0])<=2:
            return dict([(row[0],1.0) for row in rows])
        # Initialize the dictionary with large values
        mindistance=dict([(row[0],1000000) for row in rows])
        for row in rows:
            #it takes the difference between each location and the previ- ous location
            dist=sum([abs(row[i]-row[i-1]) for i in range(2,len(row))])
            if dist<mindistance[row[0]]:
                mindistance[row[0]]=dist
        return self.normalizescores(mindistance,smallIsBetter=1)
    
    #return all the pages containing the search terms, ranked solely on how many inbound links they have
    def inboundlinkscore(self,rows):
        uniqueurls = set([row[0] for row in rows])
        inboundcounts={}
        for u in uniqueurls:
            self.cur.execute("select count(*) from link where toid = %d" %u)
            res = self.cur.fetchone()
            inboundcounts[u] = res[0]
        return self.normalizescores(inboundcounts)
    
    #The importance of the page is calculated from the importance of all the other pages that link to it 
    #and from the number of links each of the other pages has.
    def pagerankscore(self,rows):
        pageranks={}
        for row in rows:
            self.cur.execute("select score from pagerank where urlid=%d"%row[0])
            pageranks[row[0]]=self.cur.fetchone()[0]
        maxrank = max(pageranks.values())
        vsmall = 0.0001
        if maxrank == 0 :
            maxrank=vsmall
        normalizescores = dict([(u,float(l)/maxrank) for (u,l) in pageranks.items()])
        return normalizescores
    
    #A page with a lot of links from important pages that contain the query terms will get a very high score
    def linktextscore(self,rows,wordids):
        linkscores = dict([(row[0],0) for row in rows])
        for wordid in wordids:
            self.cur.execute("select fromid,toid from linkwords,link where linkwords.wordid = %d and \
            linkwords.linkid = link.rowid"%wordid)
            res = self.cur.fetchall()
            for (fromid,toid) in res:
                if toid in linkscores:
                    self.cur.execute("select score from pagerank where urlid=%d"%fromid)
                    pr = self.cur.fetchone()[0]
                    linkscores[toid]+=pr
        maxscore = max(linkscores.values())
        vsmall = 0.0001
        if maxscore == 0 :
            maxscore=vsmall
        normalizescores = dict([(u,float(l)/maxscore) for (u,l) in linkscores.items()])
        return normalizescores
    
    def nnscore(self,rows,wordids):
        # Get unique URL IDs as an ordered list
        urlids=[urlid for urlid in set([row[0] for row in rows])]
        nnres=mynet.getresult(wordids,urlids)
        scores=dict([(urlids[i],nnres[i]) for i in range(len(urlids))])
        return self.normalizescores(scores)
        


