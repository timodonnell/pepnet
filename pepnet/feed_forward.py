# Copyright (c) 2017. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (
    print_function,
    division,
    absolute_import,
)

from keras.models import Sequential
from keras.layers.core import Dense, Activation, Flatten, Dropout
from keras.layers.embeddings import Embedding
from keras.layers.normalization import BatchNormalization
from keras.layers import SpatialDropout1D

def _build_layers(
        model,
        input_size,
        layer_sizes,
        activation,
        output_size,
        output_activation,
        init,
        batch_normalization,
        dropout):
    layer_sizes = (input_size,) + tuple(layer_sizes)
    for i, dim in enumerate(layer_sizes):
        if i == 0:
            # input is only conceptually a layer of the network,
            # don't need to actually do anything
            continue

        previous_dim = layer_sizes[i - 1]

        # hidden layer fully connected layer
        model.add(
            Dense(
                units=dim,
                input_dim=previous_dim,
                kernel_initializer=init))
        model.add(Activation(activation))

        if batch_normalization:
            model.add(BatchNormalization())

        if dropout > 0:
            model.add(Dropout(dropout))

    # add final layer
    model.add(Dense(
        units=output_size,
        input_dim=layer_sizes[-1],
        kernel_initializer=init))
    model.add(Activation(output_activation))
    return model

def make_fixed_length_feedforward_network(
        input_size,
        output_size=1,
        embedding_input_dim=None,
        embedding_output_dim=None,
        layer_sizes=[100],
        activation="tanh",
        init="glorot_uniform",
        output_activation="sigmoid",
        dropout=0.0,
        embedding_dropout=0.0,
        batch_normalization=True,
        initial_embedding_weights=None,
        embedding_init_method="glorot_uniform",
        model=None,
        optimizer="rmsprop",
        loss="mse"):

    if model is None:
        model = Sequential()

    if embedding_input_dim:
        if not embedding_output_dim:
            raise ValueError(
                "Both embedding_input_dim and embedding_output_dim must be "
                "set")

        if initial_embedding_weights:
            n_rows, n_cols = initial_embedding_weights.shape
            if n_rows != embedding_input_dim or n_cols != embedding_output_dim:
                raise ValueError(
                    "Wrong shape for embedding: expected (%d, %d) but got "
                    "(%d, %d)" % (
                        embedding_input_dim, embedding_output_dim,
                        n_rows, n_cols))
            model.add(Embedding(
                input_dim=embedding_input_dim,
                output_dim=embedding_output_dim,
                input_length=input_size,
                weights=[initial_embedding_weights]))
        else:
            model.add(Embedding(
                input_dim=embedding_input_dim,
                output_dim=embedding_output_dim,
                input_length=input_size,
                embeddings_initializer=embedding_init_method))

        if embedding_dropout:
            model.add(SpatialDropout1D(embedding_dropout))

        model.add(Flatten())

        input_size = input_size * embedding_output_dim

    model = _build_layers(
        model=model,
        input_size=input_size,
        layer_sizes=layer_sizes,
        activation=activation,
        output_size=output_size,
        output_activation=output_activation,
        init=init,
        batch_normalization=batch_normalization,
        dropout=dropout)

    model.compile(loss=loss, optimizer=optimizer)
    return model


def make_fixed_length_hotshot_network(
        peptide_length=9,
        n_symbols=20,
        **kwargs):
    """
    Construct a feed-forward neural network whose inputs are binary vectors
    representing a "one-hot" or "hot-shot" encoding of a fixed length amino
    acid sequence.
    """
    return make_fixed_length_feedforward_network(
        input_size=peptide_length * n_symbols,
        **kwargs)


def make_fixed_length_embedding_network(
        peptide_length=9,
        n_symbols=20,
        embedding_output_dim=20,
        **kwargs):
    """
    Construct a feed-forward neural network whose inputs are vectors of integer
    indices.
    """
    return make_fixed_length_feedforward_network(
        input_size=peptide_length,
        embedding_input_dim=n_symbols,
        embedding_output_dim=embedding_output_dim,
        **kwargs)
