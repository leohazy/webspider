# -*- coding: utf-8 -*-

import os
import re
import requests

class Tool:
	#去除图片信息
	removeImg = re.compile('<IMG SRC=".*?" onload=".*?"><br/>')
	#去除文末标注
	removeFont = re.compile('</font><font class=.*?</font><font class=.*?\n')

	def repalce(self,x):
		x = re.sub(self.removeImg,"",x)
		x = re.sub(self.removeFont,"",x)

		return x.strip()

class Shuiyuan_LovebridgeSpider:
	def __init__(self,init_url=None):
		print("开始爬去水源bbs鹊桥板块上的帖子。。")
		print("水源bbs鹊桥板块目前共有"+str(self.get_totalPageNums())+"页帖子")
		self.tool = Tool() 
		self.maxPageNum = self.get_totalPageNums()
		if(init_url==None):
			self.init_url = 'https://bbs.sjtu.edu.cn/bbsdoc,board,LoveBridge,page,'+str(self.maxPageNum-1)+'.html'
		else:
			self.init_url = init_url
		print("开始页面为: "+self.init_url)
		self.pageNum = int(input("请输入想要获取的页数："))
		self.validPageNum()

	def validPageNum(self):
		if self.pageNum >= self.maxPageNum:
			print("输入的页数过大，最多只能"+str(self.maxPageNum))
			print("已按照最大页数"+str(self.maxPageNum)+"进行抓取")
			self.pageNum = self.maxPageNum
			
	def get_sourcecode(self,url):
		html = requests.get(url).text
		return html

	def get_totalPageNums(self):
		homePage = 'https://bbs.sjtu.edu.cn/bbsdoc,board,LoveBridge.html'
		html = self.get_sourcecode(homePage)
		pattern_num = re.compile(r'<a .*?(\d+).html>上一页</a>',re.S)
		return int(pattern_num.findall(html)[0])+2

	def get_allurls(self,url,pageNum):
		pageGroup = []
		def num_sub1(match):
			return str(int(match.group())-1)
		p = re.compile(r'\d+')
		for i in range(pageNum):
			pageGroup.append(url)
			url = p.sub(num_sub1,url)
		return pageGroup

	def get_postinfo(self,html):
		pattern_blcok = re.compile(r'<tr><td>(\d+)<td>.*?<td><a href="bbsqry.*?userid=.*?">.*?</a><td>.*?<td><a(.*?)</a>',re.S)	
		pattern_post = re.compile(r'href=(.*?)>')

		post_url = []
		block = pattern_blcok.findall(html)
		for x in block:	
