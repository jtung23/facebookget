# Logic:
# Objective - store fbId, yelpId,3 day, 7 day, 14 day, 28 day.
# 	define function that does the math?
# Pull from AllRestaurant collection
# for each document
# 	store checkin, reviews, ratingcount in diff lists
# 	e.g. array: [{count: 35, query_date: 12/21/2017}, {count: 35, query_date: 12/21/2017}]
# 	do [index+1 - index]

import json
import requests
import statistics
import pymongo
from pymongo import MongoClient
import numpy
import pprint
pp = pprint.PrettyPrinter(indent=4)
from itertools import islice
import datetime
now = datetime.datetime.utcnow()
from operator import itemgetter, attrgetter, methodcaller

client = MongoClient('mongodb://admin:bootcamp123@ds159776.mlab.com:59776/heroku_vg8qr96g')
db = client.heroku_vg8qr96g

all_restaurants = db.all_restaurants

# returns the different values in list
# for each dict in list, find difference
# between value and value+1
# then save value+1 date
def sum_list(arr,first, last):
	sum = 0
	for x in arr[first:last]:
		int_x = float(x)
		sum += int_x
	return sum

def seperate_count(seq, filter):
	return [i[filter] for i in seq if i[filter]]

def percent_change(diff, totals):
	# divide diff[i] by totals[i]
	perc_change_list = []
	for i,each in enumerate(diff):
		percent = each/totals[i]
		perc_change_list.append(format(percent, '.6f'))
	return perc_change_list

def difference(arr):
	# seperates count into array
	checkins = seperate_count(arr['checkins'], 'checkins')
	ratings = seperate_count(arr['rating_count'], 'rating_count')
	reviews = seperate_count(arr['reviews'], 'review_count')

	# finds difference
	checkins_diff = list(numpy.diff(checkins))
	ratings_diff = list(numpy.diff(ratings))
	reviews_diff = list(numpy.diff(reviews))

	# finds %change, diff / total
	checkins_percent = percent_change(checkins_diff, checkins)
	ratings_percent = percent_change(ratings_diff, ratings)
	reviews_percent = percent_change(reviews_diff, reviews)
	data = {
		'fbId': arr['fbId'],
		'yelpId': arr['yelpId'],
		'checkins': {
			'difference': checkins_diff,
			'percent_change': checkins_percent
		},
		'rating_count': {
			'difference': ratings_diff,
			'percent_change': ratings_percent
		},
		'reviews': {
			'difference': reviews_diff,
			'percent_change': reviews_percent
		}
	}
	return data

restaurants = list(all_restaurants.find({'yelpId': 'jong-ga-house-oakland'}))
pp.pprint(restaurants)
from IPython import embed; embed()
all_data = []

# makes array of all checkins, rating count, and reviews 
for each in restaurants:
	all_data.append({
		'fbId': each['fbId'],
		'yelpId': each['yelpId'],
		'checkins': each['checkins'],
		'rating_count': each['rating_count'],
		'reviews': each['reviews']
	})
diff_data = []

for data in all_data:
	obj_diff = difference(data)
	diff_data.append(obj_diff)

# add last 7 percentchanges together, then
# weeklychange = recent 7 - previous 7
# total = weeklychange / previous7sum
# checkins total, ratings total, reviews total

def find_velocity(perc_list, second, third):
	# reverses percentage list
	rev_checkins = perc_list[::-1]
	# gets last 7 days sum
	recent_sum = sum_list(rev_checkins, None, second)
	# gets days 7 to 14 sum
	previous_sum = sum_list(rev_checkins, second, third)
	weekly_change = recent_sum - previous_sum

	if weekly_change == 0.0 or previous_sum == 0.0:
		velocity = None
	else:
		velocity = weekly_change/previous_sum
	return velocity

for this in diff_data:

	checkin_perc = this['checkins']['percent_change']
	rating_perc = this['rating_count']['percent_change']
	review_perc = this['reviews']['percent_change']

	checkin_vel7 = find_velocity(checkin_perc, 7, 14)
	rating_vel7 = find_velocity(rating_perc, 7, 14)
	review_vel7 = find_velocity(review_perc, 7, 14)

	checkin_vel14 = find_velocity(checkin_perc, 14, 28)
	rating_vel14 = find_velocity(rating_perc, 14, 28)
	review_vel14 = find_velocity(review_perc, 14, 28)

	score = {
		'trending_score': {
			'7day': {
				'checkins': checkin_vel7,
				'rating_count': rating_vel7,
				'review_count': review_vel7
			},
			'14day': {
				'checkins': checkin_vel14,
				'rating_count': rating_vel14,
				'review_count': review_vel14
			},
			'updated_on': str(now)
		}

	}

	# all_restaurants.update_one({'yelpId': this['yelpId']},
	# 	{"$set":score})

restaurants = list(all_restaurants.find())
pp.pprint(restaurants)
doobie = []
for bam in restaurants:
	doobie.append({
		'yelpId': bam['yelpId'],
		'score': bam['trending_score']['7day']['checkins']
	})

# have array of scores, now sort by score
replaced_none = [{'score': 0.0, 'yelpId':x['yelpId']} if x['score'] is None else x for x in doobie]
sorted_score_list = sorted(replaced_none , key=itemgetter('score'), reverse=True)

for i, scores in enumerate(sorted_score_list):
	scores['rank'] = i + 1
pp.pprint(sorted_score_list)
from IPython import embed; embed()