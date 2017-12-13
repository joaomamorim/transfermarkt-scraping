import urllib
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
from time import time, sleep

CURRENT_YEAR = 17
N_SEASON_HISTORY = 5

def readRow( row):
	cells = row.find_all( "td")
	cells = list( map( lambda x : x.text.strip(), cells))
	year = cells[0]
	games_played = cells[4]
	goals_scored = cells[6]
	assists = cells[7]
	minutes_played = cells[-1]
	#year, _, _ , _, games_played, _, goals_scored, asists, _, minutes_played = map(lambda x : x.text.strip(), cells)
	games_played = int(games_played) if games_played != "-" else 0
	goals_scored = int(goals_scored) if goals_scored != "-" else 0
	assists = int(assists) if assists != "-" else 0
	minutes_played = int( minutes_played[:-1].replace(".","")) if minutes_played != "-" else 0
	return year, games_played, goals_scored, assists, minutes_played


class PlayerProfile:
	def __init__(self, playerUrl, pageScrapper):
		urlPerfPage = playerUrl.replace("profil","leistungsdatendetails")
		soup = pageScrapper( playerUrl)

		playerAttributes = {}

		#scrapping profile page information
		playerAttributes["name"] = soup.find("div", class_="dataMain").find("h1").text
		StoredAttributes = ["Age:", "Height:", "Nationality:", "Position:", "Foot:", "Current club:"]
		for entry in soup.find("table", class_="auflistung").find_all("th"):
			key = entry.text.strip()
			val = entry.find_next_sibling().text
			if key in StoredAttributes:
				playerAttributes[ key[:-1].lower()] = val.strip()
		#cleaning some entries
		if "height" in playerAttributes:
			#converting height in meters str to cm int 
			meter, centimeters = re.search("(\d),(\d+)",playerAttributes["height"]).groups()
			playerAttributes["height"] = int(meter)*100 + int(centimeters)
		if "nationality" in playerAttributes:
			if "\xa0" in playerAttributes["nationality"]:
				playerAttributes["nationality"] = playerAttributes["nationality"].replace("\xa0", " ")
		if "position" in playerAttributes:
			playerAttributes["position"] = "CF" if "Centre-Forward" in playerAttributes["position"] else "W"
		if "age" in playerAttributes:
			playerAttributes["age"] = int( playerAttributes["age"])

		#scrapping performance page information -- TODO => add scrapping of national team performance
		soup = pageScrapper(urlPerfPage)
		performanceColumns = ("season", "games", "goals", "assists", "minutes")
		performanceRows = pd.DataFrame( {col:[] for col in performanceColumns})
		for row in soup.find("div", class_="responsive-table").find("tbody").find_all("tr"):
			#try:
			rowContents = readRow( row)
			#except:
			#	 print( row)
			#else:
			#	 pass
			year = rowContents[0]
			if re.match( "\d{4}", year):
				year = int( year[2:])
				year = "%02d/%02d" %(year-1, year)
			if not re.match( "\d{2}/\d{2}", year):
				raise ValueError("Wrong format for played year")
			if int( year[:2]) < CURRENT_YEAR - N_SEASON_HISTORY:
				break
			#print( rowContents)
			performanceRows = performanceRows.append( {col:val for col, val in zip(performanceColumns, rowContents)}, ignore_index=True)
		performanceDF = performanceRows.groupby("season").sum()
		#converting to serie
		performanceSeries = pd.Series( {"%s %s" %(row, col): performanceDF[col][row] for row in performanceDF.index for col in performanceDF.columns})
		
		self.PlayerData = pd.Series( playerAttributes).append( performanceSeries)
		print( "\t%s done" %self.PlayerData["name"])
		
	def __str__(self):
		return "Performance profile for %s" % self.PlayerData["name"]

	def __repr__(self):
		return "< profile of %s >" % self.PlayerData["name"]

