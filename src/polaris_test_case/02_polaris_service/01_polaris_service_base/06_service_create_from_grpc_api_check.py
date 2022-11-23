import random
import string
import subprocess

from testbase.conf import settings
from testbase.testcase import TestCase

from src.polaris_test_lib.polaris import PolarisServer
from src.polaris_test_lib.polaris_testcase import PolarisTestCase


class ServiceCreateFromGRPCApiCheck(PolarisTestCase):
    """
    Used to test creating service from grpc.

    """
    owner = "atom"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    timeout = 5

    def run_test(self):
        # ===========================
        self.start_step("Create one polaris service from grpc demo.")
        _random_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        self.namespace_name = "AutoTestPolarisGRPCNamespace-" + _random_str
        self.service_name = "AutoTestPolarisGRPCService-" + _random_str

        # ===========================
        new_directory = self.create_temp_test_directory(_random_str)

        # ===========================
        self.start_step("Register by grpc demo, auto create namespace if not exist.")
        self.log_info("The polaris-server.yaml default config: namespace.autoCreate=true has been pre-set, "
                      "if this case fail, please check your polaris-server.yaml.")
        reg_ip = settings.POLARIS_SERVER_GRPC_SERVICE_ADDR
        cmd_exe = "cd %s && chmod 777 provider && sed -i 's/ipaddr/%s/g' polaris.yaml && " \
                  "nohup ./provider -service=%s -namespace=%s -auto_shutdown=true &" % \
                  (new_directory, reg_ip, self.service_name, self.namespace_name)
        self.log_info("Exec cmd: %s" % cmd_exe)
        rsp = subprocess.check_output(cmd_exe, shell=True)
        self.log_info("\n" + rsp.decode())

        # ===========================
        self.start_step("Check create service.")
        self.get_console_token()
        self.polaris_server = PolarisServer(self.token, self.user_id)
        return_services = self.get_all_services(self.polaris_server, namespace_name=self.namespace_name)

        return_service_names = [srv["name"] for srv in return_services]
        self.assert_("Fail! No return except polaris service.", self.service_name in return_service_names)

    def post_test(self):
        self.clean_test_namespaces(self.polaris_server, [self.namespace_name])


if __name__ == '__main__':
    ServiceCreateFromGRPCApiCheck().debug_run()
