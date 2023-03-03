import os
import os.path as osp
import argparse
import json

from labelme import utils
import numpy as np
import glob
import PIL.Image
from labelme.utils.qt import LogPrint


class labelme2coco(object):
    def __init__(self, labelme_json=[], save_json_path="./lbcoco.json", shape_item=[]):
        """
        :param labelme_json: the list of all labelme json file paths
        :param save_json_path: the path to save new json
        """
        self.labelme_json = labelme_json
        self.save_json_path = save_json_path
        self.shape_list = shape_item
        self.images = []
        self.categories = []
        self.annotations = []
        self.label = []
        self.annID = 1
        self.height = 0
        self.width = 0

        self.save_json()

    def data_transfer_new_way(self):    #after i must this away
        try:
            if len(self.shape_list) == 0:
                for num, json_file in enumerate(self.labelme_json):
                    with open(json_file, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        self.images.append(self.image(data, num))
                        for shapes in data["shapes"]:
                            label = shapes["label"]
                            grade = shapes["grade"]
                            self.label.append(label)
                            color = shapes["color"]
                            lineweight = shapes["lineweight"]
                            shape_type = shapes["shape_type"]
                            self.categories.append(self.category(grade, label, color, lineweight, shape_type))
                            points = shapes["points"]
                            self.annotations.append(self.annotation(points, label, num))
                            self.annID += 1
                for annotation in self.annotations:
                    annotation["category_id"] = self.getcatid(annotation["category_id"])
            else:
                num = 0
                #if self.imagePath.find("meta/") > -1:
                #    self.imagePath = self.imagePath.replace("meta/", "")
                #self.images.append(self.image(data, num)) #후에
                for s in self.shape_list:
                    label = s.label.encode("utf-8") if PY2 else s.label
                    grade = s.grade.encode("utf-8") if PY2 else s.grade
                    self.label.append(label)
                    cColor = QtGui.QColor(s.color if s.color else "#808000")
                    color = cColor.name(QtGui.QColor.HexArgb)
                    lineweight = s.lineweight if s.lineweight else "2.0"
                    plen = len(s.points)
                    if plen == 1:
                        s.shape_type = "point"
                    shape_type = s.shape_type
                    self.categories.append(self.category(grade, label, color, lineweight, shape_type))
                    points = s.points
                    self.annotations.append(self.annotation(points, label, num))
                    self.annID += 1
                for annotation in self.annotations:
                    annotation["category_id"] = self.getcatid(annotation["category_id"])
        except Exception as e:
            LogPrint("data_transfer of labelme2coco :: %s" % e)
            pass

    def data_transfer(self):
        try:
            for num, json_file in enumerate(self.labelme_json):
                with open(json_file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    self.images.append(self.image(data, num))
                    for shapes in data["shapes"]:
                        label = shapes["label"]
                        grade = shapes["grade"]
                        #if label not in self.label: ckd  This delete equal labels
                        #    self.label.append(label)
                        self.label.append(label)
                        color = shapes["color"]
                        lineweight = shapes["lineweight"]
                        shape_type = shapes["shape_type"]
                        self.categories.append(self.category(grade, label, color, lineweight, shape_type))
                        points = shapes["points"]
                        self.annotations.append(self.annotation(points, label, num))
                        self.annID += 1

            # Sort all text labels so they are in the same order across data splits.
            #self.label.sort()
            #for label in self.label:
            #    self.categories.append(self.category(label))
            for annotation in self.annotations:
                annotation["category_id"] = self.getcatid(annotation["category_id"])
        except Exception as e:
            LogPrint("data_transfer of labelme2coco :: %s" % e)
            pass

    def data_transfer_org(self):
        for num, json_file in enumerate(self.labelme_json):
            with open(json_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                self.images.append(self.image(data, num))
                for shapes in data["shapes"]:
                    label = shapes["label"].split("_")
                    # if label not in self.label: ckd  This delete equal labels
                    #    self.label.append(label)
                    self.label.append(label)
                    points = shapes["points"]
                    self.annotations.append(self.annotation(points, label, num))
                    self.annID += 1

        # Sort all text labels so they are in the same order across data splits.
        self.label.sort()
        for label in self.label:
            self.categories.append(self.category(label))
        for annotation in self.annotations:
            annotation["category_id"] = self.getcatid(annotation["category_id"])

    def image(self, data, num):
        image = {}
        height = 0
        width = 0
        try:
            if data["imageData"]:
                img = utils.img_b64_to_arr(data["imageData"])
                height, width = img.shape[:2]
            else:
                height = data["imageHeight"]
                width = data["imageWidth"]

            image["height"] = height
            image["width"] = width
            image["id"] = num
            image["file_name"] = data["imagePath"].split("/")[-1]
        except Exception as e:
            LogPrint("image of labelme2coco  : %s" % e)
            pass

        self.height = height
        self.width = width

        return image

    def category_org(self, label):
        category = {}
        category["supercategory"] = label[0]
        category["id"] = len(self.categories)
        category["name"] = label[0]
        return category

    def category(self, grade, label, color, lineweight, shape_type):
        category = {}
        category["supercategory"] = grade
        category["id"] = len(self.categories)
        category["name"] = label
        category["color"] = color
        category["lineweight"] = lineweight
        category["shape_type"] = shape_type
        return category

    def annotation(self, points, label, num):
        try:
            annotation = {}
            contour = np.array(points)
            x = contour[:, 0]
            y = contour[:, 1]
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            annotation["segmentation"] = [list(np.asarray(points).flatten())]
            annotation["iscrowd"] = 0
            annotation["area"] = area
            annotation["image_id"] = num

            annotation["bbox"] = list(map(float, self.getbbox(points)))

            annotation["category_id"] = label  # self.getcatid(label)
            annotation["id"] = self.annID
            return annotation
        except Exception as e:
            LogPrint("annotation of labelme2coco  : %s" % e)
            pass

    def getcatid(self, label):
        try:
            for category in self.categories:
                if label == category["name"]:
                    return category["id"]
            #print("label: {} not in categories: {}.".format(label, self.categories))
            #exit()
        except Exception as e:
            LogPrint("getcatid of labelme2coco  : %s" % e)
            pass
        return -1

    def getbbox(self, points):
        polygons = points
        mask = self.polygons_to_mask([self.height, self.width], polygons)
        return self.mask2box(mask)

    def mask2box(self, mask):

        index = np.argwhere(mask == 1)
        rows = index[:, 0]
        clos = index[:, 1]

        left_top_r = np.min(rows)  # y
        left_top_c = np.min(clos)  # x

        right_bottom_r = np.max(rows)
        right_bottom_c = np.max(clos)

        return [
            left_top_c,
            left_top_r,
            right_bottom_c - left_top_c,
            right_bottom_r - left_top_r,
        ]

    def polygons_to_mask(self, img_shape, polygons):
        try:
            mask = np.zeros(img_shape, dtype=np.uint8)
            mask = PIL.Image.fromarray(mask)
            xy = list(map(tuple, polygons))
            if len(polygons) == 1:  # add ckd
                PIL.ImageDraw.Draw(mask).point(xy=xy, fill=1)
            else:
                PIL.ImageDraw.Draw(mask).polygon(xy=xy, outline=1, fill=1)
            mask = np.array(mask, dtype=bool)
            return mask
        except Exception as e:
            LogPrint("polygons_to_mask of labelme2coco  : %s" % e)
            pass

    def data2coco(self):
        data_coco = {}
        data_coco["images"] = self.images
        data_coco["categories"] = self.categories
        data_coco["annotations"] = self.annotations
        return data_coco

    def save_json(self):
        try:
            self.data_transfer()
            self.data_coco = self.data2coco()
            if not osp.exists(self.save_json_path):
                os.makedirs(
                    os.path.dirname(os.path.abspath(self.save_json_path)), exist_ok=True
                )
            ##json.dump(self.data_coco, open(self.save_json_path, "w"), indent=4)
            json.dump(self.data_coco, open(self.save_json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
        except Exception as e:
            LogPrint("코코스 파일 덤프중 오류  : %s" % e)
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="labelme annotation to coco data json file."
    )
    parser.add_argument(
        "labelme_images",
        help="Directory to labelme images and annotation json files.",
        type=str,
    )
    parser.add_argument(
        "--output", help="Output json file path.", default="trainval.json"
    )
    args = parser.parse_args()
    labelme_json = glob.glob(os.path.join(args.labelme_images, "*.json"))
    labelme2coco(labelme_json, args.output)