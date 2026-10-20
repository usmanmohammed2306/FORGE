from forge.hardware import probe


def test_probe_reports_host_and_never_invents_device_names():
    inventory = probe()
    assert inventory["host"]["system"]
    assert inventory["cuda"]["devices"] == [] or inventory["cuda"]["available"]
    assert inventory["hpu"]["devices"] == [] or inventory["hpu"]["available"]
