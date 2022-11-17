from testit_api_client.models import (
    AutoTestPostModel,
    AutoTestPutModel,
    AutoTestResultsForTestRunModel)


class Converter:
    @staticmethod
    def test_result_to_autotest_post_model(
            result,
            external_id: str,
            project_id: str):
        return AutoTestPostModel(
            external_id,
            project_id,
            result.get_name(),
            namespace=result.get_name_space(),
            classname=result.get_class_name(),
        )

    @staticmethod
    def test_result_to_autotest_put_model(
            result,
            external_id: str,
            project_id: str):
        return AutoTestPutModel(
            external_id,
            project_id,
            result.get_name(),
            namespace=result.get_name_space(),
            classname=result.get_class_name(),
        )

    @staticmethod
    def test_result_to_testrun_result_post_model(
            result,
            external_id: str,
            configuration_id: str):
        return AutoTestResultsForTestRunModel(
            configuration_id,
            external_id,
            result.get_status().value,
            traces=result.get_trace(),
            duration=round(result.get_duration()),
            message=result.get_message(),
        )
