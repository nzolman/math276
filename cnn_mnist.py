# -*- coding: utf-8 -*-
"""
Created on Sun Jan 28 18:48:11 2018

@author: Thomas Tu
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
from os.path import dirname, abspath, join

tf.logging.set_verbosity(tf.logging.INFO)

def cnn_model_fn(features, labels, mode):
    input_layer = tf.reshape(features["x"], [-1,28,28,1])
    conv1 = tf.layers.conv2d(
            inputs=input_layer,
            filters=32,
            kernel_size=[5,5],
            padding="same",
            activation=tf.nn.relu)
    
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2,2],strides=2)
    conv2 = tf.layers.conv2d(
            inputs=pool1,
            filters=64,
            kernel_size=[5,5],
            padding="same",
            activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2,2],strides=2)
    
    pool2_flat = tf.reshape(pool2, [-1,7*7*64])
    dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)
    dropout = tf.layers.dropout(
            inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
    
    logits = tf.layers.dense(inputs=dropout, units=10)
    
    predictions = {
            "classes": tf.arg_max(input=logits, dimension=1),
            "probabilities": tf.nn.softmax(logits, name="softmax_tensor"),
            "logits": logits,
            "conv1": conv1,
            "conv2": conv2}
    # "smuggle" out logits
#    loss_vs_target = tf.nn.sparse_softmax_cross_entropy_with_logits(
#        logits=logits, 
#        labels=features['fake_targets']
#    )
#    predictions['image_gradient_vs_fake_target'] = tf.gradients(loss_vs_target, [input_layer])

    
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)
    
    loss = tf.losses.sparse_softmax_cross_entropy(labels=labels, logits=logits)
    
    if mode == tf.estimator.ModeKeys.TRAIN:
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
        train_op = optimizer.minimize(
                loss=loss,
                global_step=tf.train.get_global_step())
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)
    
    eval_metric_ops = {
            "accuracy": tf.metrics.accuracy(
                    labels=labels, predictions=predictions["classes"])}
    return tf.estimator.EstimatorSpec(
            mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)

def mnist_direct_data_input_fn(features_np_dict, targets_np):
    features_dict = { k:tf.constant(v) for k,v in features_np_dict.items()}
    targets = None if targets_np is None else tf.constant(targets_np)
    return features_dict, targets

def main(unused_argv):
    mnist = tf.contrib.learn.datasets.load_dataset("mnist")
    train_data = mnist.train.images
    train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
    eval_data = mnist.test.images
    eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)
    mnist_classifier = tf.estimator.Estimator(
            model_fn=cnn_model_fn, model_dir=join(dirname(abspath(__file__)),"mnist_convnet_model"))
    tensors_to_log = {"probabilities": "softmax_tensor"}
    logging_hook = tf.train.LoggingTensorHook(
            tensors=tensors_to_log, every_n_iter=50)
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": train_data},
               y=train_labels,
               batch_size=100,
               num_epochs=None,
               shuffle=True)
    mnist_classifier.train(
            input_fn=train_input_fn,
            steps=1,
            hooks=[logging_hook])


    tensor_prediction_generator = mnist_classifier.predict( 
        input_fn=tf.estimator.inputs.numpy_input_fn(
            x={"x": eval_data},
            y=eval_labels,
            num_epochs=1,
            shuffle=False),
        predict_keys=['logits', 'conv1', 'conv2']
    )
    
    for tensor_predictions in tensor_prediction_generator:
        break # Get the first one...
    
    print("########### LOGITS ###########")
    print(tensor_predictions['logits'])
    print("########### CONV1 ###########")
    print(tensor_predictions['conv1'])
    print("########### CONV2 ###########")
    print(tensor_predictions['conv2'])
#    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
#            x={"x": eval_data},
#            y=eval_labels,
#            num_epochs=1,
#            shuffle=False)
#    eval_results = mnist_classifier.evaluate(input_fn=eval_input_fn)
#    print(eval_results)
    
if __name__ == "__main__":
    tf.app.run()
    