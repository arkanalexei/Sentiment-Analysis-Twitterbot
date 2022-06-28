"""
How does the program work?

Pertama, cari tweet ID dari tweet terakhir yang mention saya.
Hal ini mencegah pengulangan apabila program di run berkali-kali.
Jika tidak ada mention baru, program akan langsung berhenti.
Jika ada mention baru, maka last_id akan memiliki tweet ID yang berbeda dari
tweet ID yang baru mention tersebut.

Kedua, program akan menentukan tipe analisa yang akan dilakukan.
Jika tipe keyword, maka fungsi sentiment akan digunakan.
Jika tipe profile, maka fungsi sentiment_profile akan digunakan.

Ketiga, program akan reply dengan piechart.png ke tweet yang mention username
twitter saya.
"""

import tweepy
import logging
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob

# Jika nltk.sentiment.vader tidak ada,
# import nltk dan lakukan nltk.download('vader_lexicon')

consumer_key = ''
consumer_secret_key = ''
access_token = ''
access_token_secret = ''

auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# For adding logs in application
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


# Piechart
def piechart(keyword, positive, neutral, negative, is_keyword):

    labels = [f'Positive [{str(positive)}%]', f'Neutral [{str(neutral)}%]', f'Negative [{str(negative)}%]']
    sizes = [positive, neutral, negative]
    colors = ['yellowgreen', 'blue', 'red']

    plt.pie(sizes, colors=colors, startangle=90)
    plt.legend(labels)
    plt.axis('equal')

    if is_keyword:
        plt.title(f'Sentiment Analysis Result for Keyword: {keyword}')
    else:
        plt.title(f'Sentiment Analysis Result for Profile: {keyword}')

    return plt.savefig('piechart.png', facecolor='w')


# Sentiment Analysis
def sentiment(api, keyword, jumlah_tweet):

    jumlah_tweet = int(jumlah_tweet)
    positive = 0
    negative = 0
    neutral = 0
    polarity = 0

    tweets = tweepy.Cursor(api.search, q=keyword).items(jumlah_tweet)  # Search keyword

    try:
        for tweet in tweets:
            analysis = TextBlob(tweet.text)
            score = SentimentIntensityAnalyzer().polarity_scores(tweet.text)  # Magic
            neg = score['neg']
            pos = score['pos']
            polarity += analysis.sentiment.polarity

            if neg > pos:
                negative += 1

            elif pos > neg:
                positive += 1

            else:
                neutral += 1

    except tweepy.TweepError:
        return f'Keyword "{keyword}" was not found! '

    positive = f'{positive / jumlah_tweet * 100:.1f}'
    negative = f'{negative / jumlah_tweet * 100:.1f}'
    neutral = f'{neutral / jumlah_tweet * 100:.1f}'

    return piechart(keyword, positive, neutral, negative, True) if float(positive) + float(negative) + float(
        neutral) == 100.0 else f'keyword "{keyword}" has less than {jumlah_tweet} tweets!'


# Sentiment Analysis Profil
def sentiment_profil(api, keyword, jumlah_tweet):

    jumlah_tweet = int(jumlah_tweet)
    positive = 0
    negative = 0
    neutral = 0
    polarity = 0

    tweets = tweepy.Cursor(api.user_timeline, keyword).items(jumlah_tweet)  # Search profile

    try:

        for tweet in tweets:
            analysis = TextBlob(tweet.text)
            score = SentimentIntensityAnalyzer().polarity_scores(tweet.text)  # Magic v2
            neg = score['neg']
            pos = score['pos']
            polarity += analysis.sentiment.polarity

            if neg > pos:
                negative += 1

            elif pos > neg:
                positive += 1

            else:
                neutral += 1

    except tweepy.TweepError:
        return f'Username {keyword} not found!'

    positive = f'{positive / jumlah_tweet * 100:.1f}'
    negative = f'{negative / jumlah_tweet * 100:.1f}'
    neutral = f'{neutral / jumlah_tweet * 100:.1f}'

    return piechart(keyword, positive, neutral, negative, False) if float(positive) + float(negative) + float(
        neutral) == 100.0 else f'User {keyword} has less than {jumlah_tweet} tweets and replies'


# Tweet ID mention terakhir
def get_last_tweet(file):
    f = open(file, 'r')
    lastId = int(f.read().strip())
    f.close()
    return lastId


# Mengganti Tweet ID menjadi yang terbaru
def put_last_tweet(file, Id):
    f = open(file, 'w')
    f.write(str(Id))
    f.close()
    logger.info("Updated the file with the latest tweet Id")
    return


# Fungsi utama
def respond_to_tweet(file='tweet_ID.txt'):
    last_id = get_last_tweet(file)
    mentions = api.mentions_timeline(last_id, tweet_mode='extended')

    if len(mentions) == 0:
        return

    new_id = 0
    logger.info("someone mentioned me...")

    for mention in reversed(mentions):
        logger.info(str(mention.id) + '-' + mention.full_text)
        new_id = mention.id
        answer = mention.full_text.split()

        if answer[1].lower() == 'profile':
            logger.info(f"Answering profile to {mention.user.name}")
            try:
                sentiment_profil(api, answer[2], answer[3])

                media = api.media_upload(filename='piechart.png')

                api.update_status(
                    status='Here you go!',
                    in_reply_to_status_id=mention.id,
                    media_ids=[media.media_id],
                    auto_populate_reply_metadata=True
                )
            except:
                logger.info("Already replied to {}".format(mention.id))

        elif answer[1].lower() == 'keyword':
            logger.info(f"Answering keyword to {mention.user.name}")

            try:
                sentiment(api, answer[2], answer[3])
                media = api.media_upload(filename='piechart.png')
                api.update_status(
                    status='Here you go!',
                    in_reply_to_status_id=mention.id,
                    media_ids=[media.media_id],
                    auto_populate_reply_metadata=True
                )
            except:
                logger.info("Already replied to {}".format(mention.id))
    put_last_tweet(file, new_id)


if __name__ == "__main__":
    respond_to_tweet()
