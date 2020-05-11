import os
import os.path as op
import numpy as np

import tensorflow as tf
from datetime import datetime
now = datetime.now()


def get_data(base_dir, save_npy=True):
    # check if '.npy' files are in base path
    base_files = os.listdir(base_dir)
    if "y.npy" in base_files and "x.npy" in base_files:
        print("Loading data from local '.npy' files")
        x = np.load(op.join(base_dir, "x.npy"))
        y = np.load(op.join(base_dir, "y.npy"))
        return x, y

    filepath = op.join(base_dir, "sudoku.csv")
    x, y = [], []
    with open(filepath, 'r') as f:
        next(f)
        for line in f:
            a, b = line.rstrip().split(",")
            x.append([int(num) for num in a])
            y.append([int(num) for num in b])

    x = np.array(x)
    y = np.array(y)
    if save_npy:
        np.save("x.npy", x)
        np.save("y.npy", y)
    return x, y


# Read data
import sys
x, y = get_data(sys.argv[1])

# reserve first 100000 for testing
x_train = tf.keras.utils.to_categorical(x[100000:150000]).reshape((50000, 810))
y_train = tf.keras.utils.to_categorical(y[100000:150000]).reshape((50000, 810))

x_test = tf.keras.utils.to_categorical(x[:100000]).reshape((100000, 810))
y_test = y[:100000]

model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(4000, activation="relu", input_dim=810))
model.add(tf.keras.layers.Dense(4000, activation="relu"))
model.add(tf.keras.layers.Dense(4000, activation="tanh"))
model.add(tf.keras.layers.Dense(4000, activation="tanh"))
model.add(tf.keras.layers.Dense(810, activation="sigmoid"))

adam = tf.keras.optimizers.Adam(lr=0.0001)
model.compile(loss="categorical_crossentropy", optimizer=adam)

callbacks = [
    tf.keras.callbacks.TensorBoard(log_dir="./logs/{0:%Y-%m-%d_%H:%M:%S}".format(now)),
    tf.keras.callbacks.ReduceLROnPlateau(monitor="loss"),
    tf.keras.callbacks.ModelCheckpoint(
        "model_{0:%Y-%m-%d_%H:%M:%S}.h5".format(now),
        monitor="val_loss",
        save_best_only=True,
    ),
]

model.fit(
    x_train,
    y_train,
    epochs=20,
    batch_size=50,
    validation_split=0.1,
    callbacks=callbacks,
)
model.save("model-v2_{0:%Y-%m-%d_%H:%M:%S}.h5".format(now))

preds = model.predict(x_test[:3]).reshape((3, 81, 10))

# preds = np.argmax(preds, axis=2).reshape((100000, 81, 10))
# correct = 0
# for i, pred in enumerate(preds):
#     compared = (pred == y_test[i])
#     if False not in compared:
#         correct += 1
#
# print("\nModel correctly solved {}/100000 puzzles".format(correct))
