import os
import subprocess


def deploy():
    os.chdir("deploy")
    try:
        subprocess.check_output(
            "cdk deploy --all --require-approval never",
            stderr=subprocess.STDOUT,
            shell=True,
        )
    except subprocess.CalledProcessError as cpe:
        print(cpe.output.decode())
        raise


def destroy():
    os.chdir("deploy")
    try:
        subprocess.check_output(
            "cdk destroy --all --require-approval never",
            stderr=subprocess.STDOUT,
            shell=True,
        )
    except subprocess.CalledProcessError as cpe:
        print(cpe.output.decode())
        raise
