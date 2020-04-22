
import pandas as pd


def metadata_table(samples):
    """Return a pandas dataframe with metadata from `samples`."""
    pass


def sample_module_field(sample, module_name, field_name):
    """Return a dict of `sample_names` -> `transformer(stored_data)` for the specified field."""
    ars = [
        ar for ar in sample.get_analysis_results()
        if ar.module_name == module_name
    ]
    if len(ars) == 0:
        raise KeyError(f'Sample {sample.name} has no analysis result {module_name}')
    fields = [
        field for field in ars[0].get_fields()
        if field.name == field_name
    ]
    if len(fields) == 0:
        raise KeyError(f'Sample {sample.name} has no result field {field_name} for {module_name}')
    return fields[0]


def scrub_category_val(category_val):
    """Make sure that category val is a string with positive length."""
    if not isinstance(category_val, str):
        category_val = str(category_val)
        if category_val.lower() == 'nan':
            category_val = 'NaN'
    if not category_val:
        category_val = 'NaN'
    return category_val


def categories_from_metadata(samples, min_size=2):
    """
    Create dict of categories and their values from sample metadata.
    Parameters
    ----------
    samples : list
        List of sample models.
    min_size: int
        Minimum number of values required for a given metadata item to
        be included in returned categories.
    Returns
    -------
    dict
        Dictionary of form {<category_name>: [category_value[, category_value]]}
    """
    categories = {}

    # Gather categories and values
    for sample in samples:
        for prop, val in sample.metadata.items():
            if not val:
                continue
            if prop not in categories:
                categories[prop] = set([])
            categories[prop].add(scrub_category_val(val))

    # Filter for minimum number of values
    categories = {
        category_name: list(category_values)
        for category_name, category_values in categories.items()
        if len(category_values) >= min_size
    }
    categories['All'] = ['All']

    return categories


def group_samples_by_metadata(samples, min_size=2, group_apply=lambda x: x):
    """
    Create dict of categories, their values and samples from sample metadata.
    Parameters
    ----------
    samples : list
        List of sample models.
    min_size: int
        Minimum number of values required for a given metadata item to
        be included in returned categories.
    group_apply: function
        Function to apply to each group of samples
    Returns
    -------
    tuple of
    dict
        Dictionary of form {<category_name>: [category_value[, category_value]]}
    dict
        Dictionary of form {
            <category_name>: {
                category_value: [sample[, sample]]
            }
        }
    """
    categories = categories_from_metadata(samples, min_size=min_size)
    grouped_samples = {}
    for category_name, category_values in categories.items():
        grouped_samples[category_name] = {}
        for cat_val in category_values:
            grouped_samples[category_name][cat_val] = group_apply([
                sample for sample in samples
                if category_name == 'All' or sample.metadata.get(category_name, None) == cat_val
            ])
    return categories, grouped_samples
