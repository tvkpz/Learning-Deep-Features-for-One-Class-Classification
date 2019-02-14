from keras.applications import MobileNetV2, VGG16
from keras.optimizers import SGD
from keras.models import Model
from keras.layers import GlobalAveragePooling2D, Dense
from keras import backend as K
from keras.engine.network import Network
from keras.datasets import fashion_mnist
from sklearn.neighbors import LocalOutlierFactor
from sklearn import metrics
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model

from data import makedata

import numpy as np
import matplotlib.pyplot as plt

input_shape = (96, 96, 3)
classes = 10
#feature_out = 512 #secondary network out for VGG16
feature_out = 1280 #secondary network out for MobileNet
alpha = 0.5 #for MobileNetV2
lambda_ = 0.1 #for compact loss

(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
X_train_s, X_ref, y_ref, X_test_s, X_test_b = makedata(x_train,x_test,y_train,y_test)

mobile = MobileNetV2(include_top=True, input_shape=input_shape, alpha=alpha,
                         depth_multiplier=1, weights='imagenet')

mobile.layers.pop() 

for layer in mobile.layers:
    if layer.name == "block_13_expand": # "block5_conv1": for VGG16
        break
    else:
        layer.trainable = False

model = Model(inputs=mobile.input,outputs=mobile.layers[-1].output)

model.load_weights('')

train = model.predict(X_train_s)
test_s = model.predict(X_test_s)
test_b = model.predict(X_test_b)

train = train.reshape((len(X_train_s),-1))
test_s = test_s.reshape((len(X_test_s),-1))
test_b = test_b.reshape((len(X_test_b),-1))

#0-1に変換
ms = MinMaxScaler()
train = ms.fit_transform(train)
test_s = ms.transform(test_s)
test_b = ms.transform(test_b)

# fit the model
clf = LocalOutlierFactor(n_neighbors=5)
y_pred = clf.fit(train)

# 異常スコア
Z1 = -clf._decision_function(test_s)
Z2 = -clf._decision_function(test_b)

#ROC曲線の描画
y_true = np.zeros(len(test_s)+len(test_b))
y_true[len(test_s):] = 1#0:正常、1：異常

# FPR, TPR(, しきい値) を算出
fpr, tpr, _ = metrics.roc_curve(y_true, np.hstack((Z1, Z2)))

# AUC
auc = metrics.auc(fpr, tpr)

# ROC曲線をプロット
plt.plot(fpr, tpr, label='DeepOneClassification(AUC = %.2f)'%auc)
plt.legend()
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.grid(True)
plt.show()
