"""Module to handle docker.io registry."""
from udocker.container import localrepo
from udocker.docker import DockerIoAPI

doia = DockerIoAPI(localrepo.LocalRepository())
default_registry = doia.registry_url


def manifest(imagerepo, tag):
    """Return the manifest of an image."""
    try:
        (imagerepo, remoterepo) = doia._parse_imagerepo(imagerepo)
        (hdr_data, manifest) = doia.get_v2_image_manifest(remoterepo, tag)
        status = doia.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
    except Exception as err:  # noqa B902
        raise err from err  # Forward the exception, but reset registry
    finally:
        doia.set_registry(default_registry)
    if status == 200:
        return manifest
    elif status == 401:
        raise Exception("Error: not authorized")
    elif status == 404:
        raise Exception("Error: manifest not found")
    else:
        raise Exception("Error: pulling manifest")
