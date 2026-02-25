from celery import Celery
import docker
import shlex
from docker.types import Mount
import os
import stat
from celery import shared_task


celery_app = Celery(
    "celery_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

OWASP_UID = 1000
OWASP_GID = 1000

celery_app.autodiscover_tasks()

def prepare_project_paths(project_id):
    base_path = f"grepmarx_gpx-data/projects/{project_id}"
    extract_path = os.path.join(base_path, "extract")
    reports_path = os.path.join(base_path, "reports")

    for path in [extract_path, reports_path]:
        os.makedirs(path, exist_ok=True)
        
        os.chown(path, OWASP_UID, OWASP_GID)
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    return extract_path, reports_path

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    os.chown(path, OWASP_UID, OWASP_GID)
    os.chmod(path, 0o755)

@celery_app.task(name="worker.run_depscan")
@shared_task
def run_depscan(project_id):

    print("DEPSCAN LAUNCHED ----------------------------------")
    # client = docker.from_env()
    client = docker.APIClient(base_url='unix://var/run/docker.sock')
    
    # source_path, reports_path = prepare_project_paths(project_id)

    # ensure_dir(source_path)
    # ensure_dir(reports_path)

    # print("Source :" + source_path)
    # print("reports :" + reports_path)

    source_path = os.path.expanduser(
    f"~/.local/share/grepmarx/data/projects/{project_id}"
    )

    DATA_PATH = os.getenv("GREPMARX_DATA_PATH")
    container = client.create_container(
    image="depscan-worker",
    command=[
        "-i", "/scan/target",
        "-o", "/scan/reports",
        "--no-banner",
        "--no-vuln-table",
    ],
    user="0:0",
    volumes=['/scan/target', '/scan/reports'],
    host_config=client.create_host_config(binds={
        f'{DATA_PATH}/projects/{project_id}': {
            'bind': '/scan/target',
            'mode': 'ro',
        },
        f'{DATA_PATH}/projects/{project_id}/reports': {
            'bind': '/scan/reports',
            'mode': 'rw',
        },
    }),
    #  volumes=[ f"{DATA_PATH}/projects/{project_id}:/scan/target"],
    # volumes={
    #     "~/.local/share/grepmarx/projects/{project_id}": {
    #         "bind": f"/scan/target",
    #         "mode": "ro",
    #     },
    # reports_path : {
    #     "bind": "/scan/reports",
    #     "mode": "rw",
    # },
    # },
    )
    client.start(container=container.get("Id"))
    client.wait(container=container.get("Id"))
    logs = client.logs(container=container.get("Id"))
    print("TOTO ----------------------------------")
    print(logs.decode())

    client.remove_container(container=container.get("Id"))
    return f"{DATA_PATH}/projects/{project_id}/reports/sbom-universal.cdx.json"

@celery_app.task(name="worker.run_test")
@shared_task
def run_test():
    print("SUPET MEGA TEST WORKER -------------------------------")
    return