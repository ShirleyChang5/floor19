#! /usr/bin/env python

import numpy as np
import tensorflow as tf

from .model import PTBModel
from .config import get_config

flags = tf.flags

flags.DEFINE_string(
    "model", "small",
    "A type of model. Possible options are: small, medium, large.")
flags.DEFINE_bool("use_fp16", False,
                  "Train using 16-bit floats instead of 32bit floats")
flags.DEFINE_string("checkpoint_file", None, "file with saved model parameters")
flags.DEFINE_integer('seed', None, "initial word")
flags.DEFINE_integer('n_words', 1, "number of words to generate")

FLAGS = flags.FLAGS


def generate(session, model, seed, n_words, eval_op):
    words = [seed]

    state = session.run(model.initial_state)

    for n in xrange(n_words):
        fetches = [model.cost, model.final_state, model.probabilities, model.logits, eval_op]

        x = np.array([[words[-1]]])

        feed_dict = {
            model.input_data: x,
            model.targets: x,
        }

        for i, (c, h) in enumerate(model.initial_state):
            feed_dict[c] = state[i].c
            feed_dict[h] = state[i].h

        cost, state, probs, logits, _ = session.run(fetches, feed_dict)

        words.append(np.argmax(probs, 1))

    return words


def main(_):
    if FLAGS.checkpoint_file is None:
        raise ValueError("Must set --checkpoint_file")

    if FLAGS.seed is None:
        raise ValueError("Must set --seed")

    eval_config = get_config(FLAGS.model)
    eval_config.batch_size = 1
    eval_config.num_steps = 1

    with tf.Graph().as_default(), tf.Session() as session:
        initializer = tf.random_uniform_initializer(-eval_config.init_scale,
                                                    eval_config.init_scale)

        with tf.variable_scope("model", reuse=None, initializer=initializer):
            model = PTBModel(is_training=False, config=eval_config, use_fp16=FLAGS.use_fp16)
            saver = tf.train.Saver()

        tf.initialize_all_variables().run()

        saver.restore(session, FLAGS.checkpoint_file)
        print "Model parameters restored from disk"

        words = generate(session, model, FLAGS.seed, FLAGS.n_words, tf.no_op())
        print words


if __name__ == "__main__":
    tf.app.run()