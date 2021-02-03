import webapp2, os, urllib2, json, jinja2, logging, urllib

#print organized data
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeGet(url):
    try:
        return urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if hasattr(e,"code"):
            logging.error("The server couldn't fulfill the request.")
            logging.error("Error code: ", e.code)
        elif hasattr(e,'reason'):
            logging.error("We failed to reach a server")
            logging.error("Reason: ", e.reason)
    return None


def cleanTimestamp(timestamp):
    cleantime = timestamp.split()
    date = cleantime[0]
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    cleandate = month + "." + day + "." + year
    time = cleantime[1][0:5]
    if int(time[0:2]) > 12:
        newtime = str(int(time[0:2]) - 12) + " p.m."
    else:
        newtime = str(int(time[0:2])) + " a.m."
    cleantimestamp = cleandate + " at " + newtime
    return cleantimestamp


def getDifficulty(string):
    if string == "green":
        difficulty = "easy"
    elif string == "greenBlue":
        difficulty = "Easy/Intermediate"
    elif string == "blue":
        difficulty = "intermediate"
    elif string == "blueBlack":
        difficulty = "Intermediate/Difficult"
    elif string == "black":
        difficulty = "difficult"
    else:
        difficulty = "Extremely Difficult"
    return difficulty


#key to use LocationIQ data
lockey = "ee78b2170710a9"

#key to use Hiking Project data
hikekey = "200631064-ab106bebec1fa44b7b27b1a66e8fa345"

#turns location string into coordinates (required in Hiking API)
def getLatLon(lockey, q):
    baseURL = "https://us1.locationiq.com/v1/search.php?key="
    fullURL = baseURL + lockey + "&q=" + q + "&format=json&limit=1"
    locstr = urllib2.urlopen(fullURL).read()
    locjson = json.loads(locstr)
    coordinates = {}
    coordinates['lat'] = str(locjson[0]['lat'])
    coordinates['lon'] = str(locjson[0]['lon'])
    return coordinates


def getHikes(loc, maxDistance, minLength, difficulty, hikekey):
    baseURL = "https://www.hikingproject.com/data/get-trails?"
    coords = getLatLon(lockey, loc)
    lat = coords['lat']
    lon = coords['lon']
    fullURL = baseURL + "lat=" + lat + "&lon=" + lon + "&maxDistance=" + str(maxDistance) + "&maxResults=100" + "&minLength=" + str(minLength) + "&key=" + hikekey
    hikestr = urllib2.urlopen(fullURL).read()
    hikejson = json.loads(hikestr)
    hikejson['diff'] = difficulty
    return hikejson

#gets hike information from Hiking API
def makeHikeList(hikejson):
    hikes = []
    for item in hikejson['trails']:
        hikeinfo = {}
        if getDifficulty(item['difficulty']) == hikejson['diff']:
            hikeinfo['hikename'] = item['name']
            if item['summary'] != "Needs Summary":
                hikeinfo['summary'] = item['summary']
            hikeinfo['location'] = item['location']
            hikeinfo['length'] = str(item['length']) + " miles"
            hikeinfo['ascent'] = str(item['ascent']) + " feet"
            hikeinfo['difficulty'] = getDifficulty(item['difficulty'])
            hikeinfo['photoURL'] = item['imgSmallMed']
            if hikeinfo['photoURL'] == "":
                 del hikeinfo['photoURL']
            hikeinfo['hikeURL'] = item['url']
            if item['conditionDetails'] != None:
                hikeinfo['conditionStatus'] = item['conditionStatus']
                hikeinfo['conditionDetails'] = item['conditionDetails']
                hikeinfo['conditionDate'] = "Last updated on " + cleanTimestamp(item['conditionDate'])
            hikeinfo['hikedata'] = str(item['length']) + " miles, " + str(item['ascent']) + " feet" + " (" + hikeinfo['difficulty'] + ")"
            hikes.append(hikeinfo)
    return hikes

def getCampgrounds(loc, maxDistance, hikekey):
    baseURL = "https://www.hikingproject.com/data/get-campgrounds?"
    coords = getLatLon(lockey, loc)
    lat = coords['lat']
    lon = coords['lon']
    fullURL = baseURL + "lat=" + lat + "&lon=" + lon + "&maxDistance=" + str(maxDistance) + "&maxResults=10" + "&key=" + hikekey
    campstr = urllib2.urlopen(fullURL).read()
    campjson = json.loads(campstr)
    return campjson


#gets campground information from Hiking API
def makeCampList(campjson):
    campgrounds = []
    for item in campjson['campgrounds']:
        campinfo = {}
        if item['isCampground'] == True:
            campinfo['name'] = item['name']
            campinfo['location'] = item['location']
            campinfo['photoURL'] = item['imgUrl']
            if campinfo['photoURL'] == "":
                 del campinfo['photoURL']
            elif campinfo['photoURL'] == 'https://www.rei.com/assets/camp/images/campground-placeholder-image/live.png':
                del campinfo['photoURL']
            campinfo['campURL'] = item['url']
            campgrounds.append(campinfo)
    return campgrounds


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                       extensions=['jinja2.ext.autoescape'], autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def genpage(self, input=None):
        template = JINJA_ENVIRONMENT.get_template("index.html")
        if input is not None:
            hikes = getHikes(input)
            hikelist = makeHikeList(hikes)
            template = JINJA_ENVIRONMENT.get_template("index.html")
            self.response.write(template.render(hikelist))

    def get(self):
        self.genpage()

    def post(self):
        input = None
        loc = self.request.get('location')
        travel = self.request.get('travel')
        length = self.request.get('length')
        difficulty = self.request.get('difficulty')
        if loc is not None and travel is not None and length is not None and difficulty is not None:
            input = {'loc':loc, 'maxDistance':travel, "minLength": length, 'difficulty': difficulty, 'key': hikekey}
            self.genpage(input)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render())

class Results(webapp2.RequestHandler):
    def get(self):
        loc = self.request.get('location')
        maxDistance = self.request.get('distance')
        minLength = self.request.get('length')
        difficulty = self.request.get('difficulty')
        hikes = getHikes(loc, maxDistance, minLength, difficulty, hikekey)
        hikes_list = makeHikeList(hikes)
        campgrounds = getCampgrounds(loc, maxDistance, hikekey)
        campgrounds_list = makeCampList(campgrounds)
        data = {}
        data['hikes'] = hikes_list
        data['campgrounds'] = campgrounds_list
        template = JINJA_ENVIRONMENT.get_template('results.html')
        self.response.out.write(template.render(data))
        print(pretty(data))

application =webapp2.WSGIApplication([('/results', Results), ('/.*', MainHandler)], debug=True)