#		    由于正文的序号处都应该位数字，所以直接在正则表达式中就可以判断了
#			if any(excludeWords  in x[0] for excludeWords in ['板规','通知']):	
#				print(x[0])
#				continue
			if all(excludeWords not in x[1] for excludeWords in ['Re','发文权限','公告','任命']):
				post = pattern_post.findall(x[1])
				post = 'https://bbs.sjtu.edu.cn/'+post[0]
				post_url.append(post)

		return post_url

	def get_postText(self,url):
		pattern_postText = re.compile(r'<pre>发信人.*?信区: LoveBridge(.*?)</pre>',re.S)
	#	pattern_postTitle = re.compile(r'标  题: (.*?)\n')
		pattern_postTitle = re.compile(r'<title>(.*?) - 饮水思源</title>')
		post_html = requests.get(url).text

		try:
			postTitle = pattern_postTitle.findall(post_html)[0]
			postText_PreTool = pattern_postText.findall(post_html)[0]
		except	IndexError:
			print(" 正文格式与预定义的不同，匹配结果错误！@get_postText")
			print(postTitle)
			#用(.*?)时，一定不能忘了re.S
			postText_PreTool = re.compile(r'<pre>(.*?)</pre>',re.S).findall(post_html)[0]
			#返回值这里如何处理？	

		postText = self.tool.repalce(postText_PreTool)

		return postText,postText_PreTool,postTitle

	def get_Pic(self,postText_PreTool):
		pattern_getPic = re.compile(r'<IMG SRC="(.*?)"')
		picUrl_list = pattern_getPic.findall(postText_PreTool)
		imgContent_list = []
		for i in picUrl_list:
			picUrl = 'https://bbs.sjtu.edu.cn' + i
			image = requests.get(picUrl).content
			imgContent_list.append(image)

		return imgContent_list

	def baseDir(self):
		currentdir = os.getcwd()
		parrentdir = os.path.dirname(currentdir)
		return parrentdir+"\\Data\\SJTU_BBS\\Post_LB\\"

	def getReNums(self,url):
		#fetch reUrl
		pattern_postRe = re.compile(r'<a href=\'(bbstfind0.*?)\'>同主题列表</a>',re.S)
		post_html = requests.get(url).text
		reUrl = 'https://bbs.sjtu.edu.cn/' + pattern_postRe.findall(post_html)[0]
		#get reNums
		pattern_reNum = re.compile(r'共找到 (\d+) 篇')		
		return int(pattern_reNum.findall(requests.get(reUrl).text)[0])-1

	def savePost(self,postText,postTitle,imgContent_list,url):
		postTitle = re.sub('[\/:*?"<>|\.\'\s]','_', postTitle) #去掉不符合规范的符号
		richNum = [len(imgContent_list),self.getReNums(url)]
		richNum = str(richNum)
		os.makedirs(self.baseDir()+richNum+postTitle)
		f_txt = open(self.baseDir()+richNum+postTitle+"\\"+postTitle+".txt",'w',encoding="utf-8")
		f_txt.write(postText+'\n'+url)
		f_txt.close()

		if imgContent_list:
			for index ,img in enumerate(imgContent_list):
				f_img = open(self.baseDir()+richNum+postTitle+"\\"+str(index+1)+".jpg",'wb')
				f_img.write(img)
				f_img.close()

	def start(self):
		pageGroup = self.get_allurls(self.init_url,self.pageNum)
		TotalPost = 0
		i = [1,0]
		for page in pageGroup:
			print("开始获取第"+str(i[0])+"页的内容...")
			html=self.get_sourcecode(page)
			post_url = self.get_postinfo(html)
			print("本页共有"+str(len(post_url))+"个帖子")
			print("页面地址为"+page)
			TotalPost += len(post_url)
			j = 1
			for postUrl in post_url:
				try:
						print("开始抓取第"+str(i[0])+':'+str(j)+'/'+str(len(post_url))+"个帖子的内容")
						(postText,postText_PreTool,postTitle) = self.get_postText(postUrl)
						imgContent_list = self.get_Pic(postText_PreTool)

						self.savePost(postText,postTitle,imgContent_list,postUrl)
						print("第"+str(j)+"个帖子的内容保存完毕！\n")
						j += 1
				except	Exception as e:
					i[1] += 1
					print(e)
					print("页面地址为"+page+"\n帖子地址为"+postUrl)
					if i[1]==1 :
						f_err =  open(self.baseDir()+"errRecord.txt",'w',encoding="utf-8")
					else:
						f_err =  open(self.baseDir()+"errRecord.txt",'a',encoding="utf-8")
					f_err.write('\n'+str(e)+"\n页面地址为"+page+"\n帖子地址为"+postUrl+"\n帖子为:"+postTitle+'\n')#这里为什么要在前后加上\n才能实现断行
					f_err.close()

			print("第"+str(i[0])+"页的内容保存完毕！\n")
			i[0] += 1
			if int(re.compile(r'-?[\d]+').findall(page)[0]) == 0 :#可抓取负数
				print("已经抓取到第零页了！")
				break
		print("共抓取了"+str(i[0]-1)+"页 - "+str(TotalPost)+"个帖子!")
		print("共有"+str(i[1])+"次抓取失败，失败日志见"+self.baseDir()+"errRecord.txt")

init_url = "https://bbs.sjtu.edu.cn/bbsdoc,board,LoveBridge,page,47.html"
lovebridgespider1 = Shuiyuan_LovebridgeSpider(init_url)
lovebridgespider1.start()


