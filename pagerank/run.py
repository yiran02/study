import searchengine
pages=['https://news.google.com.tw/']
crawler = searchengine.crawler('test')
crawler.createindextables()#create tables

crawler.crawl(pages)

crawler.caculatepagerank()

e = searchengine.searcher('test')
e.query('單場 球季')