from flask import Flask, render_template, url_for, request
import urllib2, time, cgi
from bs4 import BeautifulSoup

app = Flask(__name__) 

chartname = '';
str_chart='';

@app.route('/')
def radio():
  	return render_template('radio.html')

@app.route('/pick', methods=['POST'])
def home():
	global str_chart
	str_chart = request.form['chart']
	global chartname
	chartname = str_chart.replace(" ","-")
	chartname = chartname.replace("/","-")
	chartname = chartname.replace("&","-")
  	return render_template('pick.html', str_chart=str_chart)

@app.route('/graph')
def graph():
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	songs= map(findTitleArtist, getSongHtml(html))	
	data=[]
	date=[]
	for elem in songs:
		data.append(positionData(elem))
 	return render_template('graph.html', songs=songs, data=data, date=date, str_chart=str_chart)

@app.route('/graphdate', methods=['POST'])
def graphdate():
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	songs= map(findTitleArtist, getSongHtml(html))	
	args = request.form
	date =[ int(args['month']) , int(args['day']), int(args['year'])]		
	stringdate=	findClosestSat(date[0],date[1],date[2])
	data=[]
	for elem in songs:
		data.append(positionData(elem, stringdate))
 	return render_template('graph.html', songs=songs, data=data, date=date, str_chart=str_chart) 

@app.route('/chart')
def chart():	
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	songs= map(findTitleArtist, getSongHtml(html))	
	soup = BeautifulSoup(html)
	curr_date= [soup.findAll("ul","header_meta")[0].findAll("span","chart_date")[0].renderContents()]
	newsongs = getNewSongs()
	date=[]
	return render_template('chart.html', newsongs=newsongs, songs=songs, curr_date=curr_date, date=date, str_chart=str_chart)

@app.route('/chartdate', methods=['POST'])
def chartdate():	
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	songs= map(findTitleArtist, getSongHtml(html))	
	soup = BeautifulSoup(html)	
	curr_date= [soup.findAll("ul","header_meta")[0].findAll("span","chart_date")[0].renderContents()]	
	args = request.form
	date =[ int(args['month']) , int(args['day']), int(args['year'])]		
	stringdate=	[findClosestSat(date[0],date[1],date[2])]	
	newsongs = compareWith(stringdate[0])
	return render_template('chart.html', newsongs=newsongs, songs=songs, curr_date=curr_date, date=stringdate, str_chart=str_chart)	

def getSongHtml(html): 
	soup = BeautifulSoup(html)
	top = soup.findAll("article", "song_review no_category chart_albumTrack_detail no_divider") #number 1 special class
	songs = soup.findAll("article", "song_review no_category chart_albumTrack_detail") #number 2-9
	if (len(top)!=0): 
		songs.insert(0,top[0]) 
	return songs #complete 10 songs of current chart

#Song element is the complete article html (return from getSongHtml)
def lastWeekPosition(song_elem):
	return int(song_elem.findAll("ul", "chart_stats")[0].findAll("li")[1].renderContents()[29:-45:])

def findTitleArtist(song_elem):
	artist_info =song_elem.findAll("p","chart_info")[0] 
	if (len(artist_info.findAll("a"))==0): #No link for artist
		artist = artist_info.renderContents()[2:-10:].strip()
	else:
		artist = artist_info.findAll("a")[0].renderContents()
	return song_elem.findAll("h1")[0].renderContents().rstrip() + " by " + artist


"""
Returns songs that weren't on the chart.
Compared with last week's chart.
"""	
def getNewSongs():
	html = urllib2.urlopen('http://www.billboard.com/charts/'+chartname).read()
	songs = getSongHtml(html)
	new_songs=[]
	for elem in songs:
		if (lastWeekPosition(elem) >=11): #Wasn't top 10 last week
			new_songs.append(findTitleArtist(elem))
	return new_songs

"""
Finds which new songs on the chart appeared compared to the date.
Input date must fall on a chart.
"""
def compareWith(date): 
 	date_split = date.split('-')
 	year = int(date_split[0])
 	month = int(date_split[1])
 	day = int(date_split[2])
 	try: 
		past_html = urllib2.urlopen('http://www.billboard.com/charts/' + date + "/" + chartname).read()
	except urllib2.HTTPError: #Invalid date and chart doesn't exist
		return False 	
	past_songs = getSongHtml(past_html)
	past_song_titles= map(findTitleArtist, past_songs)
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	curr_songs = getSongHtml(html)	
	curr_song_titles= map(findTitleArtist, curr_songs)
	new_songs=[]
	for song in curr_song_titles:
		#Checking if current song was in past list
		if song not in past_song_titles:
			new_songs.append(song)
	return new_songs

