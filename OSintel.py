import mapStructure as ms
import scrape as sc

START_URL = "https://www.zenenergy.com.au"
MAX_DEPTH = 10000

ms.map(START_URL,MAX_DEPTH)
#sc.scrape(START_URL)