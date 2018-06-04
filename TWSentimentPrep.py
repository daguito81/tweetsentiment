import tweepy
from tweepy import OAuthHandler
import indicoio
import json
import csv
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


credentials = json.loads(open('./keys/twitterkeys.json').read())
apikey = json.loads(open('./keys/indicokey.json').read())


def get_all_tweets(screen_name):
    # Twitter allows you get around 3000 tweets like this. We will check the timeline afterwards from datestamps

    auth = OAuthHandler(consumer_key=credentials['client_key'], consumer_secret=credentials['client_secret'])
    auth.set_access_token(key=credentials['resource_owner_key'], secret=credentials['resource_owner_secret'])

    api = tweepy.API(auth)

    alltweets = []  # To Store all the tweets

    new_tweets = api.user_timeline(screen_name=screen_name, count=200,
                                   tweet_mode='extended', include_rts=False)

    alltweets.extend(new_tweets)

    oldest = alltweets[-1].id - 1  # This is to save the ID of the oldest tweet we have

    # Now we grab EEEEVERYTHIIIIING (gary oldman)
    while len(new_tweets) > 0:
        print("Getting tweets before ", oldest)

        # new tweets pulled used oldest as the max id to avoid duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=200,
                                       max_id=oldest, tweet_mode='extended', include_rts=False)

        # save most recent tweets
        alltweets.extend(new_tweets)
        oldest = alltweets[-1].id - 1

        print("Downloaded: ", len(alltweets), " tweets so far!")

    # transform the list of tweets into an 2D Array to write into a CSV
    outtweets = [[tweet.id_str, tweet.created_at, tweet.full_text] for tweet in alltweets]

    with open('./Data/%s_tweets.csv' % screen_name, 'w', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "full_text"])
        writer.writerows(outtweets)
    pass


def prep_viz(screen_name):
    # This will give some very basic EDA and info and then fix the datetime

    df = pd.read_csv('./Data/%s_tweets.csv' % screen_name, encoding='utf8')
    print("-------------------------------------------------------")
    print("Number of Tweets: ", len(df['id']))
    print("Original Tweet from the last 3200:", (len(df['id']) / 3200) * 100, '%')
    print("")
    print("Earliest Tweet: ", df['created_at'].min())
    print("Latest Tweet: ", df['created_at'].max())
    a = datetime.strptime(df['created_at'].min(), '%Y-%m-%d %H:%M:%S')
    b = datetime.strptime(df['created_at'].max(), '%Y-%m-%d %H:%M:%S')
    length = len(df['id'])
    c = (b - a).days
    r = length / c

    print("Tweets/Day Average: ", round(r, 2))
    print("-------------------------------------------------------")

    df['date'] = df['created_at'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    df['date'] = df['date'].apply(lambda x: x.replace(hour=0, minute=0, second=0))

    plt.figure(figsize=(14, 8))
    df['date'].hist(bins=70)
    plt.title("Tweets over the past year")
    plt.xlabel("Date")
    plt.ylabel("Tweets")
    plt.show()

    df.to_csv('./Data/%s_prep.csv' % screen_name, encoding='utf8', index=False)


def sentiment(screen_name, language):
    # This will create a sentiment column and length column
    df = pd.read_csv('./Data/%s_prep.csv' % screen_name, encoding='utf8')
    indicoio.config.api_key = apikey['client_key']

    # Trial Run
    test = df.sample(50)
    test['length'] = test['full_text'].apply(len)
    test['sentiment'] = indicoio.sentiment(test['full_text'].tolist(), language=language)
    test['handle'] = screen_name

    # Real Run
    df['length'] = df['full_text'].apply(len)
    df['sentiment'] = indicoio.sentiment(df['full_text'].tolist(), language=language)
    df['handle'] = screen_name

    # Export both dataframes to csv
    test.to_csv('./Data/%s_test.csv' % screen_name, encoding='utf8', index=False)
    df.to_csv('./Data/%s_final.csv' % screen_name, encoding='utf8', index=False)


if __name__ == '__main__':
    # Pass in the username of the account you want to download
    print("")
    print("Let's scrape some TWITTA!!!")
    while True:
        print("Choices: 1) Scrape Twitter, 2) Prep and Viz, 3) Sentiment Prep, Anything else Quits")
        choice = input("Please make your choice: ")

        if choice == '1':
            screen_name = input("Please enter the Twitter handle: ")
            get_all_tweets(screen_name)
            print("DONE!")
            continue

        if choice == '2':
            screen_name = input("Please enter the Twitter handle: ")
            prep_viz(screen_name)
            print("DONE!")
            continue

        if choice == '3':
            screen_name = input("Please enter the Twitter handle: ")
            language = (input("Please enter language: ")).lower()
            sentiment(screen_name, language)
            print("Done")
            continue

        else:
            print("Quitting!!!")
            break
