import math
import optimization
people=['Charlie','Augustus','Veruca','Violet','Mike','Joe','Willy','Miranda']
links=[('Augustus', 'Willy'),
        ('Mike', 'Joe'),
        ('Miranda', 'Mike'),
        ('Violet', 'Augustus'),
        ('Miranda', 'Willy'),
        ('Charlie', 'Mike'),
        ('Veruca', 'Joe'),
        ('Miranda', 'Augustus'),
        ('Willy', 'Augustus'),
        ('Joe', 'Charlie'),
        ('Veruca', 'Augustus'),
        ('Miranda', 'Joe')]
domain = [(10,370)]*(len(people)*2)
def crosscount(v):
    total=0
    # (x,y) for each person
    loc=dict([(people[i],(v[i*2],v[i*2+1])) for i in range(len(people))])
    #loop through every pair of links
    for i in range(len(links)):
        for j in range(i+1,len(links)):
            (x1,y1),(x2,y2)=loc[links[i][0]],loc[links[i][1]]
            (x3,y3),(x4,y4)=loc[links[j][0]],loc[links[j][1]]
            #斜率分别为(y2-y1)/(x2-x1)和(y4-y3)/(x4-x3)
            #斜率相等，即den=0，则两线段平行，不可能相交
            den=(y4-y3)*(x2-x1)-(x4-x3)*(y2-y1)
            if den==0:
                continue
            # 以参数方程表示两条直线(x=x1+t(x2-x1))，分别令x，y相等，得到二元一次方程组，解得的两参数在0，1之间，则交点在线段上。
            ua=((x4-x3)*(y1-y3)-(y4-y3)*(x1-x3))/den
            ub=((x2-x1)*(y1-y3)-(y2-y1)*(x1-x3))/den
            if ua>0 and ua<1 and ub>0 and ub<1:
                total+=1
    # penalize close together nodes           
    for i in range(len(people)):
        for j in range(i+1,len(people)):
            (x1,y1),(x2,y2) = loc[people[i]],loc[people[j]]
            dist = math.sqrt(pow((x2-x1),2)+pow((y2-y1),2))
            if dist<50.:
                total+=(1-dist/50)
    return total

from PIL import Image,ImageDraw
def drawnetwork(sol):
    img = Image.new('RGB',(400,400),(255,255,255))
    draw = ImageDraw.Draw(img)
    
    #create position dict
    pos = dict([(people[i],(sol[i*2],sol[i*2+1])) for i in range(len(people))])
    #draw lines
    for (a,b) in links:
        draw.line((pos[a],pos[b]),(139, 121, 94))
    #draw nodes
    for n,p in pos.items():
        draw.text(p,n,(139, 37, 0))
    img.show()

if __name__=='__main__':
    sol = optimization.annealingoptimize(domain,crosscount,step=50,cool=0.99)
    drawnetwork(sol)