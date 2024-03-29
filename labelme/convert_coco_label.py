import base64
import contextlib
import io
import json
import os
import os.path as osp
import copy

from labelme import __version__
from labelme.logger import logger
from labelme import PY2
from labelme.utils.qt import LogPrint

@contextlib.contextmanager
def open(name, mode):
    assert mode in ["r", "w"]
    if PY2:
        mode += "b"
        encoding = None
    else:
        encoding = "utf-8"
    yield io.open(name, mode, encoding=encoding)
    return


class CoCoFileError(Exception):
    pass


class ConvertCoCOLabel(object):
    suffix = "_coco.json"

    def __init__(self, cocofilename=None, labelfilename=None):
        self.shapes = []
        self.imagePath = None
        self.imageData = None
        self.imageHeight = 0
        self.imageWidth = 0
        self.version = None
        self.cocofilename = cocofilename
        self.labelfilename = labelfilename
        if cocofilename is not None:
            self.load(self.cocofilename)

    def load(self, filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            version = data.get("version")
            if version is None:
                self.version = __version__
            elif version.split(".")[0] != __version__.split(".")[0]:
                logger.warn(
                    "This JSON file ({}) may be incompatible with "
                    "current labelme. version in file: {}, "
                    "current version: {}".format(
                        filename, version, __version__
                    )
                )

            for info in data.get("images"):
                self.imagePath = info["file_name"]
                self.imageHeight = info["height"]
                self.imageWidth = info["width"]

            categories = data.get("categories")
            for cate in categories:
                shape = {}
                shape["grade"] = cate["supercategory"]
                shape["label"] = cate["name"]
                shape["label_display"] = "{}-{}".format(cate["supercategory"], cate["name"])
                shape["color"] = cate["color"] if "color" in cate else "#808000"
                shape["points"] = []
                shape["lineweight"] = cate["lineweight"] if "lineweight" in cate else "2.0"
                shape["shape_type"] = cate["shape_type"] if "shape_type" in cate else "line"
                shape["group_id"] = None
                shape["category_id"] = cate["id"]
                self.shapes.append(shape)

            annotations = data.get("annotations")
            for anno in annotations:
                cate_id = int(anno["id"]) - 1
                shape = self.getShapeByCategoryID(cate_id)
                if shape:
                    stype = shape["shape_type"]
                    segmentation = anno["segmentation"][0]
                    if hasattr(segmentation, "__len__"):
                        list_len = len(segmentation) / 2
                    else:
                        # LogPrint(self.cocofilename + "에서 segmentation 는 배열이여야 합니다.")
                        segmentation = anno["segmentation"]
                        list_len = len(segmentation) / 2

                    ii = 0
                    i = 0
                    while i < list_len:
                        one = segmentation[ii]
                        two = segmentation[ii + 1]
                        point = [one, two]
                        shape["points"].append(point)
                        ii = ii + 2
                        i = i + 1

                    """
                    if stype == "polygon":
                        segmentation = anno["segmentation"][0]
                        list_len = len(float(segmentation)) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    elif stype == "rectangle":
                        segmentation = anno["segmentation"][0]
                        list_len = len(segmentation) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    elif stype == "circle":
                        segmentation = anno["segmentation"][0]
                        list_len = len(segmentation) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    elif stype == "line":
                        segmentation = anno["segmentation"][0]
                        list_len = len(segmentation) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    elif stype == "linestrip":
                        segmentation = anno["segmentation"][0]
                        list_len = len(segmentation) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    else:  # default line
                        segmentation = anno["segmentation"][0]
                        list_len = len(segmentation) / 2
                        ii = 0
                        i = 0
                        while i < list_len:
                            one = segmentation[ii]
                            two = segmentation[ii + 1]
                            point = [one, two]
                            shape["points"].append(point)
                            ii = ii + 2
                            i = i + 1
                    """

        except Exception as e:
            LogPrint("coco 파일이 정확하지 않습니다 : %s" % e)
            pass
            #raise CoCoFileError(e)


    def getShapeByCategoryID(self, cid):
        for shape in self.shapes:
            if int(shape["category_id"]) == cid:
                return shape

        return None


    def save(self):
        for sp in self.shapes:
            del sp["category_id"]

        data = dict(
            version=self.version,
            shapes=self.shapes,
            imagePath=self.imagePath,
            imageData=self.imageData,
            imageHeight=self.imageHeight,
            imageWidth=self.imageWidth,
        )
        try:
            if osp.dirname(self.labelfilename) and not osp.exists(osp.dirname(self.labelfilename)):
                os.makedirs(osp.dirname(self.labelfilename))

            with open(self.labelfilename, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.shapes.clear()
            self.imagePath = None
            self.imageData = None
            self.imageHeight = 0
            self.imageWidth = 0
            self.version = None
            self.cocofilename = None
            lfname = copy.deepcopy(self.labelfilename)
            self.labelfilename = None
            return lfname
        except Exception as e:
            LogPrint("코코파일을 라벨파일로 변환중 오류 %s" % e)
            pass
            # raise CoCoFileError(e)
        return ""

    @staticmethod
    def is_coco_file(filename):
        loustr = filename.lower()
        # fd = loustr.rfind(ConvertCoCOLabel.suffix)
        return loustr.endswith(ConvertCoCOLabel.suffix)