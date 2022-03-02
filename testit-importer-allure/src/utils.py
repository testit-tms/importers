import re


def form_steps(steps, requests, path):
    adapt_steps = []
    results_steps = []

    if steps:
        steps, prefix = mapping_xml_values(steps, 'step', 'status')

        for step in steps:
            if 'steps' in step:
                inner_steps, inner_results_steps = form_steps(step['steps'], requests, path)
            else:
                inner_steps = []
                inner_results_steps = []

            adapt_steps.append(
                {
                    'title': step['name'],
                    'steps': inner_steps
                }
            )

            attachments = get_attachment(requests, step['attachments'], path) if 'attachments' in step else []

            results_steps.append(
                {
                    'title': step['name'],
                    'stepResults': inner_results_steps,
                    'outcome': step[f'{prefix}status'].title() if step[f'{prefix}status'] in ('passed', 'skipped') else 'Failed',
                    'duration': (int(step[f'{prefix}stop']) - int(step[f'{prefix}start'])) if f'{prefix}stop' in step else 0,
                    "attachments": attachments,
                    'parameters': form_parameters(step['parameters']) if 'parameters' in step else None
                }
            )

    return adapt_steps, results_steps


def form_labels_namespace_classname_workitems_id(allure_labels):
    classname = None
    namespace = None
    labels = []
    workitems_id = []

    allure_labels, prefix = mapping_xml_values(allure_labels, 'label', 'value')

    for label in allure_labels:
        if label[f'{prefix}name'] == 'testcase':
            workitems_id.append(label[f'{prefix}value'])
        else:
            labels.append({'name': f"{label[f'{prefix}name']}:{label[f'{prefix}value']}"})

        if label[f'{prefix}name'] == 'package':
            namespace = label[f'{prefix}value'].split('.')[-1]
        elif label[f'{prefix}name'] == 'subSuite':
            classname = label[f'{prefix}value']
        elif label[f'{prefix}name'] == 'testClass':
            classname = label[f'{prefix}value'].split('.')[-1]

    return labels, namespace, classname, workitems_id


def form_links(allure_links):
    links = []

    for link in allure_links:
        links.append({})

        if 'url' in link and re.fullmatch(r'^(?:(?:(?:https?|ftp):)?\/\/)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff][a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.)+(?:[a-zA-Z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$', link['url']):
            links[-1]['url'] = link['url']
        else:
            raise Exception('Some links have the wrong URL or no URL!')

        if 'type' in link and link['type'] in ('Related', 'BlockedBy', 'Defect', 'Issue', 'Requirement', 'Repository'):
            links[-1]['type'] = link['type']

        if 'name' in link:
            links[-1]['title'] = link['name']

    return links


def form_setup_teardown(data_before_after, uuid, requests, path):
    setup = []
    teardown = []
    results_setup = []
    results_teardown = []

    if uuid:
        for time in data_before_after:
            for child in data_before_after[time]['children']:
                if child == uuid:
                    steps, results_steps = form_steps(data_before_after[time]['befores'], requests, path)
                    setup += steps
                    results_setup += results_steps
                    steps, results_steps = form_steps(data_before_after[time]['afters'], requests, path)
                    teardown += steps
                    results_teardown += results_steps

    return setup, results_setup, teardown, results_teardown


def form_parameters(allure_parameters):
    parameters = {}

    allure_parameters, prefix = mapping_xml_values(allure_parameters, 'parameter', 'value')

    for parameter in allure_parameters:
        parameters[parameter[f'{prefix}name']] = parameter[f'{prefix}value']

    return parameters


def get_attachment(requests, attachments_sources, path):
    attachments = []

    if attachments_sources:
        if 'attachment' in attachments_sources:
            if type(attachments_sources['attachment']) != list:
                attachments_sources = [attachments_sources['attachment']]
            else:
                attachments_sources = attachments_sources['attachment']

        prefix = '' if 'source' in attachments_sources[0] else '@'

        for attachment_source in attachments_sources:
            attachments.append({'id': requests.load_attachment(open(f"{path}/{attachment_source[f'{prefix}source']}", 'rb'))})

    return attachments


def mapping_xml_values(attributes, key, value):
    if key in attributes:
        if type(attributes[key]) != list:
            attributes = [attributes[key]]
        else:
            attributes = attributes[key]

    prefix = '' if attributes and value in attributes[0] else '@'

    return attributes, prefix
