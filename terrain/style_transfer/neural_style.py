import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications import vgg19
import os


def load_image(img_path, target_shape):
    img = keras.preprocessing.image.load_img(img_path, target_size=target_shape)
    img = keras.preprocessing.image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return tf.convert_to_tensor(img, dtype=tf.float32)


def tensor_to_image(x, target_shape):
    x = x.reshape((target_shape[0], target_shape[1], 3))
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    x = x[:, :, ::-1]
    x = np.clip(x, 0, 255).astype("uint8")
    return x


def gram_matrix(x):
    x = tf.transpose(x, (2, 0, 1))
    features = tf.reshape(x, (tf.shape(x)[0], -1))
    gram = tf.matmul(features, tf.transpose(features))
    return gram


def style_loss(style, combination, img_nrows, img_ncols):
    S = gram_matrix(style)
    C = gram_matrix(combination)
    channels = 3
    size = img_nrows * img_ncols
    return tf.reduce_sum(tf.square(S - C)) / (4.0 * (channels ** 2) * (size ** 2))


def content_loss(base, combination):
    return tf.reduce_sum(tf.square(combination - base))


def total_variation_loss(x, img_nrows, img_ncols):
    a = tf.square(
        x[:, : img_nrows - 1, : img_ncols - 1, :] - x[:, 1:, : img_ncols - 1, :]
    )
    b = tf.square(
        x[:, : img_nrows - 1, : img_ncols - 1, :] - x[:, : img_nrows - 1, 1:, :]
    )
    return tf.reduce_sum(tf.pow(a + b, 1.25))


def compute_loss(combination_image, base_image, style_reference_image, feature_extractor, content_layer_name, style_layer_names, content_weight, style_weight, tv_weight, img_nrows, img_ncols):
    input_tensor = tf.concat(
        [base_image, style_reference_image, combination_image], axis=0
    )
    features = feature_extractor(input_tensor)
    loss = tf.zeros(shape=())

    # Content loss
    layer_features = features[content_layer_name]
    base_image_features = layer_features[0, :, :, :]
    combination_features = layer_features[2, :, :, :]
    loss = loss + content_weight * content_loss(
        base_image_features, combination_features
    )

    # Style loss
    for layer_name in style_layer_names:
        layer_features = features[layer_name]
        style_reference_features = layer_features[1, :, :, :]
        combination_features = layer_features[2, :, :, :]
        sl = style_loss(style_reference_features, combination_features, img_nrows, img_ncols)
        loss += (style_weight / len(style_layer_names)) * sl

    # Total variation loss
    loss += tv_weight * total_variation_loss(combination_image, img_nrows, img_ncols)
    return loss

@tf.function
def compute_loss_and_grads(combination_image, base_image, style_reference_image, feature_extractor, content_layer_name, style_layer_names, content_weight, style_weight, tv_weight, img_nrows, img_ncols):
    with tf.GradientTape() as tape:
        loss = compute_loss(
            combination_image, base_image, style_reference_image, feature_extractor,
            content_layer_name, style_layer_names, content_weight, style_weight, tv_weight, img_nrows, img_ncols
        )
    grads = tape.gradient(loss, combination_image)
    return loss, grads


def apply_neural_style(content_path, style_path, num_steps=2000, style_weight=1e-5, content_weight=2.5e-11, tv_weight=1e-10, img_nrows=512, result_prefix="outputs/transferred_morphology", progress_callback=None):
    """
    Apply neural style transfer to a procedural terrain map using a real-world heightmap as style, using TensorFlow/Keras VGG-19.
    Args:
        content_img: np.ndarray or PIL.Image, procedural noise map
        style_img: np.ndarray or PIL.Image, real-world heightmap
        num_steps: int, number of optimization steps
        style_weight: float, beta in the paper
        content_weight: float, alpha in the paper
        tv_weight: float, gamma in the paper
        img_nrows, img_ncols: target image size
        result_prefix: prefix for saved outputs
    Returns:
        Stylized terrain as np.ndarray
    """
    # Preprocess images    

    width, height = keras.preprocessing.image.load_img(content_path).size
    img_ncols = width * img_nrows // height

    target_shape = (img_nrows, img_ncols)

    base_image = load_image(content_path, target_shape)
    style_reference_image = load_image(style_path, target_shape)
    combination_image = tf.Variable(load_image(content_path, target_shape))

    # Build VGG19 model for feature extraction
    model = vgg19.VGG19(weights="imagenet", include_top=False)
    outputs_dict = dict([(layer.name, layer.output) for layer in model.layers])
    feature_extractor = keras.Model(inputs=model.inputs, outputs=outputs_dict)

    # Style and content layers
    style_layer_names = [
        "block1_conv1",
        "block2_conv1",
        "block3_conv1",
        "block4_conv1",
        "block5_conv1"
    ]
    content_layer_name = "block5_conv2"

    # Optimizer
    optimizer = keras.optimizers.legacy.SGD(
        keras.optimizers.schedules.ExponentialDecay(
            initial_learning_rate=150.0, decay_steps=100, decay_rate=0.96
        )
    )

    for i in range(1, num_steps + 1):
        loss, grads = compute_loss_and_grads(
            combination_image, base_image, style_reference_image, feature_extractor,
            content_layer_name, style_layer_names, content_weight, style_weight, tv_weight, img_nrows, img_ncols
        )
        optimizer.apply_gradients([(grads, combination_image)])

        if progress_callback:
            pct = int(i / num_steps * 100)
            progress_callback(pct)
    return tensor_to_image(combination_image.numpy(), target_shape)
