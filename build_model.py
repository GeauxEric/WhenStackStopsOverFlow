#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
sns.set()
plt.rcParams['figure.figsize'] = (12, 8)
sns.set_style("darkgrid")
sns.set_context("poster", font_scale=1.3)

from sklearn import metrics
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from feature_union import unionFeature

feature_union = unionFeature()

import pandas as pd

# starting_date = "2015-11-01"
starting_date = "2016-03-01"

qa = pd.read_pickle("./extracted.{}.pkl".format(starting_date))
qa.shape

qa.posttypeid.value_counts()

qa.head(1)

questions_ids = qa[qa['posttypeid'] == 1]['id']
questions_ids.shape

qa['hasCodes'] = qa.codes.apply(lambda c: 0 if c is None else 1)

answers = qa[qa.posttypeid == 2]

answers.head(1)

questions_answered_ids = questions_ids[questions_ids.isin(answers.parentid)]

questions_unanswered_ids = questions_ids[~questions_ids.isin(answers.parentid)]

questions = qa[qa['id'].isin(questions_ids)]

answered_q = questions[questions['id'].isin(questions_answered_ids)]

q_a = pd.merge(answered_q, answers, left_on='id', right_on='parentid')

q_a['ElapsedTime'] = (
    q_a.creationdate_y - q_a.creationdate_x).astype('timedelta64[m]')

q_a.sample(200).plot(kind='scatter', x='hasCodes_x', y='ElapsedTime')

shortest_elapsed_time = q_a.groupby('id_x').apply(
    lambda g: g['ElapsedTime'].min())

print("One week = {} min".format(24 * 60 * 7))

questions_answered_late_ids = shortest_elapsed_time[shortest_elapsed_time >
                                                    10080].index

failed_questions_ids = np.concatenate(
    (questions_unanswered_ids.values, questions_answered_late_ids))

failed_questions_ids.shape

questions['success'] = questions['id'].isin(failed_questions_ids).apply(
    lambda b: 0 if b else 1)

questions.head(1)

feature_cols = ['title', 'paragraphs', 'tags', 'hasCodes']

cls_df = questions[feature_cols + ['success']]

cls_df.head()

cls_train = cls_df.sample(int(cls_df.shape[0] / 2))

cls_test = cls_df[~cls_df.index.isin(cls_train.index)]

pipeline = Pipeline(feature_union + [('cls', LogisticRegression()), ])

pipeline.fit(cls_train[feature_cols], cls_train['success'])
y = pipeline.predict(cls_test[feature_cols])
print(classification_report(y, cls_test['success']))

joblib.dump(pipeline, "./logistic_regression.{}.pkl".format(starting_date))

random_guesses = cls_df.success.sample(cls_test.shape[0])

print(classification_report(random_guesses, cls_test['success']))
"""

scores = pipeline.decision_function(cls_test[feature_cols])
fpr, tpr, thresholds = metrics.roc_curve(cls_test['success'],
                                         scores,
                                         pos_label=1)

plt.figure()
plt.plot(fpr, tpr)
plt.xlabel("False positive rate")
plt.ylabel("True positive rate")
plt.savefig("./logistic_regression_roc.png")
plt.title("ROC of logistic regression classifier")
print("Area under curve is {}".format(metrics.auc(fpr, tpr)))
"""

# pipeline = Pipeline(feature_union + [
#     ('cls', RandomForestClassifier(n_jobs=4, class_weight='balanced')),
# ])
# pipeline.fit(cls_train[feature_cols], cls_train['success'])
# y = pipeline.predict(cls_test[feature_cols])
# print(classification_report(y, cls_test['success']))

# scores = pipeline.predict_proba(cls_test[feature_cols])

# fpr, tpr, thresholds = metrics.roc_curve(cls_test['success'],
#                                          scores[:, 1],
#                                          pos_label=1)

# plt.figure()
# plt.plot(fpr, tpr)
# plt.xlabel("False positive rate")
# plt.ylabel("True positive rate")
# plt.savefig("./random_forest_roc.png")
# plt.title("ROC of random forest classifier")
# print("Area under curve is {}".format(metrics.auc(fpr, tpr)))

good_q_a = q_a[~q_a.acceptedanswerid_x.isnull()]

good_q_a.ElapsedTime.hist()

good_q_a.head(1)

X = good_q_a[['title_x', 'paragraphs_x', 'tags_x', 'hasCodes_x']]
X.columns = ['title', 'paragraphs', 'tags', 'hasCodes']
y = good_q_a.ElapsedTime

X_train, X_test, y_train, y_test = train_test_split(X,
                                                    y,
                                                    test_size=0.33,
                                                    random_state=42)

pipeline = Pipeline(feature_union + [('reg', LinearRegression(n_jobs=6)), ])

pipeline.fit(X_train, y_train)

y = pipeline.predict(X_test)

print(mean_absolute_error(y, y_test))

joblib.dump(pipeline, "./linear_regression.{}.pkl".format(starting_date))