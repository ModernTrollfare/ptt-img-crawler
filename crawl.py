#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import re
import requests
from bs4 import BeautifulSoup

from datetime import timedelta
from datetime import date

from pathlib import Path



s = requests.Session()
rooturl = "https://www.ptt.cc/bbs/nba"
head = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'}

def getTgDates(off=None):
	if not off:
		off = 1
	r = []
	for x in range(1,1+off):
		tgdatetime=date.today()-timedelta(x)
		tgdate = '{0:2d}/{1:02d}'.format(tgdatetime.month, tgdatetime.day)
		r = r+[tgdate]
	return r

def crawlPage(subPageUrl=None):
	global s
	if subPageUrl:
		try:
			resp = s.get(subPageUrl, headers=head)
		except:
			print("Error crawling page "+subPageUrl)
			return
		pagesoup = BeautifulSoup(resp.text,features="html.parser")
		
		#other images
		filter1 = re.compile("(http|https)\:\/\/[0-9A-Za-z\.\/]*\.(jpg|png|jpeg|gif|bmp)")
		ulist = [x for x in pagesoup(text=filter1)]

		#imgur nonimages
		filter2 = re.compile(r"(http|https)://imgur.com")
		clist = [x['href'] for x in pagesoup.find_all("a",href=filter2) if x['href'] not in ulist]
		filter3 = re.compile(r"://i.imgur.com")

		for c in set(clist):
			try:
				resp = s.get(c, headers=head)
				content2=BeautifulSoup(resp.text,features="html.parser")
				ulist = ulist+[x['href'] for x in content2.find_all("a",href=filter3)]+[x['href'] for x in content2.find_all("link",href=filter3)]
			except:
				print("Failed to get page "+c)

		#all images
		for u in set(ulist):
			if not Path("img/"+u.split('/')[-1]).is_file():
				print("Getting Picture: "+u)
				try:
					resp = s.get(u, headers=head)
					resp.raise_for_status()
					with open("img/"+u.split('/')[-1],'wb') as f:
						f.write(resp.content)
				except:
					print("Response code for request: "+resp.status_code)
					print("Failed to get image "+u)
			else:
				print("Entry already exists:"+u)


def initCookies():
	global s,rooturl
	try:
		resp = s.get(rooturl, headers=head)
	except:
		print("Error sending initial request")
		raise
	resp.raise_for_status()

	#print("Initial request successful.")
	soup = BeautifulSoup(resp.text,features="html.parser")
	try:
		nextPage = soup(text=re.compile(u'上頁',re.UNICODE))[0].parent['href'].split('/')[-1]
	except:
		pass
	else:
		return True
	try:
		resp = s.post("https://www.ptt.cc/ask/over18?from=%2Fbbs%2FBeauty%2Findex.html", headers=head,data={'yes':'yes'})
	except:
		print("Error sending provision request")
		raise

	#print("Provision successful.")
	soup = BeautifulSoup(resp.text,features="html.parser")
	try:
		nextPage = soup(text=re.compile(u'上頁',re.UNICODE))[0].parent['href'].split('/')[-1]
	except:
		return False
	else:
		return True

def main():
	if initCookies():
		pass
	else:
		print("error")
	url = rooturl
	found = False
	tgDates = getTgDates(3);
	tgPosts = re.compile(r'\[(query)\]', re.UNICODE)
	count = 0

	while count < 500:
		count += 1;
		foundInRun=False
		try:
			resp = s.get(url, headers=head)
		except:
			print("Error sending request to" + url)
			break

		soup = BeautifulSoup(resp.text,features="html.parser")

		nextPage = soup(text=re.compile(u'上頁',re.UNICODE))[0].parent['href'].split('/')[-1]
		entries = soup.find_all('div', class_=['r-ent','r-list-sep'])

		for entry in entries:
			count += 1
			if entry['class'][0] == 'r-ent':
				if \
					entry.select("div.date")[0].text in tgDates \
				and entry.select("div.title > a") \
				and tgPosts.match(str(entry.select("div.title > a")[0].text)):
					if entry.select("div.nrec > span"):
						rating = str(entry.select("div.nrec > span")[0].text)
						if not "X" in rating:
							#and (rating == u'爆' or int(rating) >= 10):
							print(">>>>>Page Date:\t\t"+str(entry.select("div.date")[0].text))
							print(">>>>>Current subpage:\t "+rooturl+entry.select("div.title > a")[0]['href'].split('/')[-1])
							print(">>>>>Page Title:\t\t"+str(entry.select("div.title > a")[0].text))
							print(">>>>>Page rating:\t\t"+rating)
							found = True
							foundInRun = True
							crawlPage(subPageUrl=rooturl+entry.select("div.title > a")[0]['href'].split('/')[-1])
			else:
				break
		if found and not foundInRun:
			break
		url = rooturl+nextPage

if __name__ == "__main__":
    main()