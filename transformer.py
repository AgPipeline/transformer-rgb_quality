"""My nifty transformer
"""

import datetime
import logging
import os
from typing import Optional
import numpy as np
import gdal

from terrautils.formats import create_geotiff
import terrautils.lemnatec

import configuration
import transformer_class

terrautils.lemnatec.SENSOR_METADATA_CACHE = os.path.dirname(os.path.realpath(__file__))

# Image filename checking definitions
IMAGE_FILENAME_END = ".tif"


class __internal__:
    """Class for functionality to only be used by this file"""
    def __init__(self):
        """Initializes class instance"""

    @staticmethod
    def get_files_to_process(file_list: list) -> list:
        """Returns the name of the file to load from the list of files
        Arguments:
            file_list: the list of file names to look through
        Return:
            Returns the files that match the searching criteria
        """
        image_files = []
        for one_file in file_list:
            if one_file.endswith(IMAGE_FILENAME_END):
                image_files.append(one_file)
        return image_files

    @staticmethod
    # main function: Multiscale Autocorrelation (MAC)
    def MAC(im1: np.ndarray, im2: np.ndarray, im0: np.ndarray):
        """Calculates the MAC value of the image
        Arguments:
            im1: one image to use for scoring
            im2: one image to use for scoring
            im0: one image to use for scoring
        Return:
            Returns the NRMAC score
        """
        # We disable these checks since the names should be capitalized, and to keep with the original code
        # pylint: disable=invalid-name, consider-using-enumerate
        width, _, channels = im1.shape
        if channels > 1:
            im0 = np.matrix.round(__internal__.rgb2gray(im0))
            im1 = np.matrix.round(__internal__.rgb2gray(im1))
            im2 = np.matrix.round(__internal__.rgb2gray(im2))
        # multiscale parameters
        scales = np.array([2, 3, 5])
        FM = np.zeros(len(scales))
        for scale_index in range(len(scales)):
            im1[0: width-1, :] = im0[1:width, :]
            im2[0: width-scales[scale_index], :] = im0[scales[scale_index]:width, :]
            dif = im0*(im1 - im2)
            FM[scale_index] = np.mean(dif)
        NRMAC = np.mean(FM)
        return NRMAC

    @staticmethod
    def rgb2gray(rgb: np.ndarray) -> np.ndarray:
        """Converts RGB image to greyscale
        Arguments:
            rgb: the image to convert
        Return:
            The grey scale image
        """
        red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        gray = 0.2989 * red + 0.5870 * green + 0.1140 * blue
        return gray

    @staticmethod
    def get_image_quality(imgfile: str):
        """Calculates the quality score for the image
        Arguments:
            imgfile: the path to the image file to score
        Return:
            Returns the image quality score
        """
        # We disable these checks since the names should be capitalized
        # pylint: disable=invalid-name
        # Some RGB Geotiffs have issues with Image library...
        img = np.rollaxis(gdal.Open(imgfile).ReadAsArray().astype(np.uint8), 0, 3)
        NRMAC = __internal__.MAC(img, img, img)
        return NRMAC


def check_continue(transformer: transformer_class.Transformer, check_md: dict, transformer_md: list, full_md: list) -> tuple:
    """Checks if conditions are right for continuing processing
    Arguments:
        transformer: instance of transformer class
        check_md: request specific metadata
        transformer_md: metadata associated with previous runs of the transformer
        full_md: the full set of metadata available to the transformer
    Return:
        Returns a tuple containing the return code for continuing or not, and
        an error message if there's an error
    """
    # pylint: disable=unused-argument
    if not __internal__.get_files_to_process(check_md['list_files']()):
        return -1, "No supported image files were specified for processing"
    return tuple([0])


def perform_process(transformer: transformer_class.Transformer, check_md: dict, transformer_md: list, full_md: list) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
        check_md: request specific metadata
        transformer_md: metadata associated with previous runs of the transformer
        full_md: the full set of metadata available to the transformer
    Return:
        Returns a dictionary with the results of processing
    """
    # pylint: disable=unused-argument
    start_timestamp = datetime.datetime.now()
    all_files = check_md['list_files']()
    total_file_count = len(all_files)
    files_to_process = __internal__.get_files_to_process(all_files)

    file_md = []
    num_image_files = 0
    num_processed_files = 0
    for one_file in files_to_process:
        logging.debug("Processing file: '%s'", one_file)
        num_image_files += 1

        if not os.path.exists(one_file):
            logging.error("Unable to access file: '%s'. Continuing processing", one_file)
            continue

        try:
            quality_value = __internal__.get_image_quality(one_file)
            image_bounds = transformer.get_image_file_geobounds(one_file)
            quality_image_bounds = (image_bounds[2], image_bounds[3], image_bounds[0], image_bounds[1])

            mac_file_name = os.path.join(check_md['working_folder'], os.path.splitext(os.path.basename(one_file))[0] + '_mac.tif')

            logging.info("MAC score %s for file '%s'", str(quality_value), one_file)
            logging.debug("Creating quality image: bounds %s  name: '%s'", str(quality_image_bounds), mac_file_name)
            create_geotiff(np.array([[quality_value, quality_value], [quality_value, quality_value]]), quality_image_bounds,
                           mac_file_name, None, True, transformer.generate_transformer_md(), full_md[0], compress=True)

            num_processed_files += 1
            file_md.append(
                {
                    'path': mac_file_name,
                    'key': 'tif',
                    'metadata': {
                        'replace': True,
                        'data': {
                            'MAC score': str(quality_value),
                            'utc_timestamp': datetime.datetime.utcnow().isoformat(),
                            'source_file': one_file
                        }
                    }
                }
            )
        except Exception as ex:
            logging.warning("Ignoring exception caught processing image file '%s'", one_file)
            logging.debug("Exception: %s", str(ex))
            logging.exception('broken')

    return {'code': 0,
            'files': file_md,
            configuration.TRANSFORMER_NAME: {
                'version': configuration.TRANSFORMER_VERSION,
                'utc_timestamp': datetime.datetime.utcnow().isoformat(),
                'processing_time': str(datetime.datetime.now() - start_timestamp),
                'num_files_received': str(total_file_count),
                'num_image_files': str(num_image_files),
                'num_processed_files': str(num_processed_files)
            }
            }
