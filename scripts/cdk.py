import os


def deploy():
    os.chdir("deploy")
    os.system("cdk deploy --all --require-approval never")


def destroy():
    os.chdir("deploy")
    os.system("cdk destroy --all --require-approval never")
