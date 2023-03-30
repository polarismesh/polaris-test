import os
import random
import time

from testbase import TestCase
from testbase.conf import settings

from src.polaris_test_lib.common_lib import CommonLib
from src.polaris_test_lib.polaris import PolarisServer
from src.polaris_test_lib.polaris_request import CreateNamespaceRequest, DeleteNamespaceRequest, \
    DeleteServiceInstanceRequest, DeleteServiceRequest, CreateServiceRequest, CreateServiceInstanceRequest, \
    DeleteServiceAliasRequest


class PolarisTestCase(TestCase):
    # Specify the configuration file location.
    os.environ["QTAF_SETTINGS_MODULE"] = "src.settings"

    def pre_test(self):
        # ===========================
        self.start_step("Get POLARIS_SERVER_HTTP_RESTFUL_API_ADDR configuration.")
        POLARIS_SERVER_HTTP_RESTFUL_API_ADDR = settings.get("POLARIS_SERVER_HTTP_RESTFUL_API_ADDR", None)
        if POLARIS_SERVER_HTTP_RESTFUL_API_ADDR is not None:
            self.log_info("POLARIS_SERVER_HTTP_RESTFUL_API_ADDR: %s" % POLARIS_SERVER_HTTP_RESTFUL_API_ADDR)
            self.polaris_server_http_restful_api_addr = POLARIS_SERVER_HTTP_RESTFUL_API_ADDR
        else:
            self.fail("Check your config file in [{config_dir}] and set POLARIS_SERVER_HTTP_RESTFUL_API_ADDR in [{config_dir}]."
                      .format(config_dir=os.environ["QTAF_SETTINGS_MODULE"]))

    def run_test(self):
        pass

    def create_temp_test_directory(self, temp_dir_suffix, resource_name):
        # ===========================
        self.start_step("Get directory.")
        test_now_dir = os.path.abspath(__file__)
        self.log_info("Polaris-test now directory: " + test_now_dir)

        relative_dirs = "../.."

        test_root_dir = os.path.abspath(os.path.join(test_now_dir, relative_dirs))
        self.log_info("Polaris-test root directory: " + test_root_dir)
        test_resource_dir = test_root_dir + "/polaris_test_resource/" + resource_name
        self.log_info("Polaris-test resource directory: " + test_resource_dir)

        # ===========================
        self.start_step("Create temp test directory.")
        case_name = type(self).__name__.lower()
        new_directory = "%s/temp-test/%s-%s" % (test_root_dir, case_name, temp_dir_suffix)
        cmd_pre_deal_1 = "mkdir -p %s" % new_directory
        if os.system(cmd_pre_deal_1) != 0:
            raise RuntimeError("Exec cmd: %s error!" % cmd_pre_deal_1)
        else:
            self.log_info("Exec cmd: %s success!" % cmd_pre_deal_1)

        # ===========================
        self.start_step("Copy resource to temp test directory.")
        cmd_pre_deal_2 = "cp -r %s/* %s/" % (test_resource_dir, new_directory)
        if os.system(cmd_pre_deal_2) != 0:
            raise RuntimeError("Exec cmd: %s error!" % cmd_pre_deal_2)
        else:
            self.log_info("Exec cmd: %s success!" % cmd_pre_deal_2)
            return new_directory

    def get_kona_jdk(self, new_directory, kona_jdk_version=settings.POLARIS_TEST_SCT_KONA_JDK_VERSION):
        # ===========================
        self.start_step("Download kona jdk")
        if kona_jdk_version == 11:
            kona_jdk_url = "https://github.com/Tencent/TencentKona-11/releases/download/kona11.0.17/TencentKona-11.0.17.b1-jdk_linux-x86_64.tar.gz"
        elif kona_jdk_version == 17:
            kona_jdk_url = "https://github.com/Tencent/TencentKona-17/releases/download/TencentKona-17.0.5/TencentKona-17.0.5.b1-jdk_linux-x86_64.tar.gz"
        else:
            raise RuntimeError("Unknown kona jdk version: %s" % kona_jdk_version)

        cmd_wget = "cd %s && wget %s" % (new_directory, kona_jdk_url)

        if os.system(cmd_wget) != 0:
            raise RuntimeError("Exec cmd: %s error!" % cmd_wget)
        else:
            self.log_info("Exec cmd: %s success!" % cmd_wget)

        # ===========================
        self.start_step("Unzip kona jdk")
        jdk_name = "TencentKona-%s*" % settings.POLARIS_TEST_SCT_KONA_JDK_VERSION
        cmd_unzip = "cd %s && tar zxvf %s" % (new_directory, jdk_name)

        if os.system(cmd_unzip) != 0:
            raise RuntimeError("Exec cmd: %s error!" % cmd_unzip)
        else:
            self.log_info("Exec cmd: %s success!" % cmd_unzip)

    def get_console_token(self, username=settings.POLARIS_SERVER_USERNAME, password=settings.POLARIS_SERVER_PASSWORD):
        # ===========================
        self.start_step("Get polaris main user console token.")
        login_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.LOGIN_PATH
        rsp = PolarisServer.get_initial_token(url=login_url, username=username, password=password)
        self.token = rsp.json().get("loginResponse", None).get("token", None)
        self.user_id = rsp.json().get("loginResponse", None).get("user_id", None)

    def create_single_namespace(self, polaris_server, namespace_name=None):
        # ===========================
        self.start_step("Create one regular polaris namespace.")
        self.create_namespace_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.NAMESPACE_PATH
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        self.create_namespace_request = CreateNamespaceRequest(namespace_name=namespace_name,
                                                               comment="Auto test create polaris namespace %s" % now)
        rsp = polaris_server.create_namespace(self.create_namespace_url, self.create_namespace_request)

        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_namespace = rsp.json()["responses"][0].get("namespace", None)
        if return_namespace is None:
            self.fail("Fail! No return except polaris namespace.")
            return
        else:
            re_namespace_name = return_namespace.get("name", None)
            self.assert_("Fail! No return except polaris namespace name.", re_namespace_name == namespace_name)

        if self.test_result.passed:
            self.log_info("Success to check return namespace and polaris code!")

    def create_single_service(self, polaris_server, service_name, namespace_name="default"):
        # ===========================
        self.start_step("Create one regular polaris service: %s in namespace: %s." % (service_name, namespace_name))
        self.create_service_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.SERVICE_PATH
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        self.create_service_request = CreateServiceRequest(service_name=service_name, namespace_name=namespace_name,
                                                           owners="polaris",
                                                           comment="Auto test create polaris service %s" % now)
        rsp = polaris_server.create_service(self.create_service_url, self.create_service_request)

        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_service = rsp.json()["responses"][0].get("service", None)
        if return_service is None:
            self.fail("Fail! No return except polaris service.")
            return
        else:
            re_service_name = return_service.get("name", None)
            re_service_namespace_name = return_service.get("namespace", None)
            self.assert_("Fail! No return except polaris service name.", re_service_name == service_name)
            self.assert_("Fail! No return except polaris service namespace name.",
                         re_service_namespace_name == namespace_name)

        if self.test_result.passed:
            self.log_info("Success to check return service and polaris code!")

    def create_single_service_instance(self, polaris_server, service_name, namespace_name):
        # ===========================
        self.start_step(
            "Create one regular polaris instance in service: %s, namespace: %s." % (service_name, namespace_name))
        self.create_service_instance_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.INSTANCE_PATH
        host = CommonLib._random_ip()
        port = random.randint(10000, 50000)
        self.create_service_instance_request = CreateServiceInstanceRequest(
            service_name=service_name, namespace_name=namespace_name, host=host, port=port, weight=100, healthy=True,
            enable_health_check=False)
        rsp = polaris_server.create_service_instance(self.create_service_instance_url,
                                                     self.create_service_instance_request)

        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)

        return_service_instance = rsp.json()["responses"][0].get("instance", None)
        if return_service_instance is None:
            self.fail("Fail! No return except polaris service.")
            return
        else:
            re_service_instance_host = return_service_instance.get("host", None)
            self.assert_("Fail! No return except polaris service instance host.",
                         re_service_instance_host == host)

        if self.test_result.passed:
            self.log_info("Success to check return service and polaris code!")
            return return_service_instance
        else:
            return None

    def create_single_service_alias(self, polaris_server, service_name, namespace_name, service_alias_name,
                                    alias_namespace_name):
        # ===========================
        self.start_step("Create service alias %s in %s point to service %s in %s." % (
            service_alias_name, alias_namespace_name, service_name, namespace_name))

        self.create_service_alias_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.SERVICE_ALIAS_PATH
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        rsp = polaris_server.create_service_alias(self.create_service_alias_url, service_name, namespace_name,
                                                  service_alias_name, alias_namespace_name,
                                                  comment="Auto test create polaris service %s" % now)

        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_service_alias = rsp.json().get("alias", None)
        if return_service_alias is None:
            self.fail("Fail! No return except polaris service alias .")
        else:
            re_srv_alias_name = rsp.json()["alias"].get("alias", None)
            re_srv_alias_namespace_name = rsp.json()["alias"].get("alias_namespace", None)

            self.assert_("Fail! No return except polaris service alias name.", re_srv_alias_name == service_alias_name)
            self.assert_("Fail! No return except polaris service alias namespace name.",
                         re_srv_alias_namespace_name == alias_namespace_name)

        if self.test_result.passed:
            self.log_info("Success to check return service alias and polaris code!")

    def clean_test_service_instances(self, polaris_server, namespace_name, service_name, wait_time=300):
        # ===========================
        self.start_step("Clean the test polaris service[%s:%s] instances." % (namespace_name, service_name))
        describe_service_instance_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.INSTANCE_PATH

        now = time.time()
        while time.time() - now < wait_time:
            rsp = polaris_server.describe_service_instance(describe_service_instance_url, limit=10, offset=0,
                                                           namespace_name=namespace_name, service_name=service_name)
            instances = rsp.json().get("instances", None)
            if len(instances) == 0:
                self.log_info("Delete service instance finish.")
                return True

            delete_instance_requests = []
            for ins in instances:
                self.log_info("Delete service instance: %s:%s" % (ins["host"], ins["port"]))
                delete_instance_requests.append(DeleteServiceInstanceRequest(service_instance_id=ins["id"]))
            delete_service_instance_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DELETE_INSTANCE_PATH
            rsp = polaris_server.delete_service_instance(delete_service_instance_url, delete_instance_requests)
            polaris_code = rsp.json().get("code", None)
            if polaris_code != 200000:
                self.fail("Fail! No return except polaris code.")
                return False
            time.sleep(1)
        else:
            self.fail("Fail! Delete service instance time out.")
            return False

    def clean_test_service_aliases(self, polaris_server, namespace_name, service_name, wait_time=300):
        # ===========================
        self.start_step("Clean the test polaris service[%s:%s] aliases." % (namespace_name, service_name))
        self.describe_service_alias_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DESCRIBE_SERVICE_ALIAS_PATH

        now = time.time()
        while time.time() - now < wait_time:
            rsp = self.polaris_server.describe_service_alias(self.describe_service_alias_url, limit=10, offset=0,
                                                             point_to_service_name=service_name)
            aliases = rsp.json().get("aliases", None)
            if len(aliases) == 0:
                self.log_info("Delete service aliases finish.")
                return True

            delete_alias_requests = []
            for alias in aliases:
                self.log_info("Delete service alias: %s in %s" % (alias["alias"], alias["alias_namespace"]))
                delete_alias_requests.append(
                    DeleteServiceAliasRequest(alias_namespace_name=alias["alias_namespace"], alias_name=alias["alias"]))
            delete_service_alias_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DELETE_SERVICE_ALIAS_PATH
            rsp = polaris_server.delete_service_alias(delete_service_alias_url, delete_alias_requests)
            polaris_code = rsp.json().get("code", None)
            if polaris_code != 200000:
                self.fail("Fail! No return except polaris code.")
                return False
            time.sleep(1)
        else:
            self.fail("Fail! Delete service alias time out.")
            return False

    def clean_test_services(self, polaris_server, namespace_name=None, service_name=None, wait_time=300):
        # ===========================
        self.start_step("Clean the test polaris services.")
        delete_service_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DELETE_SERVICE_PATH
        if all([namespace_name, service_name]):
            # ===========================
            self.start_step("Check service instances, delete first.")
            success = self.clean_test_service_instances(polaris_server, namespace_name=namespace_name,
                                                        service_name=service_name)
            if not success:
                self.fail("Fail to delete service: %s instances." % service_name)
                return False
            # ===========================
            self.start_step("Check service alias, delete.")
            success = self.clean_test_service_aliases(polaris_server, namespace_name=namespace_name,
                                                      service_name=service_name)
            if not success:
                self.fail("Fail to delete service: %s aliases." % service_name)
                return False
            # ===========================
            self.start_step("Delete service: %s from namespace: %s" % (service_name, namespace_name))
            delete_service_req = DeleteServiceRequest(namespace_name=namespace_name, service_name=service_name)
            rsp = polaris_server.delete_service(delete_service_url, delete_service_req)
            polaris_code = rsp.json().get("code", None)
            if polaris_code != 200000:
                self.fail("Fail! No return except polaris code.")
                return False
            return True
        elif any([service_name, namespace_name]):
            service_name_str = service_name if service_name is not None else "all"
            namespace_name_str = namespace_name if namespace_name is not None else "all"
            # ===========================
            self.start_step("Delete %s service from %s namespace" % (service_name_str, namespace_name_str))
            describe_service_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.SERVICE_PATH
            now = time.time()
            while time.time() - now < wait_time:
                rsp = polaris_server.describe_service(describe_service_url, limit=10, offset=0,
                                                      service_name=service_name, namespace_name=namespace_name)
                services = rsp.json().get("services", None)
                if len(services) == 0:
                    self.log_info("Delete service finish.")
                    return True
                    break

                delete_service_requests = []
                for srv in services:
                    self.log_info("Delete service: %s from namespace: %s" % (srv["name"], srv["namespace"]))
                    # ===========================
                    self.start_step("Check service instances, delete first.")
                    success = self.clean_test_service_instances(polaris_server, namespace_name=srv["namespace"],
                                                                service_name=srv["name"])
                    if not success:
                        self.fail("Fail to delete service: %s instances." % srv["name"])
                        return False

                    # ===========================
                    self.start_step("Check service alias, delete.")
                    success = self.clean_test_service_aliases(polaris_server, namespace_name=srv["namespace"],
                                                              service_name=srv["name"])
                    if not success:
                        self.fail("Fail to delete service: %s aliases." % srv["name"])
                        return False

                    delete_service_req = DeleteServiceRequest(namespace_name=srv["namespace"], service_name=srv["name"])
                    delete_service_requests.append(delete_service_req)

                rsp = polaris_server.delete_service(delete_service_url, delete_service_requests)
                polaris_code = rsp.json().get("code", None)
                if polaris_code != 200000:
                    self.fail("Fail! No return except polaris code.")
                    return False
                time.sleep(1)
            else:
                self.fail("Fail! Delete service time out.")
                return False

        else:
            raise Exception("You must assign at least namespace_name or service_name")

    def clean_test_namespaces(self, polaris_server, namespace_names):
        # ===========================
        self.start_step("Clean the test polaris namespaces.")
        delete_namespace_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DELETE_NAMESPACE_PATH

        delete_namespace_requests = []
        if type(namespace_names) != list:
            namespace_names = [namespace_names]
        for n in namespace_names:
            self.log_info("Delete namespace: %s" % n)
            # ===========================
            self.start_step("Check services, delete first.")
            success = self.clean_test_services(polaris_server, namespace_name=n)
            if not success:
                self.fail("Fail to delete services from namespace: %s." % n)
                return False

            delete_namespace_requests.append(DeleteNamespaceRequest(namespace_name=n))
        rsp = polaris_server.delete_namespace(delete_namespace_url, delete_namespace_requests)
        polaris_code = rsp.json().get("code", None)
        if polaris_code != 200000:
            self.fail("Fail! No return except polaris code.")
            return False
        return True

    def get_all_namespaces(self, polaris_server, limit=10):
        self.describe_namespace_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.NAMESPACE_PATH
        rsp = polaris_server.describe_namespace(self.describe_namespace_url, limit=limit, offset=0)
        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_namespace_total = rsp.json().get("amount", None)

        return_namespaces = []
        if return_namespace_total > limit:
            self.log_info("requery with the total number of Polaris namespaces.")
            query_times = int((return_namespace_total / limit) + 1)
            for offset in range(query_times):
                rsp = polaris_server.describe_namespace(self.describe_namespace_url, limit=limit, offset=offset)
                polaris_code = rsp.json().get("code", None)
                self.assert_("Fail! No return except polaris code.", polaris_code == 200000)

                return_namespaces += rsp.json().get("namespaces", None)
        else:
            return_namespaces = rsp.json().get("namespaces", None)
        return return_namespaces

    def get_all_services(self, polaris_server, limit=10, namespace_name="default"):
        self.describe_service_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.SERVICE_PATH
        rsp = self.polaris_server.describe_service(url=self.describe_service_url, limit=10, offset=0,
                                                   namespace_name=namespace_name)
        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_service_total = rsp.json().get("amount", None)

        return_services = []
        if return_service_total > limit:
            self.log_info("requery with the total number of Polaris services.")
            query_times = int((return_service_total / limit) + 1)
            for offset in range(query_times):
                rsp = polaris_server.describe_service(self.describe_service_url, limit=limit, offset=offset,
                                                      namespace_name=namespace_name)
                polaris_code = rsp.json().get("code", None)
                self.assert_("Fail! No return except polaris code.", polaris_code == 200000)

                return_services += rsp.json().get("services", None)
        else:
            return_services = rsp.json().get("services", None)
        return return_services

    def get_all_service_aliases(self, polaris_server, limit=10):
        self.describe_service_alias_url = "http://" + self.polaris_server_http_restful_api_addr + PolarisServer.DESCRIBE_SERVICE_ALIAS_PATH
        rsp = polaris_server.describe_service_alias(self.describe_service_alias_url, limit=10, offset=0)
        polaris_code = rsp.json().get("code", None)
        self.assert_("Fail! No return except polaris code.", polaris_code == 200000)
        return_service_aliases_total = rsp.json().get("amount", None)

        return_service_aliases = []
        if return_service_aliases_total > limit:
            self.log_info("requery with the total number of Polaris service aliases.")
            query_times = int((return_service_aliases_total / limit) + 1)
            for offset in range(query_times):
                rsp = self.polaris_server.describe_service_alias(self.describe_service_alias_url, limit=10, offset=0)
                polaris_code = rsp.json().get("code", None)
                self.assert_("Fail! No return except polaris code.", polaris_code == 200000)

                return_service_aliases += rsp.json().get("aliases", None)
        else:
            return_service_aliases = rsp.json().get("aliases", None)
        return return_service_aliases


