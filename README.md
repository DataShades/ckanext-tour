[![Tests](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml)

# ckanext-tour

Guided, step-by-step product tours for CKAN, managed from the admin panel.

![ckanext-tour in action](https://raw.githubusercontent.com/DataShades/ckanext-tour/master/doc/example-1.png)

![ckanext-tour in action](https://raw.githubusercontent.com/DataShades/ckanext-tour/master/doc/example-fab.png)

## Features

- Interactive, step-by-step tours highlighting specific elements on a page
- A tour is bound to a specific page (e.g. a dataset page) or shown everywhere
- One floating **Start tour** button per page; a menu when several tours apply
- Optional auto-start on a visitor's first matching page load
- Steps support a title, intro text, tooltip position, and an optional image (upload or URL)
- Multi-language titles and intros
- Live preview of an in-progress tour before saving
- Admin table listing all tours, with search/sort, edit/delete, bulk enable/disable/remove
- One-click seeding of ready-made default tours for common pages (dataset search, dataset page, organizations, homepage)
- Active/inactive state to hide a tour without deleting it

## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.11 and below  | no            |
| 2.12+           | yes           |


## Installation

To install ckanext-tour:

1. Activate your CKAN virtual environment, for example:
    ```sh
    . /usr/lib/ckan/default/bin/activate
    ```
2. Clone the source and install it on the virtualenv
    ```sh
    git clone https://github.com/DataShades/ckanext-tour.git
    cd ckanext-tour
    pip install -e .
    ```
   `pip install -e .` also pulls in the three extensions `tour` depends on
   (see the table below).

3. Enable the plugins — add them to the `ckan.plugins` setting in your CKAN
   config file (by default `/etc/ckan/default/ckan.ini`):

   ```
   ckan.plugins = ... scheming_datasets tables files file_upload_widget tour
   ```

   | Package | Plugin(s) to enable | Needed for |
   | --- | --- | --- |
   | [ckanext-scheming](https://github.com/ckan/ckanext-scheming) | `scheming_datasets` (or any `scheming_*` plugin) | helpers used by the file_upload_widget |
   | [ckanext-tables](https://github.com/DataShades/ckanext-tables) | `tables` | rendering the tour list |
   | [ckanext-files](https://github.com/DataShades/ckanext-files) | `files`, `file_upload_widget` | storing and uploading step images |

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     `sudo service apache2 reload`

### Configuring File Storage

To store tour images, you need to configure file storage for the extension. Add the following settings to your `ckan.ini` file:

```ini
ckan.files.storage.tour_image.type = files:public_fs
ckan.files.storage.tour_image.path = %(ckan.storage_path)s/storage/tours
ckan.files.storage.tour_image.initialize = true
ckan.files.storage.tour_image.public_prefix = /tours
ckan.files.storage.tour_image.max_size = 10MiB
ckan.files.storage.tour_image.supported_types = image/png image/jpeg image/gif image/webp image/svg+xml
ckan.files.storage.tour_image.location_transformers = uuid4_with_extension

ckan.files.storage.tour_link.type = files:link
ckan.files.storage.tour_link.timeout = 5
ckan.files.storage.tour_link.protocols = https
```

## Config settings

See the available config options in [`config_declaration.yaml`](ckanext/tour/config_declaration.yaml).
Options marked `editable: true` there can also be changed from the tour **Settings** page.

## Tests

```sh
pip install -e '.[test]'
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
