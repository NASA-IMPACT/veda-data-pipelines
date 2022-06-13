from aws_cdk import (
    core,
    aws_ec2 as ec2,
)
import config


class VpcStack(core.Stack):
    def __init__(self, app, construct_id, vpc, sg, **kwargs):
        super().__init__(app, construct_id, **kwargs)
        # Database config
        self._database_vpc = ec2.Vpc.from_lookup(self, f"{construct_id}-db", vpc_id=vpc)
        # PGSTAC database SG
        self._database_security_group = ec2.SecurityGroup.from_security_group_id(self, f"{construct_id}-sg", sg)

    @property
    def database_vpc(self):
        return self._database_vpc

    def add_rds_write_ingress(self, sg):
        self._database_security_group.add_ingress_rule(
            sg,
            connection=ec2.Port.tcp(5432),
            description="Allow pgstac database write access to lambda",
        )
