from celery import Celery
import docker
import shlex
from docker.types import Mount

celery_app = Celery(
    "celery_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

@celery_app.task
def run_depscan(depscan_cmd, source_path):
    client = docker.from_env()

    command = [
        "-i", "/scan/target",
        "-o", "/scan/reports",
        "--no-banner",
        "--no-vuln-table",
    ]

    container = client.containers.run(
        image="depscan-worker",
        command=command,
        mounts=[
            Mount(
                target="/scan/target",
                source=source_path,
                type="bind",
                read_only=True,
            ),
            Mount(
                target="/scan/reports",
                source="/opt/grepmarx/data/projects/2/reports",
                type="bind",
            ),
        ],
        detach=True,
        remove=True,
    )
    # get logs
    logs = container.logs(stream=True)
    for line in logs:
        print(line.decode().strip())
    
    return f"Depscan launched"