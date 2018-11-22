# Import the client library
import google.cloud.dlp

# Instantiate a client.
dlp = google.cloud.dlp.DlpServiceClient()

def redact_image_fileinmemory(project, image_binary, filetype,
                 info_types, min_likelihood=None, mime_type=None):
    """Uses the Data Loss Prevention API to redact protected data in an image.
    Args:
        project: The Google Cloud project id to use as a parent resource.
        filename: The path to the file to inspect.
        output_filename: The path to which the redacted image will be written.
        info_types: A list of strings representing info types to look for.
            A full list of info type categories can be fetched from the API.
        min_likelihood: A string representing the minimum likelihood threshold
            that constitutes a match. One of: 'LIKELIHOOD_UNSPECIFIED',
            'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY_LIKELY'.
        mime_type: The MIME type of the file. If not specified, the type is
            inferred via the Python standard library's mimetypes module.
    Returns:
        None; the response from the API is printed to the terminal.
    """

    # Prepare info_types by converting the list of strings into a list of
    # dictionaries (protos are also accepted).
    info_types = [{'name': info_type} for info_type in info_types]

    # Prepare image_redaction_configs, a list of dictionaries. Each dictionary
    # contains an info_type and optionally the color used for the replacement.
    # The color is omitted in this sample, so the default (black) will be used.
    image_redaction_configs = []

    if info_types is not None:
        for info_type in info_types:
            image_redaction_configs.append({'info_type': info_type})

    # Construct the configuration dictionary. Keys which are None may
    # optionally be omitted entirely.
    inspect_config = {
        'min_likelihood': min_likelihood,
        'info_types': info_types,
    }

    # If mime_type is not specified, guess it from the filename.
    if filetype == 'jpg':
        mime_type='image/jpeg'
    elif filetype == 'png':
        mime_type='image/png'

    # Select the content type index from the list of supported types.
    supported_content_types = {
        None: 0,  # "Unspecified"
        'image/jpeg': 1,
        'image/bmp': 2,
        'image/png': 3,
        'image/svg': 4,
        'text/plain': 5,
    }
    content_type_index = supported_content_types.get(mime_type, 0)

    # Construct the byte_item, containing the file's byte data.
    byte_item = {'type': content_type_index, 'data': image_binary}
    # Convert the project id into a full resource id.
    parent = dlp.project_path(project)

    # Call the API.
    response = dlp.redact_image(
        parent, inspect_config=inspect_config,
        image_redaction_configs=image_redaction_configs,
        byte_item=byte_item)

    return response.redacted_image

def redact_image_fileondisk(project, filename, output_filename,
                 info_types, min_likelihood=None, mime_type=None):
    """Uses the Data Loss Prevention API to redact protected data in an image.
    Args:
        project: The Google Cloud project id to use as a parent resource.
        filename: The path to the file to inspect.
        output_filename: The path to which the redacted image will be written.
        info_types: A list of strings representing info types to look for.
            A full list of info type categories can be fetched from the API.
        min_likelihood: A string representing the minimum likelihood threshold
            that constitutes a match. One of: 'LIKELIHOOD_UNSPECIFIED',
            'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY_LIKELY'.
        mime_type: The MIME type of the file. If not specified, the type is
            inferred via the Python standard library's mimetypes module.
    Returns:
        None; the response from the API is printed to the terminal.
    """

    # Prepare info_types by converting the list of strings into a list of
    # dictionaries (protos are also accepted).
    info_types = [{'name': info_type} for info_type in info_types]

    # Prepare image_redaction_configs, a list of dictionaries. Each dictionary
    # contains an info_type and optionally the color used for the replacement.
    # The color is omitted in this sample, so the default (black) will be used.
    image_redaction_configs = []

    if info_types is not None:
        for info_type in info_types:
            image_redaction_configs.append({'info_type': info_type})

    # Construct the configuration dictionary. Keys which are None may
    # optionally be omitted entirely.
    inspect_config = {
        'min_likelihood': min_likelihood,
        'info_types': info_types,
    }

    # If mime_type is not specified, guess it from the filename.
    if mime_type is None:
        mime_guess = mimetypes.MimeTypes().guess_type(filename)
        mime_type = mime_guess[0] or 'application/octet-stream'

    # Select the content type index from the list of supported types.
    supported_content_types = {
        None: 0,  # "Unspecified"
        'image/jpeg': 1,
        'image/bmp': 2,
        'image/png': 3,
        'image/svg': 4,
        'text/plain': 5,
    }
    content_type_index = supported_content_types.get(mime_type, 0)

    # Construct the byte_item, containing the file's byte data.
    with open(filename, mode='rb') as f:
        byte_item = {'type': content_type_index, 'data': f.read()}

    # Convert the project id into a full resource id.
    parent = dlp.project_path(project)

    # Call the API.
    response = dlp.redact_image(
        parent, inspect_config=inspect_config,
        image_redaction_configs=image_redaction_configs,
        byte_item=byte_item)

    # Write out the results.
    with open(output_filename, mode='wb') as f:
        f.write(response.redacted_image)
    print("Wrote {byte_count} to {filename}".format(
        byte_count=len(response.redacted_image), filename=output_filename))

    return output_filename