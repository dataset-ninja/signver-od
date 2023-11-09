import supervisely as sly
import ast
import os, csv
from collections import defaultdict
from dataset_tools.convert import unpack_if_archive
import src.settings as s
from urllib.parse import unquote, urlparse
from supervisely.io.fs import get_file_name, get_file_name_with_ext
import shutil

from tqdm import tqdm

def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:        
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path
    
def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count
    
def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    
    images_path = os.path.join("SignverOD","images")
    image_ids_path = os.path.join("SignverOD","image_ids.csv")
    train_split_data_path = os.path.join("SignverOD","train.csv")
    test_split_data_path = os.path.join("SignverOD","test.csv")
    batch_size = 30

    ds_name_to_split = {"train": train_split_data_path, "test": test_split_data_path}


    def create_ann(image_path):
        labels = []

        im_name = get_file_name_with_ext(image_path)

        img_height = int(im_id_to_shape[im_name][0])
        img_wight = int(im_id_to_shape[im_name][1])

        ann_data = name_to_data[im_name]

        for curr_ann_data in ann_data:
            obj_class = idx_to_class[curr_ann_data[0]]
            area_value = curr_ann_data[2]
            area = sly.Tag(area_meta, value=area_value)
            coords = ast.literal_eval(str(curr_ann_data[1]))

            left = int(coords[0] * img_wight)
            right = int((coords[0] + coords[2]) * img_wight)
            top = int(coords[1] * img_height)
            bottom = int((coords[1] + coords[3]) * img_height)
            rectangle = sly.Rectangle(top=top, left=left, bottom=bottom, right=right)
            label = sly.Label(rectangle, obj_class, tags=[area])
            labels.append(label)

        return sly.Annotation(img_size=(img_height, img_wight), labels=labels)


    signature = sly.ObjClass("signature", sly.Rectangle)
    initials = sly.ObjClass("initials", sly.Rectangle)
    redaction = sly.ObjClass("redaction", sly.Rectangle)
    date = sly.ObjClass("date", sly.Rectangle)

    area_meta = sly.TagMeta("area", sly.TagValueType.ANY_NUMBER)

    idx_to_class = {"1": signature, "2": initials, "3": redaction, "4": date}

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(obj_classes=list(idx_to_class.values()), tag_metas=[area_meta])
    api.project.update_meta(project.id, meta.to_json())
    incr_id = 2133
    last_id = 0
    im_id_to_name = {}
    im_id_to_shape = {}
    with open(image_ids_path, "r") as file:
        csvreader = csv.reader(file)
        for idx, row in enumerate(csvreader):
            if idx == 0:
                continue
            curr_id = int(row[2])
            if curr_id < last_id:
                new_id = curr_id + incr_id
            else:
                new_id = curr_id
            last_id = new_id
            im_id_to_name[str(new_id)] = row[3]
            im_id_to_shape[row[3]] = (float(row[0]), float(row[1]))

    used_images = []
    dublicates = []
    for ds_name, split_path in ds_name_to_split.items():
        dataset = api.dataset.create(project.id, ds_name, change_name_if_conflict=True)
        last_id = 0
        name_to_data = defaultdict(list)
        with open(split_path, "r") as file:
            csvreader = csv.reader(file)
            for idx, row in enumerate(csvreader):
                if idx == 0:
                    continue
                curr_id = int(row[4])
                if curr_id < last_id:
                    new_id = curr_id + incr_id
                else:
                    new_id = curr_id
                last_id = new_id
                im_name = im_id_to_name[str(new_id)]
                name_to_data[im_name].append([row[2], row[1], float(row[0])])

        images_names = list(name_to_data.keys())
        if ds_name == "train":
            used_images = images_names
        progress = sly.Progress("Create dataset {}".format(ds_name), len(images_names))
        if ds_name == "test":
            dublicates = [img for img in images_names if img in used_images]
            images_names = [img for img in images_names if img not in used_images]
        for images_names_batch in sly.batched(images_names, batch_size=batch_size):
            img_pathes_batch = [
                os.path.join(images_path, image_name) for image_name in images_names_batch
            ]

            img_infos = api.image.upload_paths(dataset.id, images_names_batch, img_pathes_batch)
            img_ids = [im_info.id for im_info in img_infos]

            anns = [create_ann(image_path) for image_path in img_pathes_batch]
            api.annotation.upload_anns(img_ids, anns)

            progress.iters_done_report(len(images_names_batch))

    return project
