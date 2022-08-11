from udocker.docker import DockerIoAPI
from udocker.container import localrepo

doia = DockerIoAPI(localrepo.LocalRepository())
default_registry = doia.registry_url


def manifest(imagerepo, tag):
    try:
        (imagerepo, remoterepo) = doia._parse_imagerepo(imagerepo)
        (hdr_data, manifest) = doia.get_v2_image_manifest(remoterepo, tag)
        status = doia.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
    except Exception as err:
        raise err  # Forward the exception, but reset registry
    finally:
        doia.set_registry(default_registry)
    if status != 200:
        raise Exception("Error: pulling manifest")
    if status == 401:
        raise Exception("Error: not authorized")
    if status == 404:
        raise Exception("Error: manifest not found")
    return manifest
