import json
import requests

import pymongo
from pymongo import MongoClient

import pprint
pp = pprint.PrettyPrinter(indent=4)

import datetime
now = datetime.datetime.utcnow()

import facebook

client = MongoClient('mongodb://admin:bootcamp123@ds159776.mlab.com:59776/heroku_vg8qr96g')
db = client.heroku_vg8qr96g

access_token= 'EAAG0XCqokvMBADXjKrYtgQtp6E1PCWuUOXJ1ZBCOs1rGwp4tBOzJR0IcndbZAH83g3PGhZASgNmuvt0YEPafpCMzX6civGEQOHg8DWIgDILaniCbmnyTwmyDHbVbR53OEEbLT8c9AZBKy01THwgLCGTl3xZB1Xc8XpV5lNDsTogZDZD'
graph = facebook.GraphAPI(access_token=access_token, 
	version = 2.7)


all_restaurants = db.all_restaurants
all_ids = db.all_ids

# gets data from all_ids. adds initial data
allids = list(all_ids.find())
restaurants = list(all_restaurants.find())

yelp_ids = []
for each in restaurants:
	yelp_ids.append(each['yelpId'])

fb_ids = []

# from IPython import embed; embed()

for each in restaurants:
	fb_ids.append(each['fbId'])

# Yelp update
updated_list = []
for each in yelp_ids:
	yelp_id = each
	r = requests.get(
		'https://api.yelp.com/v3/businesses/' + yelp_id, 
		headers={
			"Authorization": 'Bearer Dt0X2kf0ef_hQ5Jc_5FNnxheSlXdFX1-svTZE6AJP0J4lBoVuMFRl66QgPFblxpMN-_AHN9OL3mek81qVap7DEtTMK2MrXxXpTxV31SVTbe-qajxmCEGj_nHwuEuWnYx'
			}).json()
	all_restaurants.find_one_and_update({
		'yelpId': r['id']
		},
		{'$push': {
			'reviews': {
				'review_count': r['review_count'],
				'query_date': str(now)
			}
		}}
		# '$set': {'rating': value['rating']}
	)

print('yelp update done')

# Facebook update
for each in fb_ids:
	fb_id = each
	search_link= fb_id + '?fields=name,rating_count,checkins'
	restaurants = graph.request(search_link)
	all_restaurants.find_one_and_update({
		'fbId': restaurants['id']
	},
	{
		'$push': {
			'rating_count': {
				'rating_count': restaurants['rating_count'],
				'query_date': str(now)
			},
			'checkins': {
				'checkins': restaurants['checkins'],
				'query_date': str(now)
			}
		}
	})

print('fb done')

# 
# GETS NEW FIRMS AND ADDS TO RESTAURANT COLLECTION
# 
print('start add new')
# finds missing Id that needs to be added to all_restaurant
new_ids = []
all_restaurant_ids = []
for datum in allids:
	new_ids.append({'yelpId': datum['yelpId'], 'fbId': datum['fbId']})

restaurants = list(all_restaurants.find())
pp.pprint(restaurants)
for val in restaurants:
	all_restaurant_ids.append({'yelpId': val['yelpId'], 'fbId': val['fbId']})

# gets array of ids that need to be added to collection
missing_id =list(filter(lambda x: x not in all_restaurant_ids, new_ids))

headers = []

for value in missing_id:
	place_id = value['fbId']
	search_link= place_id + '?fields=name,rating_count,checkins,overall_star_rating'
	firms = graph.request(search_link)

	r = requests.get('https://api.yelp.com/v3/businesses/' + value['yelpId'], 
		headers={"Authorization": 'Bearer Dt0X2kf0ef_hQ5Jc_5FNnxheSlXdFX1-svTZE6AJP0J4lBoVuMFRl66QgPFblxpMN-_AHN9OL3mek81qVap7DEtTMK2MrXxXpTxV31SVTbe-qajxmCEGj_nHwuEuWnYx'}).json()
	dat={}
	dat['name']= r['name']
	dat['yelpId']= r['id']
	dat['fbId']=value['fbId']
	dat['price'] = r.get('price')
	dat['rating']= [{
		'rating': r['rating'],
		'query_date': str(now)
	}]
	dat['reviews']= [{
		'review_count': r['review_count'],
		'query_date': str(now)
		}
	]
	dat['checkins']= [
		{
			'checkins': firms['checkins'],
			'query_date': str(now)
		}
	]
	dat['star_rating']=[
		{
			'overall_star_rating': firms.get('overall_star_rating'),
			'query_date': str(now)
		}
	]
	dat['rating_count']=[
		{
		'rating_count': firms['rating_count'],
		'query_date': str(now)
		}
	]
	dat['categories']= r['categories']
	dat['phone']= r['display_phone']
	dat['yelpURL']= r['url']
	dat['yelpImg']= r['image_url']
	dat['location']= {
		'address': r['location']['address1'],
		'city': r['location']['city'],
		'state': r['location']['state'],
		'country': r['location']['country']
	}
	headers.append(dat)

pp.pprint(headers)

for data in headers:
	all_restaurants.update_one({'yelpId': data['yelpId']},
		{"$set":data}, upsert=True)
print('added new')
print(all_restaurants.count())
# from IPython import embed; embed()
