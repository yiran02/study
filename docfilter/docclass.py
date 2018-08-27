import re
import math
import pymysql

def getwords(doc):
    splitter = re.compile('\W*')
    # Split the words by non-alpha characters
    words = [p.lower() for p in splitter.split(doc) if len(p)>2 and len(p)<20]
    return dict([(w,1) for w in words])

class classifier:
    def __init__(self,getfeatures,filename=None):
        #counts of features/category combinations
        #self.fc={}
        #counts of documents in each category
        #self.cc={}
        self.getfeatures=getfeatures
    
    def setdb(self,dbfile):
        self.con = pymysql.connect(host="*****",port=3306,user="*****",password="*****",
                      database=dbfile,charset="utf8",use_unicode=True)
        self.cur = self.con.cursor()
        self.cur.execute("create table if not exists fc (feature char(100),category char(10),count int)")
        self.cur.execute("create table if not exists cc (category char(10),count int)")
        
    #increase the count of a feature/category pair
    def incf(self,f,cat):
        '''
        self.fc.setdefault(f,{})
        self.fc[f].setdefault(cat,0)
        self.fc[f][cat]+=1
        '''
        count = self.fcount(f,cat)
        if count == 0:
            self.cur.execute("insert into fc (feature,category,count) values('%s','%s',1)"%(f,cat))
        else:
            self.cur.execute("update fc set count=%d where feature='%s' and category='%s'"%(count+1,f,cat))
    
    
    #increase the count of category
    def incc(self,cat):
        '''
        self.cc.setdefault(cat,0)
        self.cc[cat]+=1
        '''
        count = self.catcount(cat)
        if count == 0:
            self.cur.execute("insert into cc (category,count) values('%s',1)"%(cat))
        else:
            self.cur.execute("update cc set count=%d where category='%s'"%(count+1,cat))
    
    #the number of a feature appears in a category
    def fcount(self,f,cat):
        '''
        if f in self.fc and cat in self.fc[f]:
            return self.fc[f][cat]
        return 0
        '''
        self.cur.execute("select count from fc where feature='%s' and category='%s'"%(f,cat))
        res = self.cur.fetchone()
        if res == None:
            return 0
        return float(res[0])
    
    #items in a category
    def catcount(self,cat):
        '''
        if cat in self.cc:
            return self.cc[cat]
        return 0
        '''
        self.cur.execute("select count from cc where category='%s'"%(cat))
        res = self.cur.fetchone()
        if res == None:
            return 0
        return float(res[0])
    
    #total items
    def totalcount(self):
        #return sum(self.cc.values())
        self.cur.execute("select sum(count) from cc")
        res = self.cur.fetchone()
        if res == None:
            return 0
        return float(res[0])
    
    #category list
    def categories(self):
        #return self.cc.keys()
        self.cur.execute("select category from cc")
        res = self.cur.fetchall()
        return [l[0] for l in res]
    
    def train(self,item,cat):
        features = self.getfeatures(item)
        # Increment the count for every feature with this category
        for f in features:
            self.incf(f,cat)
        # Increment the count for this category
        self.incc(cat)
        self.con.commit()
        
    def fprob(self,f,cat):
        if self.catcount(cat) == 0:
            return 0
        # The total number of times this feature appeared in this
         # category divided by the total number of items in this category
        return self.fcount(f,cat)/self.catcount(cat)
    
    def weightedprob(self,f,cat,prf,weight=1.0,ap=0.5):
        basicprob = prf(f,cat)
        total = sum([self.fcount(f,c) for c in self.categories()])
        bp = (weight*ap+total*basicprob)/(weight+total)
        return bp
    
    
def sampletrain(cl):
    cl.train('Nobody owns the water.','good')
    cl.train('the quick rabbit jumps fences','good')
    cl.train('buy pharmaceuticals now','bad')
    cl.train('make quick money at the online casino','bad')
    cl.train('the quick brown fox jumps','good')
    
class naivebayes(classifier):# naivebayes 继承 classifier
    def __init__(self,getfeatures):
        classifier.__init__(self,getfeatures)# 子类对父类的构造方法的调用
        self.thresholds={}
        
    def docprob(self,item,cat):
        features = self.getfeatures(item)
        p=1
        # Multiply the probabilities of all the features together
        for f in features:
            p*=self.weightedprob(f,cat,self.fprob)
        return p
    def prob(self,item,cat):
        catprob = self.catcount(cat)/self.totalcount()
        docprob = self.docprob(item,cat)
        return catprob*docprob
    
    def setthreshold(self,cat,t):
        self.thresholds[cat]=t
        
    def getthreshold(self,cat):
        if cat not in self.thresholds:
            return 1.
        return self.thresholds[cat]
    
    def classify(self,item,default=None):
        probs={}
        # Find the category with the highest probability
        max_=0.
        for cat in self.categories():
            probs[cat]=self.prob(item,cat)
            if probs[cat]>max_:
                max_=probs[cat]
                best=cat
        # Make sure the probability exceeds threshold*next best
        for cat in probs:
            if cat == best:
                continue
            if self.getthreshold(best)*probs[cat]>probs[best]:
                return default
        return best
    
class fisherclassifier(classifier):
    def __init__(self,getfeatures):
        classifier.__init__(self,getfeatures)
        self.minimums={}
        
    def cprob(self,f,cat):
        # The frequency of this feature in this category
        clf = self.fcount(f,cat)
        if clf == 0:
            return 0
        # The frequency of this feature in all the categories
        freqsum = sum([self.fcount(f,c) for c in self.categories()])
        # The probability is the frequency in this category divided by
        # the overall frequency
        p = clf/freqsum
        return p
    def fisherprob(self,item,cat):
        p = 1
        features = self.getfeatures(item)
        #muntiply all the probabilities together
        for f in features:
            p*=self.weightedprob(f,cat,self.cprob)
        # Take the natural log and multiply by -2
        fscores=-2*math.log(p)
        # Use the inverse chi2 function to get a probability
        return self.invchi2(fscores,2*len(features))
    def invchi2(self,chi,df):
        m = chi/2.
        sum_ = term = math.exp(-m)
        for i in range(1,df//2):
            term *= m/i
            sum_+=term
        return min(sum_,1.)
    
    def setminimums(self,cat,min_):
        self.minimums[cat]=min_
    
    def getminimums(self,cat):
        if cat not in self.minimums:
            return 0
        return self.minimums[cat]
    
    def classify(self,item,default=None):
        # Loop through looking for the best result
        best = default
        max_=0
        for c in self.categories():
            p = self.fisherprob(item,c)
            # Make sure it exceeds its minimum
            if p > self.getminimums(c) and p > max_:
                best=c
                max_=p
        return best
    
    
if __name__=='__main__':

    cl = fisherclassifier(getwords)
    cl.setdb('test')
    sampletrain(cl)
    cl2=naivebayes(getwords)
    cl2.setdb('test')
    cl2.classify('quick money')
