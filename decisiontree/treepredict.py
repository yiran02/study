my_data=[['slashdot','USA','yes',18,'None'],
             ['google','France','yes',23,'Premium'],
             ['digg','USA','yes',24,'Basic'],
             ['kiwitobes','France','yes',23,'Basic'],
             ['google','UK','no',21,'Premium'],
             ['(direct)','New Zealand','no',12,'None'],
             ['(direct)','UK','no',21,'Basic'],
             ['google','USA','no',24,'Premium'],
             ['slashdot','France','yes',19,'None'],
             ['digg','USA','no',18,'None'],
             ['google','UK','no',18,'None'],
             ['kiwitobes','UK','no',19,'None'],
             ['digg','New Zealand','yes',12,'Basic'],
             ['slashdot','UK','no',21,'None'],
             ['google','UK','yes',18,'Basic'],
             ['kiwitobes','France','yes',19,'Basic']]

class decisionnode:
    def __init__(self,col=-1,value=None,results=None,tb=None,fb=None):
        self.col=col
        self.value=value
        self.results=results
        self.tb=tb
        self.fb=fb
        
# Divides a set on a specific column. Can handle numeric or nominal values
def divideset(rows,column,value):
        # Make a function that tells us if a row is in
        # the first group (true) or the second group (false)
    split_function=None
    if isinstance(value,int) or isinstance(value,float):
        split_function = lambda row: row[column]>=value
    else:
        split_function = lambda row: row[column]==value
    # Divide the rows into two sets and return them
    set1 = [row for row in rows if split_function(row)]
    set2 = [row for row in rows if  not split_function(row)]
    return set1,set2 

# Create counts of possible results (the last column of  each row is the result)
def uniquecounts(rows):
    results={}
    for row in rows:
        # The result is the last column
        r = row[len(row)-1]
        if r not in results:
            results[r]=0
        results[r]+=1
    return results

# Probability that a randomly placed item will be in the wrong category
def giniimpurity(rows):
    total = len(rows)
    counts = uniquecounts(rows)
    imp = 0
    for k1 in counts:
        p1=float(counts[k1])/8
        for k2 in counts:
            if k1==k2: 
                continue
            p2=float(counts[k2])/8
            imp+=p1*p2 
    return imp

# Entropy is the sum of p(x)log(p(x)) across all the different possible results
def entropy(rows):
    results = uniquecounts(rows)
    from math import log
    log2 = lambda x:log(x)/log(2)
    ent = 0.
    for r in results.keys():
        p = float(results[r])/len(rows)
        ent-=p*log2(p)
    return ent
   
def buildtrees(rows,scoref=entropy):
    if len(rows) == 0:
        return descisionnode()
    current_score = scoref(rows)
    best_set = None
    best_criterion = None
    best_gain = 0.
    
    column_counts = len(rows[0])-1
    # Generate the list of different values in this column
    for col in range(column_counts):
        column_values = {}
        for row in rows:
            column_values[row[col]]=1
        # Now try dividing the rows up for each value  in this column
        for i in column_values.keys():
            set1,set2 = divideset(rows,col,i)
            # Information gain
            p = len(set1)/len(rows)
            gain = current_score - p*scoref(set1)-(1-p)*scoref(set2)
            if gain>best_gain and len(set1)>0 and len(set2)>0:
                best_gain=gain
                best_set=(set1,set2)
                best_criterion=(col,i)
    # Create the subbranches
    if best_gain>0:
        truebranch=buildtrees(best_set[0])
        falsebranch=buildtrees(best_set[1])
        return decisionnode(col=best_criterion[0],value=best_criterion[1],tb=truebranch,fb=falsebranch)
    return  decisionnode(results=uniquecounts(rows))

def printtree(tree,indent=' '):
    # Is this a leaf node?
    if tree.results!=None:
        print(str(tree.results))
    else:
        # Print the criteria
        print(str(tree.col)+':'+str(tree.value)+'?')
        # Print the branches
        print(indent+'T ->')
        printtree(tree.tb,indent+' ')
        print(indent+'F ->')
        printtree(tree.fb,indent+' ')

def getwidth(tree):
    if tree.tb == None and tree.fb == None:
        return 1
    return getwidth(tree.tb)+getwidth(tree.fb)+1
