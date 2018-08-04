blognames,words,data=readfile('blogdata.txt')
blogencode = [i.encode('latin-1','ignore') for i in blognames]
coords=scaledown(data)
draw2d(coords,blogencode,jpeg='blogs2d.jpg')