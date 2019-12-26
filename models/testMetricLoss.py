from HeterogeneousGraph import HAN
import tensorflow as tf
from models.MetrlcLoss import OSM_CAA_Loss


name = "hongbin_li"
lr = 0.01  # learning rate
l2_coef = 0.0001  # weight decay

han = HAN.HAN()
features, labels, pids, rawlabels = han.loadFeature(name)
nb_node = features.shape[0]
feature_size = features.shape[1]
nb_class = len(set(rawlabels))

print ("res: ", features)
print ("n_nodes: ", features.shape[0])


def buildModel():
    ftr_input = tf.placeholder("float", [None, 100])
    D1 = tf.layers.dense(ftr_input, 100, activation=tf.nn.sigmoid)
    D2 =  tf.layers.dense(D1, 100, activation=tf.nn.sigmoid)
    D3 =  tf.layers.dense(D2, 100, activation=tf.nn.sigmoid)
    return D3


def getCenters(num_classes, feature_size, labels, final_embed):
    # INF
    INF = 99999.0

    # this is wrong
    # centers = tf.zeros(shape=[num_classes, feature_size], dtype=tf.float32)
    # test
    centers = tf.Variable(tf.zeros([num_classes, feature_size]), dtype=tf.float32, name='centers')
    centers_count = tf.Variable(tf.zeros([num_classes, 1]), dtype=tf.float32, name='centers_count')
    # centers_count = centers_count + 1

    labels = tf.reshape(labels, [-1])

    # appear_times
    unique_label, unique_idx, unique_count = tf.unique_with_counts(labels)
    appear_times = tf.gather(unique_count, unique_idx)
    appear_times = tf.reshape(appear_times, [-1, 1])
    appear_times = tf.cast(appear_times, tf.float32)

    centers = tf.scatter_add(centers, labels, final_embed)
    centers_count = tf.scatter_add(centers_count, labels, appear_times)
    centers_count = tf.clip_by_value(centers_count, clip_value_min=tf.constant(1.0, dtype=tf.float32),
                                     clip_value_max=tf.constant(INF, dtype=tf.float32))

    # centers = centers * centers_count
    centers = centers / centers_count
    centers = tf.transpose(centers)

    return centers

def GetLoss(final_embedding, nb_nodes, centers_embed):
    osm_caa_loss = OSM_CAA_Loss(batch_size=nb_nodes)
    osm_loss = osm_caa_loss.forward
    osmLoss, checkvalue = osm_loss(final_embedding, rawlabels, centers_embed)
    return osmLoss

def masked_accuracy(logits, labels, mask):
    """Accuracy with masking."""
    correct_prediction = tf.equal(
        tf.argmax(logits, 1), tf.argmax(labels, 1))
    accuracy_all = tf.cast(correct_prediction, tf.float32)
    mask = tf.cast(mask, dtype=tf.float32)
    mask /= tf.reduce_mean(mask)
    accuracy_all *= mask
    return tf.reduce_mean(accuracy_all)

def training(loss, lr, l2_coef):
    # weight decay
    vars = tf.trainable_variables()
    lossL2 = tf.add_n([tf.nn.l2_loss(v) for v in vars if v.name not
                       in ['bias', 'gamma', 'b', 'g', 'beta']]) * l2_coef

    # optimizer
    opt = tf.train.AdamOptimizer(learning_rate=lr)

    # training op
    train_op = opt.minimize(loss + lossL2)

    return train_op


final_embed = buildModel()
centers = getCenters(nb_class, feature_size, rawlabels, final_embed)
loss = GetLoss(final_embed, nb_nodes=nb_node, centers_embed=centers)
train_op = training(loss,lr, l2_coef)