def getdepth(tree):
    if tree.tb == None and tree.fb == None:
        return 0
    return max(getdepth(tree.tb),getdepth(tree.fb))+1

from PIL import Image,ImageDraw
def drawtree(tree,jpeg='tree.jpeg'):
    w = getwidth(tree)*50
    h = getdepth(tree)*100+120
    
    img = Image.new('RGB',(w,h),(255,255,255))
    draw = ImageDraw.Draw(img)
    drawnode(draw,tree,2*w/3,20)
    img.save(jpeg,'JPEG')
    
def drawnode(draw,tree,x,y):
    if tree.results == None:
        # Get the width of each branch
        w1 = getwidth(tree.tb)*50
        w2 = getwidth(tree.fb)*50
        # Determine the total space required by this node
        left = x-(w1+w2)/2
        right = x+(w1+w2)/2
        
        # Draw the condition string
        draw.text((x-20,y-10),str(tree.col)+':'+str(tree.value),(139, 101, 8))
        # Draw links to the branches
        draw.line((x,y,left+w1/2,y+50),fill=(139, 69, 19))
        draw.line((x,y,right-w2/2,y+50),fill=(139, 69, 19))
        # Draw the branch nodes
        drawnode(draw,tree.fb,left+w1/2,y+50)
        drawnode(draw,tree.tb,right-w2/2,y+50)
    else:
        txt=' \n'.join(['%s:%d'%v for v in tree.results.items()]) 
        draw.text((x-20,y),txt,(122, 197, 205))

        
def classify(observation,tree):
    if tree.results != None:
        return tree.results
    else:
        v = observation[tree.col]
        branch = None
        if isinstance(v,int) or isinstance(v,float):
            if v>=tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        else:
            if v==tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        return classify(observation,branch)

def prune(tree,mingain):
     # If the branches aren't leaves, then prune them
    if tree.tb == None:
        prune(tree.tb,mingain)
    if tree.fb == None:
        prune(tree.fb,mingain)
    # If both the subbranches are now leaves, see if they should merged    
    if tree.tb.results!=None and tree.fb.results!=None:
        tb,fb=[],[]
        for v,c in tree.tb.results.items():
            tb+=[[v]]*c
        for v,c in tree.fb.results.items():
            fb+=[[v]]*c
        # Test the reduction in entropy
        delta = entropy(tb+fb)-(entropy(tb)+entroy(fb))/2
        if delta<mingain:
            # Merge the branches
            tree.fb,tree.tb=None,None
            tree.results=uniquecounts(tb+fb)

#Dealing with Missing Data
def mdclassify(observation,tree):
    if tree.results!=None:
        return tree.results
    else:
        v = observation[tree.col]
        if v==None:
            tr,fr = mdclassify(observation,tree.tb),mdclassify(observation,tree.fb)
            tcount = sum(tr.values())
            fcount = sum(fr.values())
            tw = float(tcount)/(tcount+fcount)
            fw = float(fcount)/(tcount+fcount)
            result={}
            for v,c in tr.items():
                result[v]=c*tw
            for v,c in fr.items():
                result[v]=c*fw
            return result
        else:
            if isinstance(v,int) or isinstance(v,float):
                if v>=tree.value: 
                        branch=tree.tb
                else: 
                    branch=tree.fb
            else:
                if v==tree.value: 
                    branch=tree.tb
                else: 
                    branch=tree.fb
            return mdclassify(observation,branch)

def variance(rows):
    if len(rows)==0:
        return 0
    else:
        data = [float(row[len(row)-1]) for row in rows]
        mean=sum(data)/len(data)
        variance=sum([(d-mean)**2 for d in data])/len(data)
        return variance
        
if __name__=='__main__':
    tree = buildtrees(my_data,entropy)
    printtree(tree)
    # drawtree(tree, jpeg = 'treeview.jpg')

    print ("\n['(direct)', 'USA', 'yes', 5] predicted as", \
          classify(['(direct)', 'USA', 'yes', 5], tree))

    print ("\n[None, 'USA', 'yes', None] predicted as", \
          mdclassify([None, 'USA', 'yes', None], tree))


    print ("\nAfter pruning...")
    prune(tree, 1.0)
    printtree(tree)