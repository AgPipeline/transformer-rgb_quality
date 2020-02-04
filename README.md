# Transformer: RGB Quality scoring

Generates a quality score for image files.

### Sample Docker Command Line

Below is a sample command line that shows how the imaage scoring Docker image could be run.
An explanation of the command line options used follows.
Be sure to read up on the [docker run](https://docs.docker.com/engine/reference/run/) command line for more information.

The files used in this sample command line can be found on [Google Drive](https://drive.google.com/file/d/1n4bZjawjYIp40gf4CaH1UegOOyiaUeOa/view?usp=sharing).

```sh
docker run --rm --mount "src=/home/test,target=/mnt,type=bind" agpipeline/rgb_quality:2.0 --working_space "/mnt" --metadata /mnt/b7d9aefd-c8f8-4de6-8758-6af96bb7644e_metadata_cleaned.json "/mnt/rgb_geotiff_L1_ua-mac_2018-02-01__10-40-01-576_left.tif"
```

This example command line assumes the source files are located in the `/home/test` folder of the local machine.
The name of the image to run is `agpipeline/rgb_quality:2.0`.

We are using the same folder for the source files and the output files.
By using multiple `--mount` options, the source and output files can be separated.

**Docker commands** \
Everything between 'docker' and the name of the image are docker commands.

- `run` indicates we want to run an image
- `--rm` automatically delete the image instance after it's run
- `--mount "src=/home/test,target=/mnt,type=bind"` mounts the `/home/test` folder to the `/mnt` folder of the running image

We mount the `/home/test` folder to the running image to make files available to the software in the image.

**Image's commands** \
The command line parameters after the Docker image name are passed to the software inside the image.
Note that the paths provided are relative to the running image (see the --mount option specified above).

- `--working_space "/mnt"` specifies the folder to use as a workspace
- `--metadata "/mnt/b7d9aefd-c8f8-4de6-8758-6af96bb7644e_metadata_cleaned.json"` is the name of the source metadata
- `"/mnt/rgb_geotiff_L1_ua-mac_2018-02-01__10-40-01-576_left.tif"` is the name of an image to generate a score from
