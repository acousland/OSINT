import mapStructure as ms
import scrape as sc

START_URL = "https://www.rfs.nsw.gov.au"
MAX_DEPTH = 1000

ms.map(START_URL,MAX_DEPTH)
#sc.scrape(START_URL)