import random, smtplib, sys, time, datetime, random
from bs4 import BeautifulSoup
from urllib.request import urlopen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sleepTime = 5 * 60 # 5 Minute(s)

def parse_results(search_url):
	results = []
	soup = BeautifulSoup(urlopen(search_url).read(), "html.parser")
	listings = soup.find('ul', {"id":"search-results-list"}).find_all("li", class_="search-result")
	
	for listing in listings:
		if "search-result--sponsored-ad" in listing.attrs['class']:
			continue
		if "hide-if-empty" in listing.attrs['class']:
			continue
		id = listing['data-advert-id']
		url = "https://www.preloved.co.uk/adverts/show/" + id
		title = listing.find("span", {"itemprop":"name"}, text=True).get_text(strip=True)
		price = ' '.join([meta.get_text(strip=True) for meta in listing.find("span", class_="search-result__meta").find_all("span")])
		location = listing.find("span", class_="is-location", text=True).get_text(strip=True)

		results.append({'id': id, 'url': url, 'title': title, 'price': price, 'location': location})
		
	return results
	
def new_listings(results_old, results):
	listings_new = []
	check = set([d['id'] for d in results_old])
	differences = [d for d in results if d['id'] not in check]
	
	for d in differences:
		listings_new.append(d)
		
	return listings_new
	
	
def send_mail(listings):
	
	for email_to_one in email_to:
		print("Sending listings to {}".format(email_to_one))
		msg = MIMEMultipart()
		msg['From'] = email_from
		msg['To'] = email_to_one
		msg['Subject'] = "Preloved Listings ({}) - {}".format(len(listings), datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
		#message = 'New preloved listings for URL: ' + searchURL + "&rand=" + str(random.randint(0,1000000)) + "\n\n"
		message = 'New preloved listings for URL: ' + searchURL + "\n\n"
		for listing in listings:
			message = message + "{} - {} - {}\n".format(listing["title"], listing["location"], listing["price"])
			message = message + listing["url"] + "\n\n"
		message = message + ''
		message = message + '[{}] End of message'.format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
		msg.attach(MIMEText(message.encode('utf-8'), 'plain', 'UTF-8'))
		mailserver = smtplib.SMTP(email_server,587)
		# identify ourselves to smtp gmail client
		mailserver.ehlo()
		# secure our email with tls encryption
		mailserver.starttls()
		# re-identify ourselves as an encrypted connection
		mailserver.ehlo()
		mailserver.login(str(email_username), str(email_password))
		mailserver.sendmail(email_from, email_to_one, msg.as_string())
		print("** Mail sent!")
		mailserver.quit()
	
if __name__ == '__main__':
	try:
		email_username = sys.argv[1]
		email_password = sys.argv[2]
		email_server = sys.argv[3]
		email_from = sys.argv[4]
		email_to = sys.argv[5].split(",") #Support multiple emails separated by comma
		searchURL = sys.argv[6]
	except IndexError:
		exit("Missing arguments")
		
	print("Checking for listings at: " + searchURL)
	#Populate result array with new listings
	listings = parse_results(searchURL)

	while True:
		print("Checking preloved now")
		try:
			# Move old results to cache
			listings_old = listings
			# Clear listings table for new fetch
			listings = []
			# Fetch new listings
			listings = parse_results(searchURL)
			# If page broken, use old listings
			if not listings:
				listings = listings_old

			# Compare listings with cache, check for new results, send mail
			listings_new = new_listings(listings_old, listings)
			if listings_new:
				print("New listings! Sending mail")
				send_mail(listings_new)
			else:
				print("No new listings")
		except Exception as e:
			print(str(e) + '\n!Failed!')
		print("Sleeping for %d seconds" % sleepTime)
		time.sleep(sleepTime + random.randint(0, 20)) #Sleep for set time + random between 0 and 20 seconds