from django.core.management import load_command_class


def test_createuser_has_output_streams():
    command = load_command_class("itkufs.accounting", "createuser")
    assert command.stdout is not None
    assert command.stderr is not None
