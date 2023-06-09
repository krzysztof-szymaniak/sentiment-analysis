import os
import re

import numpy as np
import pandas as pd
from keras.layers import Embedding
from keras_preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from preprocessing import preprocess

imdb_file = 'datasets/IMDB_Dataset.csv'
twitter_train_file = 'datasets/twitter_training.csv'
twitter_test_file = 'datasets/twitter_validation.csv'
multi_domain = 'datasets/multi-domain'

INPUT_LENGTH = 100

def get_data(ds):
    if ds == imdb_file:
        imdb_data = pd.read_csv(ds)
        X = preprocess(imdb_data['review'])
        Y = imdb_data['sentiment'].values.tolist()
        Y = binarize_sentiment(Y)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, shuffle=True, random_state=42)
        return (X_train, y_train), (X_test, y_test)

    if ds == twitter_train_file:
        train_data_df = pd.read_csv(twitter_train_file)
        test_data_df = pd.read_csv(twitter_test_file)

        columns = ['Tweet ID', 'entity', 'sentiment', 'Tweet content']
        train_data_df.columns = columns
        test_data_df.columns = columns
        train_data_df.drop_duplicates(inplace=True)
        test_data_df.drop_duplicates(inplace=True)
        train_data_df.dropna(inplace=True)
        test_data_df.dropna(inplace=True)

        train_data_df = filter_invalid_sentiment(train_data_df)
        test_data_df = filter_invalid_sentiment(test_data_df)

        X_train = preprocess(train_data_df['Tweet content'])
        X_test = preprocess(test_data_df['Tweet content'])
        y_train = binarize_sentiment(train_data_df['sentiment'].values.tolist())
        y_test = binarize_sentiment(test_data_df['sentiment'].values.tolist())

        X = np.concatenate([X_train, X_test])
        y = np.concatenate([y_train, y_test])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, random_state=42)
        return (X_train, y_train), (X_test, y_test)

    if ds == multi_domain:
        X, y = parse_multi_domain()
        X = preprocess(X)
        y = np.array(y).astype(np.float32)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, random_state=42)
        return (X_train, y_train), (X_test, y_test)


def parse_multi_domain():
    X = []
    y = []
    for root, dirs, files in os.walk(multi_domain):
        for file in files:
            if 'unlabeled' not in file:
                file = os.path.join(root, file)
                with open(file, encoding='utf-8') as f:
                    xml = f.read()
                revs = re.findall(r'<review_text>[\s\S]*?</review_text>', xml)
                X.extend(map(lambda x: x.lstrip('<review_text>').rstrip('</review_text>'), revs))
                sentiment = 1 if 'positive' in file else 0
                y.extend([sentiment] * len(revs))
    return X, y


def binarize_sentiment(Y):
    return np.array(list(map(lambda x: 1 if x.lower() == 'positive' else 0, Y))).astype(np.float32)


def pad(X, w2v):
    xp = pad_sequences(sequences=vectorize_data(X, vocab=w2v.key_to_index), maxlen=INPUT_LENGTH, padding='post')
    return np.array(xp).astype(np.float32)


def filter_invalid_sentiment(df):
    # filter_out = df.index[df['sentiment'] == 'Neutral'].tolist()
    # filter_out.extend(df.index[df['sentiment'] == 'Irrelevant'].tolist())
    df = df[df['sentiment'] != 'Neutral']
    df = df[df['sentiment'] != 'Irrelevant']
    # X = [v for i, v in enumerate(X) if i not in filter_out]
    # print(f'{len(X)=}')
    return df


def vectorize_data(data, vocab):
    print(f'Vectorize sentences... ({len(data)})')
    keys = list(vocab.keys())
    vectorized = [[keys.index(word) for word in review if word in vocab] for review in data]
    print('Done')
    return vectorized


def get_embedding(w2v):
    embedding_matrix = w2v.vectors
    return Embedding(
        input_dim=embedding_matrix.shape[0],
        output_dim=embedding_matrix.shape[1],
        input_length=INPUT_LENGTH,
        weights=[embedding_matrix],
        trainable=False
    )
