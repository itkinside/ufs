from django.test.simple import run_tests as django_test_runner, get_apps

def test_runner(test_labels, verbosity=1, interactive=True,
    extra_tests=[]):

    if not test_labels:
        test_labels = []

        for app in get_apps():
            if app.__name__.startswith('itkufs'):
                test_labels.append(app.__name__.split('.')[1])

    return django_test_runner(test_labels, verbosity, interactive,
                                      extra_tests)