"""
Finds the date of the chart closet to input.
Charts always released on Saturdays.
Returns string of y-m-d.
"""
def findClosestSat(month, day, year):
	month_num = {'January':1, 'February':2,'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}	
	thirty_day = [4,6,9,11]
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	soup = BeautifulSoup(html)
	curr_date= soup.findAll("ul","header_meta")[0].findAll("span","chart_date")[0].renderContents()
	curr_year=int(curr_date[-4::])
	if (curr_date[-8]==' '): #single digit
		curr_day= int(curr_date[-7])
		curr_month= month_num[curr_date[:-8:]]
	else:
		curr_day = int(curr_date[-8:-6:])
		curr_month = month_num[curr_date[:-9:]]
	#Dates later than current date will be directed to current chart.	
	if (year>curr_year or (year==curr_year and (month>curr_month or (month==curr_month and day>curr_day)))):
		return dateToString(curr_month,curr_day,curr_year)
	while (not (month==curr_month and day<=curr_day and day>(curr_day-7))):
		next_day=curr_day-7
		next_month=curr_month
		next_year=curr_year
		if (next_day<=0):
			next_month-=1
			if (next_month==0): #Previous year
				next_year-=1
				next_month=12
			if next_month!=2:
				if (next_month in thirty_day): 
					next_day+=30
				else:
					next_day+=31
			else: #Calc leap year
				if (next_year%4==0 and next_year%100!=0) or next_year%400==0:
					next_day+=29
				else:
					next_day+=28
		if (curr_day<6): #Special case
			if (month==next_month and next_day<day) or (month==curr_month and day<curr_day):
				return dateToString(curr_month,curr_day,curr_year)
		curr_day=next_day
		curr_month=next_month
		curr_year=next_year
		#print curr_day, curr_month, curr_year
	return dateToString(curr_month,curr_day,curr_year)

"""
Integer inputs returned as a string.
Format of "y-m-d" for billboard website.
"""
def dateToString(month, day, year):
	day = str(day)
	month=str(month)
	if len(day)==1: #Must be double digits
		day= "0" + day
	if len(month)==1: #Must be double digits
		month= "0" + month		
	return str(year)+'-'+ month+'-'+day

"""
ERROR CHECK
 if song not in current chart
 stop_date is the same as current

Inputs: 
Song is string with title and artist
Optional date must be in y-m-d format

When date not given, will stop when the song falls off chart.
Position will be found until date even if it falls off.
"""
def positionData(song, stop_date=False):
	position=[] #From most recent to latest
	date=[]
	html = urllib2.urlopen('http://www.billboard.com/charts/' +chartname).read()
	soup = BeautifulSoup(html)
	curr_date=soup.findAll("ul","header_meta")[0].findAll("span","chart_date")[0].renderContents()
	month_num = {'January':'01', 'February':'02','March':'03', 'April':'04', 'May':'05', 'June':'06', 'July':'07', 'August':'08', 'September':'09', 'October':'10', 'November':'11', 'December':'12'}		
	#First date will be in special format
	curr_year=curr_date[-4::]
	if (curr_date[-8]==' '): #single digit
		curr_day= curr_date[-7]
		curr_month= month_num[curr_date[:-8:]]
	else:
		curr_day = curr_date[-8:-6:]
		curr_month = month_num[curr_date[:-9:]]
	curr_date = curr_year + "-" + curr_month + "-" + curr_day
	date.append(curr_date)
	curr_songs= map(findTitleArtist, getSongHtml(html))
	if (not stop_date):
		while (song in curr_songs):
			position.append(curr_songs.index(song)+1) #index of song + 1 is the position
			prev_date=soup.findAll("ul","header_meta")[0].findAll("li","prev")[0].findAll("a")[0]['href']
			html = urllib2.urlopen('http://www.billboard.com/' + prev_date).read()
			soup = BeautifulSoup(html)
			curr_songs= map(findTitleArtist, getSongHtml(html))
			date.append(str(prev_date.split('/')[2]))		
		date.pop() #Last date invalid		
	else : #When stop date given
		while (curr_date!=stop_date):
			if (song in curr_songs):
				position.append(curr_songs.index(song)+1) #index of song + 1 is the position
			else: #Not on the chart.
				position.append(20)
			prev_date=soup.findAll("ul","header_meta")[0].findAll("li","prev")[0].findAll("a")[0]['href']
			html = urllib2.urlopen('http://www.billboard.com/' + prev_date).read()
			soup = BeautifulSoup(html)
			curr_songs= map(findTitleArtist, getSongHtml(html))
			curr_date = str(prev_date.split('/')[2])
			date.append(curr_date)		
		#Must add the position on stop date too
		if (song in curr_songs):
			position.append(curr_songs.index(song)+1) #index of song + 1 is the position
		else: #Not on the chart.
			position.append(20)
	result = []
	while (position[len(position)-1]==20):
		position.pop()
		date.pop()
	for i in range(len(date)):
		result.append([position[i], date[i]])
	return result

if __name__ == '__main__':
	app.run(debug=True)