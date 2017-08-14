import numpy as np
from keras.optimizers import Adam

from config import *
from data import VRDDataset
from evaluation import *
from model import ReferringRelationshipsModel


def get_subset(idx, data):
    res = []
    for x in data:
        res += [x[idx]]
    return res


# ******************************************* DATA *******************************************
data = VRDDataset()
print("Building VRD dataset...")
subjects_data, relationships_data, objects_data, subjects_bbox, objects_bbox = data.build_dataset()
num_subjects = len(np.unique(subjects_data))
num_predicates = len(np.unique(relationships_data))
num_objects = len(np.unique(objects_data))
# image_data = data.get_images(image_ids)
N = subjects_data.shape[0]
permutation = np.arange(N)
np.random.shuffle(permutation)
train_idx = permutation[:int(N * (1 - validation_split))]
val_idx = permutation[int(N * (1 - validation_split)):]
# training data
train_subjects, train_predicates, train_objects, train_subject_bbox, train_object_bbox = get_subset(
        train_idx,
        [subjects_data, relationships_data, objects_data, subjects_bbox, objects_bbox])
N_train = len(train_idx)
# validation data
val_subjects, val_predicates, val_objects, val_subject_bbox, val_object_bbox = get_subset(
        val_idx, [subjects_data, relationships_data, objects_data, subjects_bbox, objects_bbox])
print("Getting val images...")
val_images = data.get_images(val_idx)
N_val = len(val_idx)

# ************************************* OVERFIT 1 EXAMPLE *************************************
# N = 1
# k = 22
# image_ids = image_ids[k:k + 1]
# image_data = image_data[k:k + 1]
# subjects_data = subjects_data[k:k + 1]
# relationships_data = relationships_data[k:k + 1]
# objects_data = objects_data[k:k + 1]
# subjects_region_data = subjects_region_data[k:k + 1]
# objects_region_data = objects_region_data[k:k + 1]

# ***************************************** TRAINING *****************************************
relationships_model = ReferringRelationshipsModel()
model = relationships_model.build_model()
print(model.summary())
optimizer = Adam(lr=lr)
model.compile(loss=['categorical_crossentropy', 'categorical_crossentropy'], optimizer=optimizer)
# k = 22
# cv2.imwrite(os.path.join('results/2', 'original.png'), train_images[k])
# cv2.imwrite(os.path.join('results/2', 'gt.png'), 255*train_subject_regions[k])
for i in range(epochs):
    s_loss_hist = []
    o_loss_hist = []
    print("Epoch {}/{}".format(i, epochs))
    if (i + 1) % 20 == 0:
        lr /= 2.
        model.optimizer.lr.assign(lr)
    print("learning rate: {}".format(lr))
    for j in range(N_train / batch_size):
        train_batch_image_idx = train_idx[j * batch_size:(j + 1) * batch_size]
        train_images, gt_subject_regions, gt_object_regions = data.get_images_and_regions(train_batch_image_idx)
        _, s_loss, o_loss = model.train_on_batch([train_images, train_subjects[j * batch_size:(j + 1) * batch_size],
                                                  train_predicates[j * batch_size:(j + 1) * batch_size],
                                                  train_objects[j * batch_size:(j + 1) * batch_size]],
                                                 [gt_subject_regions, gt_object_regions])
        s_loss_hist += [s_loss]
        o_loss_hist += [o_loss]
    print("subject loss: {}".format(np.mean(s_loss_hist)))
    print("object loss: {}".format(np.mean(o_loss_hist)))
    # subject_pred, object_pred = model.predict([train_images[k:k+1], train_subjects[k:k+1], train_predicates[k:k+1], train_objects[k:k+1]])
    # visualize_weights(train_images[k], subject_pred, input_dim, i)
    s_iou_mean, s_iou_acc, o_iou_mean, o_iou_acc = evaluate(model, val_images, val_subjects, val_predicates,
                                                            val_objects, val_subject_bbox, val_object_bbox, iou_thresh,
                                                            score_thresh)
    print("subject iou mean : {} \n subject accuracy for iou thresh={} : {}".format(s_iou_mean, iou_thresh, s_iou_acc))
    print("object iou mean : {} \n object accuracy for iou thresh={} : {}".format(o_iou_mean, iou_thresh, o_iou_acc))