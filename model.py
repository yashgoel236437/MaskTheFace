# Author: aqeelanwar
# Created: 2 May,2020, 10:48 AM
# Email: aqeel.anwar@gatech.edu
import tensorflow as tf
from network import VGGNet16
import numpy as np
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class DNN:
    def __init__(self, num_classes):
        self.g = tf.Graph()
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        with self.g.as_default():
            stat_writer_path = "return_plot/"
            loss_writer_path = "loss/"
            self.stat_writer = tf.summary.FileWriter(stat_writer_path)
            self.loss_writer = tf.summary.FileWriter(loss_writer_path)
            self.num_classes = num_classes

            # Placeholders
            self.batch_size = tf.placeholder(tf.int32, shape=())
            self.keep_prob = tf.placeholder(tf.float32, shape=())
            self.learning_rate = tf.placeholder(tf.float32, shape=())
            self.input_images = tf.placeholder(
                tf.float32, [None, None, None, 3], name="input"
            )
            self.labels = tf.placeholder(
                tf.int32, shape=[None], name="classes"
            )

            # Preprocessing
            self.X = tf.image.resize_images(self.input_images, (224, 224))
            self.input = tf.map_fn(
                lambda frame: tf.image.per_image_standardization(frame), self.X,
            )

            self.model = VGGNet16(self.input, num_classes, self.keep_prob)

            self.output = self.model.output
            self.prediction_probs = self.model.prediction_probs
            self.predict_class = tf.argmax(self.prediction_probs, axis=1)
            self.accuracy, self.accuracy_op = tf.metrics.accuracy(
                labels=self.labels, predictions=self.predict_class
            )

            self.test = tf.nn.sparse_softmax_cross_entropy_with_logits(
                labels=self.labels, logits=self.output
            )
            self.loss = tf.reduce_mean(self.test)
            self.train_op = tf.train.AdamOptimizer(
                learning_rate=self.learning_rate, beta1=0.9, beta2=0.99
            ).minimize(self.loss, name="train_op")

            self.sess = tf.InteractiveSession(config=config)
            tf.global_variables_initializer().run()
            tf.local_variables_initializer().run()
            self.saver = tf.train.Saver()
            self.all_vars = tf.trainable_variables()

            self.sess.graph.finalize()

    def predict(self, input):
        labels = self.classes = tf.placeholder(tf.int32, shape=[None, self.num_classes])
        predict_class, prediction_probs = self.sess.run(
            [self.predict_class, self.prediction_probs],
            feed_dict={
                self.batch_size: input.shape[0],
                self.learning_rate: 0,
                self.input_images: input,
                self.labels: labels,
                self.keep_prob: 1.0
            },
        )
        return predict_class, prediction_probs

    def train(self, input, labels, lr, iter, keep_prob):
        labels = np.squeeze(labels)
        _, loss, acc = self.sess.run(
            [self.train_op, self.loss, self.accuracy_op],
            feed_dict={
                self.batch_size: input.shape[0],
                self.learning_rate: lr,
                self.input_images: input,
                self.labels: labels,
                self.keep_prob: keep_prob
            },
        )
        # Log to tensorboard
        self.log_to_tensorboard(
            tag="Loss", group="Main", value=loss, index=iter, type="loss"
        )
        self.log_to_tensorboard(
            tag="Acc", group="Main", value=acc, index=iter, type="loss"
        )

        return loss, acc


    def log_to_tensorboard(self, tag, group, value, index, type="loss"):
        summary = tf.Summary()
        tag = group + "/" + tag
        summary.value.add(tag=tag, simple_value=value)
        if type == "loss":
            self.loss_writer.add_summary(summary, index)
        elif type == "stat":
            self.stat_writer.add_summary(summary, index)

    def get_accuracy(self, input, labels):
        labels = np.squeeze(labels)
        accuracy = self.sess.run(
            self.accuracy_op,
            feed_dict={
                self.batch_size: input.shape[0],
                self.learning_rate: 0,
                self.input_images: input,
                self.labels: labels,
                self.keep_prob: 1.0
            },
        )
        return accuracy

    def save_network(self, epoch):
        save_path = 'saved_network/net_' + str(epoch)+'.ckpt'
        self.saver.save(self.sess, save_path)
        print('Model Saved: ', save_path)