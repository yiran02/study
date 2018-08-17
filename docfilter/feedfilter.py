import feedparser
import re
import docclass

# Takes a filename of URL of a blog feed and classifies the entries
def read(feed,classifier):
    # Get feed entries and loop over them
    f=feedparser.parse(feed)
    for entry in f['entries']:
        print()
        print('-'*10)
        # Print the contents of the entry
        print('Title: ',entry['title'].encode('utf-8'))
        print('Publisher: ',entry['publisher'].encode('utf-8'))
        print()
        print(entry['summary'].encode('utf-8'))
        # Combine all the text to create one item for the classifier
        fulltext = '%s\n%s\n%s'%(entry['title'],entry['publisher'],entry['summary'])
        # Print the best guess at the current category
        print('Guess:'+str(classifier.classify(entry)))
        # Ask the user to specify the correct category and train on that
        cl = input('Enter category:')
        classifier.train(entry,cl)
        
def entryfeatures(entry):
    f={}
    splitter = re.compile('\W')
    # Extract the title words and annotate
    titlewords = [word.lower() for word in splitter.split(entry['title']) if len(word)>2 and len(word)<20]
    for w in titlewords:
        f['Title'+w]=1
    
    # Extract the summary words
    summarywords = [s for s in splitter.split(entry['summary']) if len(s)<2 and len(s)<20]
    
    #count of uppercase words
    uc=0
    for i in range(len(summarywords)):
        w = summarywords[i]
        f[w]=1
        if w.isupper():
            uc+=1
        # Get word pairs in summary as features
        if i < len(summarywords)-1:
            totalwords = ' '.join(summarywords[i:i+1])
            f[totalwords]=1
    # Keep creator and publisher whole
    f['Publisher:'+entry['publisher']]=1
    # UPPERCASE is a virtual word flagging too much shouting
    if float(uc)/len(summarywords)>0.3: f['UPPERCASE']=1
    return f        

if __init__=='__mian__':
    cl=docclass.fisherclassifier(entryfeatures)
    cl.setdb('test') 
    read('python_search.xml',cl)