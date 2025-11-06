import os
import docker


BACKEND_CONTAINER_NAME = os.environ.get("BACKEND_CONTAINER_NAME", "innexar-backend")


def _get_backend():
    return docker.from_env().containers.get(BACKEND_CONTAINER_NAME)


def run_bench(command: str):
    backend = _get_backend()
    cmd = ["bash", "-lc", command]
    rc, out = backend.exec_run(cmd, demux=True)
    if rc != 0:
        stdout, stderr = out if isinstance(out, tuple) else (out, b"")
        raise RuntimeError(f"bench command failed: {stderr.decode(errors='ignore')}")
    return True


def bench_new_site(site: str, mariadb_root_password: str, admin_password: str, db_name: str):
    return run_bench(
        (
            f"bench new-site {site} "
            f"--mariadb-root-password {mariadb_root_password} "
            f"--admin-password {admin_password} "
            f"--no-mariadb-socket "
            f"--db-name {db_name}"
        )
    )


def bench_install_app(site: str, app: str):
    return run_bench(f"bench --site {site} install-app {app}")


