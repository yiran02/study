from math import tanh
import pymysql

def dtanh(y):
    return 1.0-y*y
class searchnet:
    def __init__(self,dbname):
        self.con = pymysql.connect(host="*****",port=3306,user="*****",password="*****",
                                  database=dbname,charset="utf8",use_unicode=True)
        self.cur = self.con.cursor()
    def __del__(self):
        self.con.close()
        
    def maketables(self):
        self.cur.execute("create table hiddennode(rowid int not null primary key auto_increment,create_key char(50))")
        self.cur.execute("create table wordhidden(rowid int not null primary key auto_increment,fromid int,toid int,strength float)")
        self.cur.execute("create table hiddenurl(rowid int not null primary key auto_increment,fromid int,toid int,strength float)")
        self.con.commit()
    
    def getstrength(self,fromid,toid,layer):
        if layer == 0:
            table='wordhidden'
        else:
            table='hiddenurl'
        self.cur.execute("select strength from %s where fromid=%d and toid=%d"%(table,fromid,toid))
        res=self.cur.fetchone()
        if res==None:
            if layer==0:
                return -0.2
            if layer==1:
                return 0
        return res[0]
    
    def setstrength(self,fromid,toid,layer,strength):
        if layer == 0:
            table='wordhidden'
        else:
            table='hiddenurl'
        self.cur.execute("select rowid from %s where fromid=%d and toid=%d"%(table,fromid,toid))
        res=self.cur.fetchone()
        if res==None:
            self.cur.execute("insert into %s (fromid,toid,strength) values(%d,%d,%f)"%(table,fromid,toid,strength))
        else:
            rowid=res[0]
            self.cur.execute("update %s set strength=%f where rowid=%d"%(table,strength,rowid))
    
    def generatehiddennode(self,wordids,urls):
        if len(wordids)>3:
            return None
        createkey = '_'.join(sorted([str(wi) for wi in wordids]))
        self.cur.execute("select rowid from hiddennode where create_key='%s' "%createkey)
        res=self.cur.fetchone()
        #if not ,create it
        if res == None:
            self.cur.execute("insert into hiddennode (create_key) values ('%s')"%createkey)
            hiddenid = self.cur.lastrowid
            for wordid in wordids:
                self.setstrength(wordid,hiddenid,0,1.0/len(wordids))
            for urlid in urls:
                self.setstrength(hiddenid,urlid,1,0.1)
            self.con.commit()
            
    def getallhiddenids(self,wordids,urlids):
        l1={}
        for wordid in wordids:
            self.cur.execute("select toid from wordhidden where fromid=%d"%wordid)
            res=self.cur.fetchall()
            for row in res:
                l1[row[0]]=1
        for urlid in urlids:
            self.cur.execute("select fromid from hiddenurl where toid=%d"%urlid)
            res=self.cur.fetchall()
            for row in res:
                l1[row[0]]=1
        return list(l1.keys())
    
    def setupnetwork(self,wordids,urlids):
        # value lists
        self.wordids=wordids
        self.urlids=urlids
        self.hiddenids=self.getallhiddenids(wordids,urlids)
         # node outputs
        self.ai = [1.0]*len(self.wordids)
        self.ah = [1.0]*len(self.hiddenids)
        self.ao = [1.0]*len(self.urlids)
         # create weights matrix
        self.wi = [[self.getstrength(wordid,hiddenid,0) for hiddenid in self.hiddenids] for wordid in self.wordids]
        self.wo = [[self.getstrength(hiddenid,urlid,1) for urlid in self.urlids] for hiddenid in self.hiddenids]
        
    def feedforward(self):
        # the only inputs are the query words
        for i in range(len(self.wordids)):
            self.ai[i]=1.0
        # hidden activations
        for j in range(len(self.hiddenids)):
            sum_=0.0
            for i in range(len(self.wordids)):
                sum_=sum_+self.ai[i]*self.wi[i][j]
            self.ah[j]=tanh(sum_)
       # output activations
        for k in range(len(self.urlids)):
            sum_=0.0
            for j in range(len(self.hiddenids)):
                sum_=sum_+self.ah[j]*self.wo[j][k]
            self.ao[k]=tanh(sum_)
        return self.ao[:]
    
    def getresult(self,wordids,urlids):
        self.setupnetwork(wordids,urlids)
        return self.feedforward()
    
    def backPropagate(self, targets, N=0.5):
        # calculate errors for output
        output_deltas = [0.0]*len(self.urlids)
        for i in range(len(self.urlids)):
            error = targets[i]-self.ao[i]
            output_deltas[i]=error*dtanh(self.ao[i])
        # calculate errors for output
        hidden_deltas = [0.0]*len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error=0.0
            for k in range(len(self.urlids)):
                error = error+output_deltas[k]*self.wo[j][k]
            hidden_deltas[j]=error*dtanh(self.ah[j])
    
        # update output weights
        for i in range(len(self.hiddenids)):
            for j in range(len(self.urlids)):
                change = output_deltas[j]*self.ah[i]
                self.wo[i][j]=self.wo[i][j]+N*change
        # update input weights
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change = hidden_deltas[j]*self.ai[i]
                self.wi[i][j]=self.wi[i][j]+N*change 
                
    def trainquery(self,wordids,urlids,selectedurl):
        # generate a hidden node if necessary
        self.generatehiddennode(wordids,urlids)
        self.setupnetwork(wordids,urlids)
        self.feedforward()
        targets=[0.0]*len(urlids)
        targets[urlids.index(selectedurl)]=1.0
        error = self.backPropagate(targets)
        self.updatedatabase()
    
    def updatedatabase(self):
          # set them to database values
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                self.setstrength(self.wordids[i],self.hiddenids[j],0,self.wi[i][j])
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                self.setstrength(self.hiddenids[j],self.urlids[k],1,self.wo[j][k])
        self.con.commit( )
        